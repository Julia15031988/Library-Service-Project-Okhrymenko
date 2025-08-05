from django.db import models
from django.conf import settings
from library.models import Book
from django.contrib.auth import get_user_model


User = get_user_model()


class Borrowing(models.Model):
    borrow_date = models.DateTimeField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.email} borrowed {self.book.title}"


class Payment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = "Pending"
        PAID = "Paid"
        FAILED = "Failed"

    borrowing = models.ForeignKey(
        "Borrowing", on_delete=models.CASCADE, related_name="payments"
    )
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices)
    user_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")

    session_url = models.URLField(blank=True, null=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - {self.payment_status} - {self.user_amount}"
