from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product, ProductVariant


class VariantTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Apparel')
        self.product = Product.objects.create(
            name='Test Shirt', category=self.category, price=Decimal('1000.00'),
            stock_quantity=0, sku='VAR-TEST-001',
        )
        self.variant_a = ProductVariant.objects.create(
            product=self.product, size='M', color='Blue', sku='VAR-TEST-001-BLU-M',
            stock_quantity=5, is_default=True,
        )
        self.variant_b = ProductVariant.objects.create(
            product=self.product, size='L', color='Blue', sku='VAR-TEST-001-BLU-L',
            stock_quantity=0,
        )

    def test_product_has_variants_true(self):
        self.assertTrue(self.product.has_variants)

    def test_default_variant_resolves(self):
        self.assertEqual(self.product.default_variant, self.variant_a)

    def test_variant_label(self):
        self.assertEqual(self.variant_a.label, 'Blue / M')

    def test_variant_effective_price_falls_back_to_product(self):
        self.assertEqual(self.variant_a.effective_price, self.product.price)

    def test_variant_price_override(self):
        self.variant_a.price_override = Decimal('1200.00')
        self.variant_a.save()
        self.assertEqual(self.variant_a.effective_price, Decimal('1200.00'))

    def test_only_one_default_variant_enforced(self):
        self.variant_b.is_default = True
        self.variant_b.save()
        self.variant_a.refresh_from_db()
        self.assertFalse(self.variant_a.is_default)

    def test_product_detail_shows_variant_selector(self):
        resp = self.client.get(self.product.get_absolute_url())
        self.assertContains(resp, 'variant-select')
        self.assertContains(resp, 'Blue / M')


class CartVariantTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Apparel')
        self.product = Product.objects.create(
            name='Test Shirt', category=self.category, price=Decimal('1000.00'),
            stock_quantity=0, sku='VAR-CART-001',
        )
        self.variant = ProductVariant.objects.create(
            product=self.product, size='M', color='Red', sku='VAR-CART-001-RED-M',
            stock_quantity=3, is_default=True,
        )

    def test_add_to_cart_requires_variant_selection(self):
        resp = self.client.post(
            reverse('cart:add_to_cart', args=[self.product.id]),
            {'quantity': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()['success'])

    def test_add_to_cart_with_valid_variant(self):
        resp = self.client.post(
            reverse('cart:add_to_cart', args=[self.product.id]),
            {'quantity': 1, 'variant_id': self.variant.id},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['success'])

    def test_add_to_cart_rejects_out_of_stock_variant(self):
        self.variant.stock_quantity = 0
        self.variant.save()
        resp = self.client.post(
            reverse('cart:add_to_cart', args=[self.product.id]),
            {'quantity': 1, 'variant_id': self.variant.id},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(resp.status_code, 400)

    def test_add_to_cart_clamps_to_variant_stock(self):
        resp = self.client.post(
            reverse('cart:add_to_cart', args=[self.product.id]),
            {'quantity': 999, 'variant_id': self.variant.id},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        data = resp.json()
        self.assertEqual(data['cart_item_count'], 3)  # clamped to variant stock


class RatingFilterTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Apparel')
        self.high_rated = Product.objects.create(
            name='Five Star Product', category=self.category, price=Decimal('1000.00'),
            stock_quantity=5, sku='RATE-001',
        )
        self.low_rated = Product.objects.create(
            name='Two Star Product', category=self.category, price=Decimal('1000.00'),
            stock_quantity=5, sku='RATE-002',
        )
        from reviews.models import Review
        u1 = User.objects.create_user(username='rater1', password='pass12345')
        u2 = User.objects.create_user(username='rater2', password='pass12345')
        Review.objects.create(product=self.high_rated, user=u1, rating=5, comment='Excellent')
        Review.objects.create(product=self.low_rated, user=u2, rating=2, comment='Meh')

    def test_rating_filter_returns_only_high_rated(self):
        resp = self.client.get(reverse('store:shop'), {'min_rating': '4'})
        self.assertContains(resp, 'Five Star Product')
        self.assertNotContains(resp, 'Two Star Product')

    def test_rating_filter_combines_with_category(self):
        resp = self.client.get(reverse('store:shop'), {'min_rating': '4', 'category': self.category.slug})
        self.assertContains(resp, 'Five Star Product')
