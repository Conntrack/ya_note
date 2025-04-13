from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(  # Создаём объект заметки.
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )

    def test_home_page(self):
        """Главная страница доступна анонимному пользователю."""
        url = reverse('notes:home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        """
        Аутентифицированному пользователю доступны страницы notes/, done/,
        add/.
        """
        names = (
            'notes:list', 'notes:add', 'notes:success',
        )
        self.client.force_login(self.author)
        for name in names:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_different_users(self):
        """
        Страницы отдельной заметки, удаления и редактирования заметки доступны
        только автору заметки.
        """
        names = (
            'notes:detail', 'notes:edit', 'notes:delete'
        )
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in names:
                with self.subTest(name=name, status=status):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirects(self):
        """
        При попытке перейти на страницу списка заметок,
        страницу успешного добавления записи, страницу добавления заметки,
        отдельной заметки, редактирования или удаления заметки
        анонимный пользователь перенаправляется на страницу логина.
        """
        names_n_slugs = (
            ('notes:detail', self.note.slug),
            ('notes:edit', self.note.slug),
            ('notes:delete', self.note.slug),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
        )
        login_url = reverse('users:login')
        for name, slug in names_n_slugs:
            with self.subTest(name=name, slug=slug):
                if slug is None:
                    url = reverse(name)
                else:
                    url = reverse(name, args=(slug,))
                expected_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, expected_url)

    def test_pages_availability_for_anonymous_user(self):
        """
        Страницы регистрации пользователей, входа в учётную запись и выхода из
        неё доступны всем пользователям.
        """
        names = ('users:login', 'users:logout', 'users:signup')
        for name in names:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
