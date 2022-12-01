from http import HTTPStatus
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache

from ..models import Post, Group

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group'
        )
        cls.author = User.objects.create(username='test_user')
        Post.objects.create(
            text='Тестовый пост',
            author=cls.author
        )
        cls.url_template_name = {
            '/': 'posts/index.html',
            '/group/test-group/': 'posts/group_list.html',
            '/profile/test_user/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='my_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author_client = Client()
        self.post_author_client.force_login(PostsURLTests.author)
        cache.clear()

    def test_urls_use_correct_templates(self):
        for url, template in self.url_template_name.items():
            with self.subTest(url=url):
                response = self.post_author_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page(self):
        """Несуществующая Страница доступна любому пользователю."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_group_url_exists_at_desired_location(self):
        """Страница /group/ доступна любому пользователю."""
        response = self.guest_client.get('/group/test-group/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_exists_at_desired_location(self):
        """Страница /profile/ доступна любому пользователю."""
        response = self.guest_client.get('/profile/test_user/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_detail_url_exists_at_desired_location(self):
        """Страница /posts/post_id доступна любому
        пользователю."""
        response = self.guest_client.get('/posts/1/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_anonymous(self):
        """Страница /edit/ перенаправляет анонимного пользователя."""
        response = self.guest_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_create_url_redirect_anonymous(self):
        """Страница /create/ перенаправляет анонимного
        пользователя.
        """
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_create_authorized(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_author(self):
        """Страница /edit/ доступна автору."""
        response = self.post_author_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
