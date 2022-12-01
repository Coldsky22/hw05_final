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
            title='Т' * 200,
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост' * 30,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__текстом поста."""
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_group_have_correct_object(self):
        """Проверяем, что у моделей корректно работает __str__ сgroup.title."""
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        task = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    task._meta.get_field(field).verbose_name, expected_value)

    def test_post_helptext_correct_verbose(self):
        """help_text поля text совпадает с ожидаемым."""
        post = PostModelTest.post
        help_text = post._meta.get_field('text').help_text
        self.assertEqual(help_text, "Введите текст поста")

    def test_text_title_max_length_not_exceed(self):
        """Длинный title обрезается и не превышает
        max_length поля title в модели."""
        group = PostModelTest.group
        max_length_title = group._meta.get_field('title').max_length
        length_title = len(group.title)
        self.assertEqual(max_length_title, length_title)
