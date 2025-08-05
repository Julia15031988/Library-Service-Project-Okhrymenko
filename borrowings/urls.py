from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BorrowingViewSet, PaymentViewSet, CreateStripeSessionView, StripeSuccessView, StripeCancelView

app_name = "borrowing"
router = DefaultRouter()
router.register(r"borrowings", BorrowingViewSet, basename="borrowing")
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("", include(router.urls)),
    path("payments/create-session/<int:borrowing_id>/", CreateStripeSessionView.as_view(),
         name="create-stripe-session"),
    path("payments/success/", StripeSuccessView.as_view(), name="payment-success"),
    path("payments/cancel/", StripeCancelView.as_view(), name="payment-cancel"),
]
