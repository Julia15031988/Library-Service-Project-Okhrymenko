from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date
from django.contrib.auth import get_user_model
from library.models import Book
from borrowings.models import Borrowing, Payment

User = get_user_model()


class BorrowingViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", password="pass123")
        self.other_user = User.objects.create_user(email="other@example.com", password="pass123")
        self.staff = User.objects.create_user(email="staff@example.com", password="pass123", is_staff=True)
        self.book = Book.objects.create(title="Test Book", author="Author", cover="HARD", inventory=3, daily_fee=2.0)
        self.client = APIClient()

    def test_borrowing_list_for_user(self):
        # Створюємо дві позики: одна юзера, одна іншого
        Borrowing.objects.create(user=self.user, book=self.book, expected_return_date=date.today() + timedelta(days=5))
        Borrowing.objects.create(user=self.other_user, book=self.book, expected_return_date=date.today() + timedelta(days=5))

        self.client.force_authenticate(user=self.user)
        url = reverse('borrowing:borrowing-list')  # якщо у тебе namespace 'borrowing', додай 'borrowing:borrowing-list'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Має повернутися тільки одна позика — для цього юзера
        self.assertEqual(len(response.data), 1)


class PaymentViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="payer@example.com", password="pass123")
        self.staff = User.objects.create_user(email="staff@example.com", password="pass123", is_staff=True)
        self.book = Book.objects.create(title="Payment Book", author="Author", cover="SOFT", inventory=2, daily_fee=2.00)
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=5)
        )
        self.payment = Payment.objects.create(
            borrowing=self.borrowing,
            user_amount=10.00,
            user=self.user,
        )
        self.client = APIClient()

    def test_payment_list_for_regular_user(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('borrowing:payment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Має повернути тільки платежі для цього користувача
        for payment in response.data:
            self.assertEqual(payment['user'], self.user.id)

    def test_payment_list_for_staff(self):
        self.client.force_authenticate(user=self.staff)
        url = reverse('borrowing:payment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Повинні бути всі платежі
        self.assertGreaterEqual(len(response.data), 1)
