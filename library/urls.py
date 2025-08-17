from django.urls import path, include
from rest_framework import routers
from .models import Book
from .views import BookViewSet

app_name = "library"
router = routers.DefaultRouter()
router.register(r"books", BookViewSet, basename="book")

urlpatterns = [path("", include(router.urls))]
