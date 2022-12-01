from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, User


class PostCacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()

        cls.authorized_client.force_login(cls.user)

    def test_cache_index(self):
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content

        Post.objects.create(
            text='abrakadabra',
            author=self.user,
        )
        response_cached = self.authorized_client.get(reverse('posts:index'))

        previous_posts = response_cached.content
        self.assertEqual(previous_posts, posts)
        cache.clear()
        response_new_cached = self.authorized_client.get(
            reverse('posts:index')
        )
        new_posts = response_new_cached.content
        self.assertNotEqual(previous_posts, new_posts)
