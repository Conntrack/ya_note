from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note


User = get_user_model()


class TestPagesContent(TestCase):
    NOTES_LIST_URL = reverse('notes:list')

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

    def test_note_in_list_for_author(self):
        """
        Отдельная заметка передаётся на страницу со списком заметок в списке
        object_list в словаре context.
        """
        self.client.force_login(self.author)
        # Запрашиваем страницу со списком заметок:
        response = self.client.get(self.NOTES_LIST_URL)
        # Получаем список объектов из контекста:
        object_list = response.context['object_list']
        # Проверяем, что заметка находится в этом списке:
        self.assertIn(self.note, object_list)

    def test_note_not_in_list_for_another_user(self):
        """
        В список заметок одного пользователя не попадают заметки другого
        пользователя.
        """
        self.client.force_login(self.reader)
        response = self.client.get(self.NOTES_LIST_URL)
        object_list = response.context['object_list']
        # Проверяем, что заметки нет в контексте страницы:
        self.assertNotIn(self.note, object_list)

    def test_pages_contains_form(self):
        """На страницы создания и редактирования заметки передаются  формы."""
        names_n_slugs = (
            ('notes:edit', self.note.slug),
            ('notes:add', None),
        )
        self.client.force_login(self.author)
        for name, slug in names_n_slugs:
            with self.subTest(name=name, slug=slug):
                if slug is None:
                    url = reverse(name)
                else:
                    url = reverse(name, args=(slug,))
                response = self.client.get(url)
                # Проверяем, есть ли объект формы в словаре контекста:
                self.assertIn('form', response.context)
                # Проверяем, что объект формы относится к нужному классу.
                self.assertIsInstance(response.context['form'], NoteForm)
