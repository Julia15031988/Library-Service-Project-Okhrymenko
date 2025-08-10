from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

User = get_user_model()


class UserModelTests(TestCase):

    def test_create_user_with_email_successful(self):
        """Тестуємо створення користувача з email і паролем"""
        email = "testuser@example.com"
        password = "Testpass123"
        user = User.objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_no_email_raises_error(self):
        """Створення користувача без email має викликати помилку"""
        with self.assertRaises(ValueError):
            User.objects.create_user(email=None, password="test123")

    def test_create_superuser(self):
        """Створення суперкористувача з відповідними правами"""
        email = "admin@example.com"
        password = "adminpass"
        admin_user = User.objects.create_superuser(email=email, password=password)

        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_create_superuser_with_wrong_is_staff_flag_raises(self):
        """Спроба створити суперкористувача з is_staff=False має викликати помилку"""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="admin2@example.com", password="adminpass", is_staff=False
            )
