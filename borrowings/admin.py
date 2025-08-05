from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("user", "borrowing", "status", "amount", "payment_date")
    list_filter = ("status",)
    search_fields = ("user__email", "borrowing__id")
