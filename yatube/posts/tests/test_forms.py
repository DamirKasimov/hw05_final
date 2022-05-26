from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from posts.models import Post
from django.test import Client, TestCase
from django.urls import reverse


User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Kookoo')

        cls.post = Post.objects.create(
            text='text',
            author=cls.user,
        )

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_posts_do_create(self):
        posts_count = Post.objects.count()

        form_data = {
            'text': 'pext',
            'author': f'{self.post.author.username}',
        }

        # Отправляем POST-запрос
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertEqual(Post.objects.count(), posts_count + 1)

        # Проверяем, что пост точно последний
        post_0 = get_object_or_404(Post, id=posts_count + 1).pub_date
        post_1 = Post.objects.last().pub_date
        self.assertNotEqual(post_1 - post_0, 0)

    def test_post_changes(self):
        form_data2 = {
            'text': 'qqqqqqqqqq',
            'author': f'{self.user.username}',
        }
        id = PostCreateFormTests.post.id

        response = self.authorized_client.post(
            reverse('posts:post_edit', args=((PostCreateFormTests.post.id),)),
            data=form_data2,
            is_edit=True,
            follow=True
        )
        self.post.save()

        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertNotEqual('text', self.post)
        self.assertEqual(id, self.post.id)
