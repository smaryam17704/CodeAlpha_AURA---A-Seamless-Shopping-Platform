from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orders.models import Order
from store.models import Category, Product
from .models import Notification


class NotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='notifyuser', password='SuperSecret123!')

    def test_notification_creation(self):
        n = Notification.objects.create(user=self.user, notif_type='general', message='Hello')
        self.assertFalse(n.is_read)

    def test_create_for_order_status_confirmed(self):
        order = Order.objects.create(
            user=self.user, order_number='AURA-TESTNOTIF', full_name='X', email='x@example.com',
            phone_number='1', shipping_address_line1='a', shipping_city='b', shipping_state='c',
            shipping_postal_code='1', status='confirmed', subtotal=1000, total=1000,
        )
        notif = Notification.create_for_order_status(order, 'confirmed')
        self.assertIsNotNone(notif)
        self.assertIn('AURA-TESTNOTIF', notif.message)

    def test_create_for_order_status_unknown_returns_none(self):
        order = Order.objects.create(
            user=self.user, full_name='X', email='x@example.com', phone_number='1',
            shipping_address_line1='a', shipping_city='b', shipping_state='c', shipping_postal_code='1',
            status='pending', subtotal=1000, total=1000,
        )
        self.assertIsNone(Notification.create_for_order_status(order, 'pending'))

    def test_notification_list_requires_login(self):
        resp = self.client.get(reverse('notifications:notification_list'))
        self.assertEqual(resp.status_code, 302)

    def test_viewing_list_marks_notifications_read(self):
        Notification.objects.create(user=self.user, notif_type='general', message='Test 1')
        Notification.objects.create(user=self.user, notif_type='general', message='Test 2')
        self.client.login(username='notifyuser', password='SuperSecret123!')
        resp = self.client.get(reverse('notifications:notification_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 0)

    def test_checkout_creates_confirmation_notification(self):
        category = Category.objects.create(name='Apparel')
        product = Product.objects.create(
            name='Notif Test Product', category=category, price=Decimal('1000.00'),
            stock_quantity=5, sku='NOTIF-001',
        )
        self.client.login(username='notifyuser', password='SuperSecret123!')
        self.client.post(reverse('cart:add_to_cart', args=[product.id]), {'quantity': 1})
        self.client.post(reverse('orders:checkout'), {
            'full_name': 'X', 'email': 'x@example.com', 'phone_number': '1', 'address_line1': 'a',
            'city': 'b', 'state': 'c', 'postal_code': '1', 'country': 'India', 'payment_method': 'cash_on_delivery',
        })
        self.assertTrue(Notification.objects.filter(user=self.user, notif_type='order_confirmed').exists())
