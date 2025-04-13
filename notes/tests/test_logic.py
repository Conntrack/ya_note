from http import HTTPStatus
from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import WARNING


User = get_user_model()


class TestPagesContent(TestCase):
    NOTES_ADD_URL = reverse('notes:add')

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
        cls.new_form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug',
            'author': cls.author,
        }
        cls.duplicated_slug_form_data = {
            'title': 'Ещё заголовок',
            'text': 'Ещё текст',
            'slug': cls.note.slug,
            'author': cls.author,
        }
        cls.empty_slug_form_data = {
            'title': 'Заголовок "Пустой слаг"',
            'text': 'Какой-то текст',
            'slug': '',
            'author': cls.author,
        }

    def test_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку."""
        self.client.force_login(self.author)
        response = self.client.post(
            self.NOTES_ADD_URL, data=self.new_form_data
        )
        # Проверяем, что был выполнен редирект на страницу успешного
        # добавления заметки:
        self.assertRedirects(response, reverse('notes:success'))
        # Считаем общее количество заметок в БД, ожидаем 2 заметки.
        self.assertEqual(Note.objects.count(), 2)
        # Чтобы проверить значения полей заметки - 
        # получаем её из базы при помощи метода get():
        new_note = Note.objects.get(slug=self.new_form_data['slug'])
        # Сверяем атрибуты объекта с ожидаемыми.
        self.assertEqual(new_note.title, self.new_form_data['title'])
        self.assertEqual(new_note.text, self.new_form_data['text'])
        self.assertEqual(new_note.slug, self.new_form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        response = self.client.post(
            self.NOTES_ADD_URL, data=self.new_form_data
        )
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={self.NOTES_ADD_URL}'
        # Проверяем, что произошла переадресация на страницу логина:
        self.assertRedirects(response, expected_url)
        # Считаем общее количество заметок в БД, ожидаем 1 заметку.
        self.assertEqual(Note.objects.count(), 1)

    def test_not_unique_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        self.client.force_login(self.author)
        response = self.client.post(
            self.NOTES_ADD_URL, data=self.duplicated_slug_form_data
        )
        # Считаем общее количество заметок в БД, ожидаем 1 заметку.
        self.assertEqual(Note.objects.count(), 1)
        # Проверяем, что в ответе содержится ошибка формы для поля slug:
        self.assertFormError(
            response, 'form', 'slug', errors=(self.note.slug + WARNING)
        )

    def test_empty_slug(self):
        """Если при создании заметки не заполнен slug."""
        self.client.force_login(self.author)
        response = self.client.post(
            self.NOTES_ADD_URL, data=self.empty_slug_form_data
        )
        # Проверяем, что даже без slug заметка была создана:
        self.assertRedirects(response, reverse('notes:success'))
        # Считаем общее количество заметок в БД, ожидаем 2 заметки.
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.all().last()
        # Формируем ожидаемый slug:
        expected_slug = slugify(self.empty_slug_form_data['title'])
        # Проверяем, что slug заметки соответствует ожидаемому:
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        """Пользователь может редактировать свои заметки."""
        self.client.force_login(self.author)
        # Получаем адрес страницы редактирования заметки:
        url = reverse('notes:edit', args=(self.note.slug,))
        # В POST-запросе на адрес редактирования заметки
        # отправляем new_form_data - новые значения для полей заметки:
        response = self.client.post(url, self.new_form_data)
        # Проверяем редирект:
        self.assertRedirects(response, reverse('notes:success'))
        # Обновляем объект заметки note: получаем обновлённые данные из БД:
        self.note.refresh_from_db()
        # Проверяем, что атрибуты заметки соответствуют обновлённым:
        self.assertEqual(self.note.title, self.new_form_data['title'])
        self.assertEqual(self.note.text, self.new_form_data['text'])
        self.assertEqual(self.note.slug, self.new_form_data['slug'])

    def test_other_user_cant_edit_note(self):
        """Пользователь не может редактировать чужие заметки."""
        self.client.force_login(self.reader)
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.client.post(url, self.new_form_data)
        # Проверяем, что страница не найдена:
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Получаем новый объект запросом из БД.
        note_from_db = Note.objects.get(id=self.note.id)
        # Проверяем, что атрибуты объекта из БД равны атрибутам заметки
        # до запроса.
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)
