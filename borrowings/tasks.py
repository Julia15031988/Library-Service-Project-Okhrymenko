from celery import shared_task
from django.utils.timezone import now
from borrowings.models import Borrowing
import requests

@shared_task
def send_telegram_message(token: str, chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    response = requests.post(url, data=data)
    return response.ok

@shared_task
def check_overdue_borrowings():
    today = now().date()
    token = "YOUR_TELEGRAM_BOT_TOKEN"
    chat_id = "YOUR_TELEGRAM_CHAT_ID"

    overdue_borrowings = Borrowing.objects.filter(
        expected_return_date__lte=today,
        returned=False
    )

    if not overdue_borrowings.exists():
        send_telegram_message.delay(token, chat_id, "No borrowings overdue today!")
        return "No overdue borrowings"

    for b in overdue_borrowings:
        text = (
            f"📚 <b>Overdue Borrowing Alert</b>\n"
            f"Book: {b.book.title}\n"
            f"Borrower: {b.user.get_full_name() or b.user.username}\n"
            f"Expected Return Date: {b.expected_return_date}\n"
            f"Days Overdue: {(today - b.expected_return_date).days}\n"
        )
        send_telegram_message.delay(token, chat_id, text)
    return "Overdue notifications sent"
