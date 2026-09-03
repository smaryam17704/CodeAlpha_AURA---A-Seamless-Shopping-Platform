from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from store.models import Category, Product, ProductVariant
from .models import Order, Coupon


class BuyNowTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Apparel')
        self.product = Product.objects.create(
            name='Buy Now Shirt', category=self.category, price=Decimal('2000.00'),
            stock_quantity=5, sku='BUYNOW-001',
        )
        self.user = User.objects.create_user(username='buyer', password='SuperSecret123!')
        self.client.login(username='buyer', password='SuperSecret123!')

    def checkout_payload(self, **overrides):
        payload = {
            'full_name': 'Buy Nower', 'email': 'buyer@example.com', 'phone_number': '9876543210',
            'address_line1': '1 Main St', 'city': 'Bengaluru', 'state': 'Karnataka',
            'postal_code': '560001', 'country': 'India', 'payment_method': 'cash_on_delivery',
        }
        payload.update(overrides)
        return payload

    def test_buy_now_requires_login(self):
        self.client.logout()
        resp = self.client.post(reverse('orders:buy_now', args=[self.product.id]), {'quantity': 1})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)

    def test_buy_now_redirects_to_checkout(self):
        resp = self.client.post(reverse('orders:buy_now', args=[self.product.id]), {'quantity': 1})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('mode=buy_now', resp.url)

    def test_buy_now_does_not_touch_cart(self):
        self.client.post(reverse('orders:buy_now', args=[self.product.id]), {'quantity': 1})
        cart = self.user.cart
        self.assertEqual(cart.items.count(), 0)

    def test_buy_now_checkout_creates_order_without_affecting_cart(self):
        # Put something unrelated in the real cart first
        other_product = Product.objects.create(
            name='Cart Item', category=self.category, price=Decimal('500.00'),
            stock_quantity=5, sku='BUYNOW-002',
        )
        self.client.post(reverse('cart:add_to_cart', args=[other_product.id]), {'quantity': 1})

        self.client.post(reverse('orders:buy_now', args=[self.product.id]), {'quantity': 2})
        resp = self.client.post(f"{reverse('orders:checkout')}?mode=buy_now", self.checkout_payload())
        self.assertEqual(resp.status_code, 302)

        order = Order.objects.first()
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().product_name, 'Buy Now Shirt')
        self.assertEqual(order.items.first().quantity, 2)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)  # 5 - 2

        # The real cart item must be untouched
        cart = self.user.cart
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().product, other_product)

    def test_buy_now_with_variant(self):
        variant = ProductVariant.objects.create(
            product=self.product, size='M', sku='BUYNOW-VAR-M', stock_quantity=4, is_default=True,
        )
        self.product.stock_quantity = 0
        self.product.save()
        resp = self.client.post(
            reverse('orders:buy_now', args=[self.product.id]),
            {'quantity': 1, 'variant_id': variant.id},
        )
        self.assertEqual(resp.status_code, 302)
        self.client.post(f"{reverse('orders:checkout')}?mode=buy_now", self.checkout_payload())
        order = Order.objects.first()
        self.assertEqual(order.items.first().variant_label, variant.label)
        variant.refresh_from_db()
        self.assertEqual(variant.stock_quantity, 3)


class CouponTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Apparel')
        self.product = Product.objects.create(
            name='Coupon Test Product', category=self.category, price=Decimal('3000.00'),
            stock_quantity=5, sku='COUPON-001',
        )
        self.user = User.objects.create_user(username='shopper2', password='SuperSecret123!')
        self.client.login(username='shopper2', password='SuperSecret123!')
        self.client.post(reverse('cart:add_to_cart', args=[self.product.id]), {'quantity': 1})
        self.coupon = Coupon.objects.create(
            code='SAVE10', discount_type='percentage', discount_value=Decimal('10'), active=True,
        )

    def checkout_payload(self, **overrides):
        payload = {
            'full_name': 'Coupon User', 'email': 'coupon@example.com', 'phone_number': '9876543210',
            'address_line1': '1 Main St', 'city': 'Bengaluru', 'state': 'Karnataka',
            'postal_code': '560001', 'country': 'India', 'payment_method': 'cash_on_delivery',
        }
        payload.update(overrides)
        return payload

    def test_valid_coupon_applies_discount(self):
        resp = self.client.post(reverse('orders:checkout'), self.checkout_payload(coupon_code='SAVE10'))
        self.assertEqual(resp.status_code, 302)
        order = Order.objects.first()
        self.assertEqual(order.discount, Decimal('300.00'))  # 10% of 3000
        self.assertEqual(order.coupon, self.coupon)

    def test_invalid_coupon_rejected(self):
        resp = self.client.post(reverse('orders:checkout'), self.checkout_payload(coupon_code='NOTREAL'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Order.objects.count(), 0)

    def test_coupon_minimum_order_enforced(self):
        self.coupon.minimum_order_amount = Decimal('5000.00')
        self.coupon.save()
        resp = self.client.post(reverse('orders:checkout'), self.checkout_payload(coupon_code='SAVE10'))
        self.assertEqual(Order.objects.count(), 0)

    def test_checkout_without_coupon_has_zero_discount(self):
        resp = self.client.post(reverse('orders:checkout'), self.checkout_payload())
        order = Order.objects.first()
        self.assertEqual(order.discount, Decimal('0.00'))


class PaymentStatusAndDeliveryStatusTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Apparel')
        self.product = Product.objects.create(
            name='Status Test Product', category=self.category, price=Decimal('1500.00'),
            stock_quantity=5, sku='STATUS-001',
        )
        self.user = User.objects.create_user(username='statususer', password='SuperSecret123!')
        self.client.login(username='statususer', password='SuperSecret123!')
        self.client.post(reverse('cart:add_to_cart', args=[self.product.id]), {'quantity': 1})

    def test_cod_order_is_pending_payment(self):
        self.client.post(reverse('orders:checkout'), {
            'full_name': 'X', 'email': 'x@example.com', 'phone_number': '1', 'address_line1': 'a',
            'city': 'b', 'state': 'c', 'postal_code': '1', 'country': 'India', 'payment_method': 'cash_on_delivery',
        })
        order = Order.objects.first()
        self.assertEqual(order.payment_status, 'pending')

    def test_card_order_is_marked_paid(self):
        self.client.post(reverse('orders:checkout'), {
            'full_name': 'X', 'email': 'x@example.com', 'phone_number': '1', 'address_line1': 'a',
            'city': 'b', 'state': 'c', 'postal_code': '1', 'country': 'India', 'payment_method': 'card',
        })
        order = Order.objects.first()
        self.assertEqual(order.payment_status, 'paid')

    def test_out_for_delivery_in_status_steps(self):
        self.assertIn('out_for_delivery', Order.STATUS_STEPS)

    def test_out_for_delivery_display_label(self):
        order = Order.objects.create(
            user=self.user, full_name='X', email='x@example.com', phone_number='1',
            shipping_address_line1='a', shipping_city='b', shipping_state='c', shipping_postal_code='1',
            status='out_for_delivery', subtotal=1000, total=1000,
        )
        resp = self.client.get(reverse('orders:order_detail', args=[order.order_number]))
        self.assertContains(resp, 'Out for Delivery')
