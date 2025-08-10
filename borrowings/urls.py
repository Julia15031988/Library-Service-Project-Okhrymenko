from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BorrowingViewSet,
    PaymentViewSet,
)

app_name = "borrowing"
router = DefaultRouter()
router.register(r"borrowings", BorrowingViewSet, basename="borrowing")
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("", include(router.urls)),
]
