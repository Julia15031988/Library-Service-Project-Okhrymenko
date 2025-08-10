from rest_framework import viewsets, status, permissions
from django_filters.rest_framework import FilterSet, filters, DjangoFilterBackend
from .models import Borrowing, Payment
from .serializers import BorrowingSerializer, PaymentSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.timezone import now
from notifications.telegram import send_telegram_notification
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import stripe
from datetime import date


stripe.api_key = settings.STRIPE_SECRET_KEY


class BorrowingFilter(FilterSet):
    is_active = filters.BooleanFilter(method="filter_is_active")
    user_id = filters.NumberFilter(field_name="user__id")

    class Meta:
        model = Borrowing
        fields = ["is_active", "user_id"]

    def filter_is_active(self, queryset, name, value):
        if value:
            return queryset.filter(actual_return_date__isnull=True)
        return queryset.filter(actual_return_date__isnull=False)


def _create_stripe_session(request, borrowing, amount, payment_type):
    """
    Helper function to create a Stripe checkout session and a Payment object.
    """
    # Перевірка на вже існуючий платіж у стані PENDING
    if Payment.objects.filter(borrowing=borrowing, payment_status=Payment.PaymentStatus.PENDING).exists():
        return None, Response({"detail": "Pending payment already exists for this borrowing."},
                              status=status.HTTP_400_BAD_REQUEST)

    domain = request.build_absolute_uri("/")[:-1]
    success_url = domain + reverse("borrowing:payment-success") + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = domain + reverse("borrowing:payment-cancel")

    try:
        session = stripe.checkout.Session.create(
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"{payment_type.capitalize()} for {borrowing.book.title}",
                    },
                    "unit_amount": int(amount * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except stripe.error.StripeError as e:
        return None, Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    payment = Payment.objects.create(
        borrowing=borrowing,
        user=borrowing.user,
        user_amount=amount,
        payment_status=Payment.PaymentStatus.PENDING,
        payment_type=payment_type,
        session_url=session.url,
        session_id=session.id
    )
    return payment, None


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BorrowingFilter

    def get_queryset(self):
        queryset = Borrowing.objects.all()

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        else:
            user_id = self.request.query_params.get("user_id")
            if user_id:
                queryset = queryset.filter(user__id=user_id)

        return queryset

    @action(detail=True, methods=["post"])
    def return_book(self, request, pk=None):
        borrowing = self.get_object()

        if borrowing.actual_return_date is not None:
            return Response(
                {"error": "This borrowing has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        borrowing.actual_return_date = date.today()
        borrowing.save()

        borrowing.book.inventory += 1
        borrowing.book.save()

        if borrowing.actual_return_date > borrowing.expected_return_date:
            overdue_days = (
                    borrowing.actual_return_date - borrowing.expected_return_date
            ).days
            fine_amount = overdue_days * borrowing.book.daily_fee * settings.FINE_MULTIPLIER

            payment, error_response = _create_stripe_session(
                request, borrowing, fine_amount, Payment.PaymentType.FINE
            )
            if error_response:
                return error_response

            return Response(
                {
                    "message": f"Book returned with delay. Fine payment of {fine_amount} USD has been created.",
                    "checkout_url": payment.session_url
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"message": "Book successfully returned."}, status=status.HTTP_200_OK
        )

    def perform_create(self, serializer):
        borrowing = serializer.save(user=self.request.user)
        message = (
            f"📚 New Borrowing Created\n\n"
            f"User: {borrowing.user.email}\n"
            f"Book: {borrowing.book.title}\n"
            f"Borrow date: {borrowing.borrow_date}\n"
            f"Expected return: {borrowing.expected_return_date}"
        )
        send_telegram_notification(message)
        # Створення Stripe сесії одразу після створення позики.
        days = (borrowing.expected_return_date - borrowing.borrow_date.date()).days
        amount = float(days * borrowing.book.daily_fee)
        _create_stripe_session(
            self.request, borrowing, amount, Payment.PaymentType.BORROWING
        )


class IsAdminOrOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        # Виправлено: тепер перевіряємо через об'єкт borrowing
        return request.user.is_staff or obj.borrowing.user == request.user


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminOrOwner]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(borrowing__user=user)

    @action(detail=False, methods=["get"], url_path="success", name="payment-success")
    def payment_success(self, request):
        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response(
                {"detail": "No session_id provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = Payment.objects.get(session_id=session_id)
        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment not found."}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid":
                payment.payment_status = Payment.PaymentStatus.PAID
                payment.save()
                return Response({"detail": "Payment was successful!"}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "Payment was not successful."}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.StripeError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="cancel", name="payment-cancel")
    def payment_cancel(self, request):
        return Response(
            {"detail": "Payment was cancelled. You can try again within 24 hours."},
            status=status.HTTP_200_OK,
        )
