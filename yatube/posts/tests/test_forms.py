import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from http import HTTPStatus
from django.core.cache import cache
from posts.models import Comment, Group, Post, User
UNO = 1
User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test_group')
        cls.author = User.objects.create_user(username='test_user')
        cls.post = Post.objects.create(text='Тестовый пост',
                                       author=cls.author,
                                       group=cls.group)
        cls.pk = PostsURLTests.post.pk

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest = Client()
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        cache.clear()

    def test_posts_forms_create_post(self):
        """Проверка, создает ли форма пост в базе."""
        post_count = Post.objects.count()
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
            'text': 'Тестовый пост формы',
            'group': PostsURLTests.group.pk,
            'image': uploaded,
        }

        response = self.authorized_author.post(reverse('posts:post_create'),
                                               data=form_data,
                                               follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), (post_count + UNO))
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост формы',
                group=PostsURLTests.group.pk,
                author=PostsURLTests.author.pk,
                image='posts/small.gif'
            ).exists())

    def test_posts_forms_edit_post(self):
        """Редачится ли пост."""
        post_count = Post.objects.count()

        form_data = {
            'text': 'Текст тестого поста',
            'group': self.group.pk,
        }

        self.authorized_author.post(reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.pk},
        ), data=form_data)

        post_endcount = Post.objects.count()

        self.assertEqual(post_count, post_endcount)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=PostsURLTests.group,
            author=PostsURLTests.author,
        ).exists())

    def test_non_autorized_user_cant_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'новый текст',
            'group': PostsURLTests.group.pk,
        }
        self.guest.post(reverse('posts:post_create'), data=form_data)
        self.assertEqual(Post.objects.count(), post_count)

    def test_add_comment(self):
        """Проверка формы комментария"""
        self.comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий'
        }
        response = self.authorized_author.post(
            reverse('posts:add_comment', args=[self.post.pk]),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             args=[self.post.pk])
                             )

        self.assertEqual(
            Comment.objects.count(), self.comments_count + UNO
        )
        self.assertIsInstance(response.context['comments'][0], Comment)

    def test_non_autorized_user_cant_edit_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'новый текст',
            'group': PostsURLTests.group.pk,
        }
        self.guest.post(reverse('posts:post_edit', kwargs={
                        'post_id': self.pk}), data=form_data)
        self.assertEqual(Post.objects.count(), post_count)
