from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_user_created(self):
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_user_email_unique(self):
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='testuser2',
                email='test@example.com',
                password='testpass123'
            )
