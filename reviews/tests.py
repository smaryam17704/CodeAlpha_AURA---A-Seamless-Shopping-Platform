from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orders.models import Order, OrderItem
from store.models import Category, Product
from .models import Review


class ReviewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Essentials')
        self.product = Product.objects.create(
            name='Canvas Tote', category=self.category, price=Decimal('1000.00'),
            stock_quantity=5, sku='REV-001',
        )
        self.user = User.objects.create_user(username='reviewer', password='SuperSecret123!')

    def _give_purchase(self):
        order = Order.objects.create(
            user=self.user, full_name='R', email='r@example.com', phone_number='1',
            shipping_address_line1='a', shipping_city='b', shipping_state='c',
            shipping_postal_code='1', status='delivered', subtotal=1000, total=1000,
        )
        OrderItem.objects.create(order=order, product=self.product, product_name='Canvas Tote', unit_price=1000, quantity=1)

    def test_review_rejected_without_purchase(self):
        self.client.login(username='reviewer', password='SuperSecret123!')
        resp = self.client.post(reverse('reviews:add_review', args=[self.product.id]), {'rating': 5, 'comment': 'Great!'})
        self.assertEqual(Review.objects.count(), 0)
        self.assertEqual(resp.status_code, 302)

    def test_review_accepted_after_purchase(self):
        self._give_purchase()
        self.client.login(username='reviewer', password='SuperSecret123!')
        resp = self.client.post(reverse('reviews:add_review', args=[self.product.id]), {'rating': 5, 'comment': 'Great quality!'})
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.first()
        self.assertTrue(review.is_verified_purchase)

    def test_duplicate_review_rejected(self):
        self._give_purchase()
        self.client.login(username='reviewer', password='SuperSecret123!')
        self.client.post(reverse('reviews:add_review', args=[self.product.id]), {'rating': 5, 'comment': 'First review'})
        self.client.post(reverse('reviews:add_review', args=[self.product.id]), {'rating': 3, 'comment': 'Second attempt'})
        self.assertEqual(Review.objects.count(), 1)

    def test_review_requires_login(self):
        resp = self.client.post(reverse('reviews:add_review', args=[self.product.id]), {'rating': 5, 'comment': 'Nice'})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)
