from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from store.models import Category, Product


def make_product(**kwargs):
    category = kwargs.pop('category', None) or Category.objects.create(name='Test Category')
    defaults = dict(
        name='Test Product', category=category, price=Decimal('1000.00'),
        stock_quantity=10, sku='TEST-001', description='A test product.',
    )
    defaults.update(kwargs)
    return Product.objects.create(**defaults)


class CatalogTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Essentials')
        self.product = make_product(category=self.category, name='Canvas Tote', sku='T-001')

    def test_shop_page_loads(self):
        resp = self.client.get(reverse('store:shop'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Canvas Tote')

    def test_search_matches_name(self):
        resp = self.client.get(reverse('store:shop'), {'q': 'Canvas'})
        self.assertContains(resp, 'Canvas Tote')

    def test_search_no_results(self):
        resp = self.client.get(reverse('store:shop'), {'q': 'NoSuchProductXYZ'})
        self.assertContains(resp, 'Nothing matched your search')

    def test_category_filter(self):
        other_cat = Category.objects.create(name='Apparel')
        make_product(category=other_cat, name='Wool Coat', sku='T-002')
        resp = self.client.get(reverse('store:shop'), {'category': self.category.slug})
        self.assertContains(resp, 'Canvas Tote')
        self.assertNotContains(resp, 'Wool Coat')

    def test_price_filter(self):
        make_product(category=self.category, name='Cheap Item', sku='T-003', price=Decimal('50.00'))
        resp = self.client.get(reverse('store:shop'), {'min_price': '500'})
        self.assertContains(resp, 'Canvas Tote')
        self.assertNotContains(resp, 'Cheap Item')

    def test_sorting_price_low_to_high(self):
        make_product(category=self.category, name='Cheap Item', sku='T-004', price=Decimal('50.00'))
        resp = self.client.get(reverse('store:shop'), {'sort': 'price_low'})
        content = resp.content.decode()
        self.assertLess(content.index('Cheap Item'), content.index('Canvas Tote'))

    def test_product_detail_page(self):
        resp = self.client.get(self.product.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Canvas Tote')

    def test_invalid_product_404(self):
        resp = self.client.get('/shop/does-not-exist/')
        self.assertEqual(resp.status_code, 404)

    def test_out_of_stock_badge(self):
        make_product(category=self.category, name='Sold Out Item', sku='T-005', stock_quantity=0)
        resp = self.client.get(reverse('store:shop'))
        self.assertContains(resp, 'Sold Out')

    def test_recently_viewed_tracked_in_session(self):
        self.client.get(self.product.get_absolute_url())
        session = self.client.session
        self.assertIn(self.product.id, session.get('recently_viewed_ids', []))
