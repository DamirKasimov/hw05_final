from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from ..models import Post, Group


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем неавторизованный клиент

        # Создаем пользователя
        cls.user = User.objects.create(username='HasNoName')
        cls.user_wr = User.objects.create(username='HasNo')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_w = Client()
        self.authorized_client_w.force_login(self.user_wr)

    def test_create_post(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)
        response_w = self.guest_client.get('/create/')
        self.assertEqual(response_w.status_code, 302)

    def test_edit_post(self):
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 200)
        response = self.authorized_client_w.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_access(self):
        paths = {
            '/': 200,
            '/profile/HasNoName/': 200,
            '/group/test-slug/': 200,
            f'/posts/{self.post.id}/': 200,
            '/unexisting': 404,
        }

        for address, code in paths.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, code)

    def test_templates(self):
        templates_url_names = {
            ('/'): 'posts/index.html',
            (f'/group/{PostURLTests.group.slug}/'): 'posts/group_list.html',
            (f'/profile/{PostURLTests.user.username}/'): 'posts/profile.html',
            (f'/posts/{self.post.id}/'): 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
