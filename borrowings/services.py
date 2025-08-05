import stripe
from django.conf import settings
from .models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_session_for_borrowing(borrowing):
    days = (borrowing.expected_return_date - borrowing.borrow_date).days
    amount = days * 1.5  # логіка розрахунку ціни

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f'Borrowing Book ID {borrowing.id}',
                },
                'unit_amount': int(amount * 100),  # у центах
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=settings.DOMAIN + '/api/payments/success/',
        cancel_url=settings.DOMAIN + '/api/payments/cancel/',
    )

    payment = Payment.objects.create(
        user=borrowing.user,
        borrowing=borrowing,
        payment_status='PENDING',
        user_amount=amount,
        session_url=session.url,
        session_id=session.id,
    )
    return payment
