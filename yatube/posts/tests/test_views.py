import shutil
import tempfile
from django.core.management import settings
from django.contrib.auth import get_user_model
from posts.forms import PostForm
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Post, Group, Follow
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache


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

    def test_post_not_follows_me(self):
        self.authorized_client.get
        (reverse('posts:profile_follow',
                 kwargs={'username': self.authorized_client}))
        self.assertEqual(Follow.objects.all().count(), 0)


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cls.author = User.objects.create(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group)
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = self.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """При отправке формы со страницы создания создаётся новый пост."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст2',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст2',
                group=self.group.id,
                image='posts/small.gif'
            ).exists()
        )


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.DEPTH = 10
        cls.DOZEN = 12
        cls.user = User.objects.create(username='koo')
        cls.group = Group.objects.create(
            title='one',
            slug='two',
            description='description',
        )

        Post.objects.bulk_create(
            [
                Post(
                    text=f'Тестовый пост №{i}',
                    author=cls.user,
                    group=cls.group,
                )
                for i in range(cls.DOZEN)
            ]
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_given_records_number(self):
        """Проверка нарезки: DEPTH"""
        paginator_pages = [
            reverse('posts:posts_basedir_path'),
            reverse(
                'posts:group_list', kwargs={'slug': f'{self.group.slug}'}
            ),
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}),
        ]

        for name in paginator_pages:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                self.assertEqual(len(response.context.get('page_obj')),
                                 self.DEPTH)

    def test_last_page_contains_left_records(self):
        paginator_pages = [
            reverse('posts:posts_basedir_path') + "?page=2",
            reverse(
                'posts:group_list', kwargs={'slug': f'{self.group.slug}'}
            ) + "?page=2",
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}) + "?page=2",
        ]
        for name in paginator_pages:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                self.assertEqual(len(response.context.get('page_obj')),
                                 self.DOZEN - self.DEPTH)

    def test_cache_in_index_page_show_correct_context(self):
        """Проверка работы кэша"""
        Post.objects.filter(id=14).delete()
        Post.objects.filter(id=13).delete()
        Post.objects.filter(id=12).delete()
        Post.objects.filter(id=11).delete()
        Post.objects.filter(id=10).delete()
        Post.objects.filter(id=9).delete()
        Post.objects.create(
            text='Текст',
            author=self.user,
        )
        len = Post.objects.count()
        resp = self.authorized_client.get(reverse('posts:posts_basedir_path'))
        self.assertEqual(len(resp.context.get('page_obj')), len)
        Post.objects.last().delete()
        self.assertEqual(len(resp.context.get('page_obj')), len)
        cache.clear()
        resp = self.authorized_client.get(reverse('posts:posts_basedir_path'))
        self.assertEqual(len(resp.context.get('page_obj')), len - 1)
