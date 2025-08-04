from rest_framework import viewsets, status
from django_filters.rest_framework import FilterSet, filters, DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from .models import Borrowing
from .serializers import BorrowingSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.timezone import now


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
                status=status.HTTP_400_BAD_REQUEST
            )

        borrowing.actual_return_date = now()
        borrowing.save()

        borrowing.book.inventory += 1
        borrowing.book.save()

        return Response(
            {"message": "Book successfully returned."},
            status=status.HTTP_200_OK
        )
