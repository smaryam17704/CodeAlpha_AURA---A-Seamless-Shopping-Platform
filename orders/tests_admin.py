from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from store.models import Category, Product
from notifications.models import Notification
from .models import Order, OrderItem


class OrderAdminBehaviorTests(TestCase):
    """Regression tests for the admin quality-control pass: admin auth
    gating and the order-status-change -> notification hook."""

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Apparel')
        cls.product = Product.objects.create(
            name='Admin Test Shirt', category=cls.category, price=Decimal('2000.00'),
            stock_quantity=5, sku='ADMINTEST-001',
        )
        cls.customer = User.objects.create_user(username='admin_test_customer', password='SuperSecret123!')
        cls.staff = User.objects.create_superuser(
            username='admin_test_staff', email='staff@example.com', password='SuperSecret123!'
        )
        cls.order = Order.objects.create(
            user=cls.customer, full_name='Admin Test Customer', email='customer@example.com',
            phone_number='9876543210', shipping_address_line1='1 Admin St',
            shipping_city='Bengaluru', shipping_state='KA', shipping_postal_code='560001',
            subtotal=Decimal('2000.00'), total=Decimal('2000.00'),
        )
        OrderItem.objects.create(
            order=cls.order, product=cls.product, product_name=cls.product.name,
            product_sku=cls.product.sku, unit_price=cls.product.price, quantity=1,
        )

    def test_admin_requires_authentication(self):
        resp = self.client.get('/admin/orders/order/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/admin/login', resp.url)

    def test_non_staff_user_cannot_access_admin(self):
        self.client.login(username='admin_test_customer', password='SuperSecret123!')
        resp = self.client.get('/admin/orders/order/')
        self.assertEqual(resp.status_code, 302)

    def test_staff_user_can_access_order_admin(self):
        self.client.login(username='admin_test_staff', password='SuperSecret123!')
        resp = self.client.get('/admin/orders/order/')
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(f'/admin/orders/order/{self.order.id}/change/')
        self.assertEqual(resp.status_code, 200)

    def test_changing_order_status_via_admin_creates_one_notification(self):
        before = Notification.objects.filter(user=self.customer).count()
        self.client.login(username='admin_test_staff', password='SuperSecret123!')

        resp = self.client.post(
            f'/admin/orders/order/{self.order.id}/change/',
            {
                'user': self.customer.id, 'order_number': self.order.order_number,
                'full_name': self.order.full_name, 'email': self.order.email,
                'phone_number': self.order.phone_number,
                'shipping_address_line1': self.order.shipping_address_line1,
                'shipping_address_line2': '', 'shipping_city': self.order.shipping_city,
                'shipping_state': self.order.shipping_state,
                'shipping_postal_code': self.order.shipping_postal_code,
                'shipping_country': 'India',
                'status': 'confirmed', 'payment_status': self.order.payment_status,
                'subtotal': self.order.subtotal, 'discount': '0.00', 'total': self.order.total,
                'payment_method': 'cash_on_delivery',
                'items-TOTAL_FORMS': '1', 'items-INITIAL_FORMS': '1',
                'items-MIN_NUM_FORMS': '0', 'items-MAX_NUM_FORMS': '1000',
                'items-0-id': OrderItem.objects.get(order=self.order).id,
                'items-0-order': self.order.id,
                'items-0-product': self.product.id,
                'items-0-product_name': self.product.name,
                'items-0-product_sku': self.product.sku,
                'items-0-unit_price': '2000.00',
                'items-0-quantity': '1',
            },
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmed')
        after = Notification.objects.filter(user=self.customer).count()
        self.assertEqual(after, before + 1)
