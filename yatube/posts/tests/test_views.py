from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from ..models import Post, Group, Follow
from django.core.cache import cache
FULL_PAGE: int = 10
DOS: int = 2
TRES: int = 3
CINK: int = 5


User = get_user_model()


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test_group',
                                         description='первая группа')
        cls.author = User.objects.create(username='test_user')
        cls.post = Post.objects.create(text='Тестовый пост', author=cls.author)
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

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        cache.clear()
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_have_correct_context(self):
        cache.clear()
        response = self.authorized_author.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        self.assertIn('title', response.context)

    def test_group_page_have_correct_context(self):
        response = self.authorized_author.get(
            reverse('posts:group_list', kwargs={'slug': 'test_group'}))
        self.assertIn('page_obj', response.context)
        self.assertIn('title', response.context)
        self.assertIn('text', response.context)

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
        for i in range(13):
            Post.objects.create(text='Тестовый пост',
                                author=cls.author,
                                group=cls.group)
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)
        for i in range(2):
            Post.objects.create(text='Тестовый пост',
                                author=cls.second_author,
                                group=cls.second_group)
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
