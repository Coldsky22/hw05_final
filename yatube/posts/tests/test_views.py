import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post

SEC_NUMBER_OF_TEST_POSTS: int = 2
NUMBER_OF_TEST_POSTS: int = 13
FULL_PAGE: int = 10
DOS: int = 2
TRES: int = 3
CINK: int = 5


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cache.clear()
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test_group',
                                         description='первая группа')
        cls.author = User.objects.create(username='test_user')
        cls.post = Post.objects.create(
            text='Тестовый пост', author=cls.author, group=cls.group,
            image=cls.uploaded)
        cls.pk = PostsURLTests.post.pk
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)
        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug':
                                                PostsURLTests.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username':
                                             PostsURLTests.author}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': PostsURLTests.pk}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': PostsURLTests.pk}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def tearDown(self) -> None:
        cache.clear()

    def posts_check_all_fields(self, post):
        """Метод, проверяющий поля поста."""
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.pk, self.post.group.pk)

    def test_pages_uses_correct_template(self):
        cache.clear()
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_correct_context(self):
        response = self.authorized_author.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_profile_page_have_correct_context(self):
        response = self.authorized_author.get(
            reverse('posts:profile', kwargs={'username': self.author}))
        self.assertIn('title', response.context)
        self.assertIn('author', response.context)
        self.assertIn('page_obj', response.context)
        self.assertIn('post_total', response.context)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('posts:post_detail', kwargs={'post_id': (self.post.pk)}))
        self.assertIn('post', response.context)
        self.assertIn('count_posts', response.context)
        self.assertIn('title', response.context)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_page_show_correct_context(self):
        """Шаблон редиактирования поста сформирован с правильным контекстом."""
        response = self.authorized_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_add_comment_correct_context(self):
        """Проверка add_comment
        комментарий появляется на странице поста
        комментировать посты может только
        авторизованный пользователь.
        """

        tasks_count = Post.objects.count()
        form_data = {
            'post': self.post,
            'author': self.post.author,
            'text': 'Тестовый текст комментария',
            'image': self.uploaded,
        }

        response = self.authorized_author.post(
            reverse('posts:add_comment', args=[self.post.pk]),
            data=form_data
        )
        self.uploaded.close

        self.assertEqual(Post.objects.count(), tasks_count)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args=[self.post.pk])
        )
        last_comment = get_object_or_404(Comment, post=self.post)

        self.assertEqual(last_comment.post, self.post)
        self.assertEqual(last_comment.author, self.post.author)
        self.assertEqual(last_comment.text, 'Тестовый текст комментария')
        cache.clear()


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test-group',
                                         description='первая группа')
        cls.second_group = Group.objects.create(title='Вторая группа',
                                                slug='test-slug-new',
                                                description='Вторая группа')
        cls.author = User.objects.create(username='test_user')
        cls.second_author = User.objects.create(username='test_user2')
        Post.objects.bulk_create([
            Post(text=f"some text {i}", author=cls.author, group=cls.group)
            for i in range(NUMBER_OF_TEST_POSTS)
        ])
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)
        Post.objects.bulk_create([Post(
            text=f'Тестовый пост, тестовый пост, тестовый пост {i}',
            author=cls.second_author,
            group=cls.second_group)
            for i in range(SEC_NUMBER_OF_TEST_POSTS)
        ])
        cls.authorized_author2 = Client()
        cls.authorized_author2.force_login(cls.second_author)
        cache.clear()

    def test_paginator_pages_name(self):
        paginatores = {
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
            + '?page=2': TRES,
            reverse('posts:profile', kwargs={'username': self.author})
            + '?page=2': TRES,
            reverse('posts:index') + '?page=2': CINK,
            reverse('posts:profile', kwargs={'username': self.author}):
            FULL_PAGE,
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            FULL_PAGE,
            reverse('posts:index'): FULL_PAGE

        }
        for page, expected_value in paginatores.items():
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(
                    len(response.context['page_obj']), expected_value)

    def test_paginator_pages_name(self):
        paginatores = {
            reverse('posts:profile', kwargs={'username': self.second_author}):
            DOS,
            reverse('posts:group_list',
                    kwargs={'slug': self.second_group.slug}): DOS
        }
        for page, expected_value in paginatores.items():
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(
                    len(response.context['page_obj']), expected_value)

    def test_profile_unfollow(self):
        followers_count = Follow.objects.count()
        self.authorized_author.post(
            reverse('posts:profile_follow', args=[self.author]))
        response = self.authorized_author.post(
            reverse('posts:profile_unfollow',
                    args=[self.author])
        )
        self.assertRedirects(response, reverse('posts:profile',
                             args=[self.author])
                             )
        self.assertFalse(Follow.objects.all().exists())
        self.assertEqual(Follow.objects.count(), followers_count)
