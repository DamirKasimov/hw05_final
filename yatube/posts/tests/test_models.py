from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        # Создаем тестовую запись поста
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
    # Напишите проверку тут
        group = PostModelTest.group
        title = group.title
        # Сравниваем поле 'название' с ожидаемым
        self.assertEqual(title, 'Тестовая группа')

    def test_models_have_correct_object_names_2(self):
        post = PostModelTest.post
        text = post.text
        self.assertEqual(text, 'Тестовая пост')
