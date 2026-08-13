import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nomaya.settings')
django.setup()

from store.models import Product, Review, Coupon
from django.contrib.auth.models import User

# Create a test user for reviews if not exists
user, created = User.objects.get_or_create(username='reviewer', defaults={'email':'reviewer@nomaya.local'})
if created:
    user.set_password('password123')
    user.save()

# Create a promo code
Coupon.objects.get_or_create(code='NOMAYA20', defaults={'discount_percentage': 20})

# Add reviews to all products
comments = [
    "Absolutely beautiful fabric, the drape falls perfectly.",
    "The quality is unmatched. Very comfortable.",
    "A stunning piece. Got so many compliments!",
    "Exactly what I was looking for. Perfect for everyday wear.",
    "The color is exactly as pictured. Very premium feel."
]

products = Product.objects.all()
for product in products:
    if product.reviews.count() < 2:
        for _ in range(random.randint(2, 4)):
            Review.objects.create(
                product=product,
                user=user,
                rating=random.randint(4, 5), # High ratings for demo
                comment=random.choice(comments)
            )

print("Database seeded with Reviews and Coupon (NOMAYA20)!")
