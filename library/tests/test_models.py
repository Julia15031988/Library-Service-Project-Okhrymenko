from django.test import TestCase
from library.models import Book


class BookModelTest(TestCase):

    def setUp(self):
        self.book = Book.objects.create(
            title="The Great Gatsby",
            author="F. Scott Fitzgerald",
            cover=Book.CoverChoices.HARD,
            inventory=5,
            daily_fee=2.50
        )

    def test_book_str_method(self):
        """Перевіряє, що __str__ повертає коректний формат."""
        self.assertEqual(str(self.book), "The Great Gatsby by F. Scott Fitzgerald")

    def test_book_fields_content(self):
        """Перевіряє збереження всіх полів."""
        self.assertEqual(self.book.title, "The Great Gatsby")
        self.assertEqual(self.book.author, "F. Scott Fitzgerald")
        self.assertEqual(self.book.cover, Book.CoverChoices.HARD)
        self.assertEqual(self.book.inventory, 5)
        self.assertEqual(float(self.book.daily_fee), 2.50)
