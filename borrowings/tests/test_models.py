from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, date
from django.contrib.auth import get_user_model
from library.models import Book
from borrowings.models import Borrowing, Payment

User = get_user_model()

class BorrowingModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", password="pass123")
        self.book = Book.objects.create(title="Test Book", author="Author", cover="HARD", inventory=5, daily_fee=1.50)

    def test_create_borrowing(self):
        expected_return = date.today() + timedelta(days=7)
        borrowing = Borrowing.objects.create(user=self.user, book=self.book, expected_return_date=expected_return)

        self.assertEqual(borrowing.user, self.user)
        self.assertEqual(borrowing.book, self.book)
        self.assertEqual(borrowing.expected_return_date, expected_return)
        self.assertIsNone(borrowing.actual_return_date)
        self.assertIsNotNone(borrowing.borrow_date)
        self.assertIn(self.user.email, str(borrowing))
        self.assertIn(self.book.title, str(borrowing))


class PaymentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="payer@example.com", password="pass123")
        self.book = Book.objects.create(title="Payment Book", author="Author", cover="SOFT", inventory=2, daily_fee=2.00)
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.book,
            expected_return_date=date.today() + timedelta(days=5)
        )

    def test_create_payment_default_status_and_type(self):
        payment = Payment.objects.create(
            borrowing=self.borrowing,
            user_amount=10.00,
            user=self.user,
        )
        self.assertEqual(payment.payment_status, Payment.PaymentStatus.PENDING)
        self.assertEqual(payment.payment_type, Payment.PaymentType.BORROWING)
        self.assertIsNotNone(payment.payment_date)
        self.assertIn(self.user.email, str(payment))
        self.assertIn(payment.payment_status, str(payment))
        self.assertIn(str(payment.user_amount), str(payment))

    def test_payment_status_choices(self):
        payment = Payment.objects.create(
            borrowing=self.borrowing,
            user_amount=5.00,
            user=self.user,
            payment_status=Payment.PaymentStatus.PAID,
            payment_type=Payment.PaymentType.FINE,
        )
        self.assertEqual(payment.payment_status, Payment.PaymentStatus.PAID)
        self.assertEqual(payment.payment_type, Payment.PaymentType.FINE)

