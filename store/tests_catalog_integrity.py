"""
Regression tests for the catalog quality-control pass.

These guard against the exact problems the catalog-fix pass targeted:
artificially duplicated product concepts, blank/duplicate image URLs,
duplicate SKUs, and non-idempotent seeding.
"""
from django.core.management import call_command
from django.db.models import Count
from django.test import TestCase

from store.models import Category, Product, ProductVariant


class CatalogSeedIntegrityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_data', verbosity=0)

    def test_minimum_category_count(self):
        self.assertGreaterEqual(Category.objects.count(), 14)

    def test_no_blank_image_urls(self):
        self.assertEqual(Product.objects.filter(image_url='').count(), 0)

    def test_no_duplicate_image_urls(self):
        dupes = (
            Product.objects.values('image_url')
            .annotate(c=Count('id'))
            .filter(c__gt=1)
        )
        self.assertEqual(list(dupes), [])

    def test_no_duplicate_skus(self):
        dupes = (
            Product.objects.values('sku')
            .annotate(c=Count('id'))
            .filter(c__gt=1)
        )
        self.assertEqual(list(dupes), [])

    def test_no_products_missing_name_or_description(self):
        self.assertEqual(Product.objects.filter(name='').count(), 0)
        self.assertEqual(Product.objects.filter(description='').count(), 0)

    def test_every_product_has_a_category(self):
        self.assertEqual(Product.objects.filter(category__isnull=True).count(), 0)

    def test_seed_data_is_idempotent(self):
        """Running the seeder twice must not create duplicate rows."""
        before_products = Product.objects.count()
        before_categories = Category.objects.count()
        before_variants = ProductVariant.objects.count()

        call_command('seed_data', verbosity=0)

        self.assertEqual(Product.objects.count(), before_products)
        self.assertEqual(Category.objects.count(), before_categories)
        self.assertEqual(ProductVariant.objects.count(), before_variants)

    def test_no_near_duplicate_boot_padding(self):
        """Regression guard: previously the catalog had several
        near-identical 'Brown Leather ___ Boot' listings distinguished
        only by a generic adjective (Classic/Vintage/Everyday). Those
        were removed; this locks in that they don't come back."""
        removed_names = {
            'Vintage Brown Leather Boot',
            'Classic Lace-Up Leather Boot',
            'Everyday Brown Leather Boot',
        }
        existing = set(Product.objects.filter(name__in=removed_names).values_list('name', flat=True))
        self.assertEqual(existing, set())

    def test_no_near_duplicate_wallet_padding(self):
        removed_names = {'Compact Leather Wallet', 'Structured Leather Wallet'}
        existing = set(Product.objects.filter(name__in=removed_names).values_list('name', flat=True))
        self.assertEqual(existing, set())
