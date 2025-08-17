from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "borrowing", "payment_status", "user_amount", "payment_date")
    list_filter = ("payment_status",)
    search_fields = ("user__email", "borrowing__id")
