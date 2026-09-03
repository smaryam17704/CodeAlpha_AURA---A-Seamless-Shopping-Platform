from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from store.models import Category, Product
from .models import Order


class CheckoutTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Essentials')
        self.product = Product.objects.create(
            name='Canvas Tote', category=self.category, price=Decimal('1000.00'),
            stock_quantity=5, sku='ORD-001',
        )
        self.user = User.objects.create_user(username='shopper', password='SuperSecret123!')
        self.client.login(username='shopper', password='SuperSecret123!')
        self.client.post(reverse('cart:add_to_cart', args=[self.product.id]), {'quantity': 2})

    def checkout_payload(self, **overrides):
        payload = {
            'full_name': 'Jane Shopper', 'email': 'jane@example.com', 'phone_number': '9876543210',
            'address_line1': '1 Main St', 'address_line2': '', 'city': 'Bengaluru', 'state': 'Karnataka',
            'postal_code': '560001', 'country': 'India', 'payment_method': 'cash_on_delivery',
        }
        payload.update(overrides)
        return payload

    def test_checkout_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse('orders:checkout'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)

    def test_successful_checkout_creates_order(self):
        resp = self.client.post(reverse('orders:checkout'), self.checkout_payload())
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total, Decimal('2000.00') + Decimal('99.00'))  # below free shipping threshold

    def test_checkout_creates_order_items_with_snapshot(self):
        self.client.post(reverse('orders:checkout'), self.checkout_payload())
        order = Order.objects.first()
        item = order.items.first()
        self.assertEqual(item.product_name, 'Canvas Tote')
        self.assertEqual(item.unit_price, Decimal('1000.00'))
        self.assertEqual(item.quantity, 2)

    def test_checkout_reduces_stock(self):
        self.client.post(reverse('orders:checkout'), self.checkout_payload())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)  # 5 - 2

    def test_checkout_clears_cart(self):
        self.client.post(reverse('orders:checkout'), self.checkout_payload())
        resp = self.client.get(reverse('cart:cart_detail'))
        self.assertContains(resp, 'Your selection is waiting')

    def test_checkout_blocked_when_cart_empty(self):
        self.client.post(reverse('cart:remove_from_cart', args=[self.user.cart.items.first().id]))
        resp = self.client.get(reverse('orders:checkout'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('store:shop'))

    def test_checkout_blocked_when_stock_insufficient(self):
        self.product.stock_quantity = 1  # less than the 2 already in cart
        self.product.save()
        resp = self.client.get(reverse('orders:checkout'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('cart:cart_detail'))
        self.assertEqual(Order.objects.count(), 0)

    def test_order_history_shows_own_orders_only(self):
        self.client.post(reverse('orders:checkout'), self.checkout_payload())
        other_user = User.objects.create_user(username='other', password='SuperSecret123!')

        resp = self.client.get(reverse('orders:order_history'))
        self.assertContains(resp, Order.objects.first().order_number)

        self.client.logout()
        self.client.login(username='other', password='SuperSecret123!')
        resp2 = self.client.get(reverse('orders:order_history'))
        self.assertNotContains(resp2, Order.objects.first().order_number)

    def test_order_detail_ownership_protected(self):
        self.client.post(reverse('orders:checkout'), self.checkout_payload())
        order = Order.objects.first()

        User.objects.create_user(username='intruder', password='SuperSecret123!')
        self.client.logout()
        self.client.login(username='intruder', password='SuperSecret123!')

        resp = self.client.get(reverse('orders:order_detail', args=[order.order_number]))
        self.assertEqual(resp.status_code, 404)
