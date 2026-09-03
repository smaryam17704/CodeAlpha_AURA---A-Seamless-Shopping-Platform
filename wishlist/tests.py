from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from store.models import Category, Product
from .models import WishlistItem


class WishlistTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Essentials')
        self.product = Product.objects.create(
            name='Canvas Tote', category=self.category, price=Decimal('1000.00'),
            stock_quantity=5, sku='WISH-001',
        )
        self.user = User.objects.create_user(username='wisher', password='SuperSecret123!')

    def test_wishlist_requires_login(self):
        resp = self.client.post(reverse('wishlist:toggle_wishlist', args=[self.product.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)

    def test_toggle_adds_and_removes(self):
        self.client.login(username='wisher', password='SuperSecret123!')
        resp = self.client.post(
            reverse('wishlist:toggle_wishlist', args=[self.product.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertTrue(resp.json()['added'])
        self.assertEqual(WishlistItem.objects.count(), 1)

        resp2 = self.client.post(
            reverse('wishlist:toggle_wishlist', args=[self.product.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertFalse(resp2.json()['added'])
        self.assertEqual(WishlistItem.objects.count(), 0)

    def test_wishlist_page_shows_items(self):
        self.client.login(username='wisher', password='SuperSecret123!')
        self.client.post(reverse('wishlist:toggle_wishlist', args=[self.product.id]))
        resp = self.client.get(reverse('wishlist:wishlist_detail'))
        self.assertContains(resp, 'Canvas Tote')

    def test_empty_wishlist_state(self):
        self.client.login(username='wisher', password='SuperSecret123!')
        resp = self.client.get(reverse('wishlist:wishlist_detail'))
        self.assertContains(resp, 'Keep what inspires you')
