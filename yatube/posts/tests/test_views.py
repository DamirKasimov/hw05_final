from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Post, Group
from django import forms


User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        PostViewsTests.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=PostViewsTests.user,
            group=PostViewsTests.group
        )

    def setUp(self):
        self.client = Client()

    def test_pages_uses_correct_template_unauth(self):
        temps = {
            reverse('posts:posts_basedir_path'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug':
                    PostViewsTests.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username':
                    PostViewsTests.user.username}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id':
                    self.post.id}): 'posts/post_detail.html',
        }
        for reverse_name, template in temps.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template_auth(self):
        reverse_name = reverse('posts:post_edit', kwargs={'post_id':
                                                          self.post.id})
        response = self.authorized_client.get(reverse_name)
        self.assertTemplateUsed(response, 'posts/create_post.html')

    # contexts_tests
    def test_post_create_page_shows_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_group_posts_page_shows_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PostViewsTests.group.slug}))
        first_object = response.context['page_obj'][0]
        post_group_0 = first_object.group
        post_text_0 = first_object.text
        self.assertEqual(post_group_0, PostViewsTests.post.group)
        self.assertEqual(post_text_0, PostViewsTests.post.text)

    def test_post_edit_page_shows_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostViewsTests.post.id}))
        form_fields = {
            'group': forms.fields.ChoiceField,
            # При создании формы поля модели типа TextField
            # преобразуются в CharField с виджетом forms.Textarea
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_page_shows_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        fields_q = len(response.context.get('form').fields)
        self.assertEqual(fields_q, 3)

    def test_post_follow_me(self):
        response = self.authorized_client.get
        (reverse('posts:profile_follow',
                 kwargs={'username': self.authorized_client}))
        self.assertEqual(response.status_code, 404)
