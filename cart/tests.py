from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from store.models import Category, Product
from .models import Cart, CartItem


class CartTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Essentials')
        self.product = Product.objects.create(
            name='Canvas Tote', category=self.category, price=Decimal('1000.00'),
            stock_quantity=5, sku='CART-001',
        )

    def test_guest_add_to_cart(self):
        resp = self.client.post(
            reverse('cart:add_to_cart', args=[self.product.id]),
            {'quantity': 2}, HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_item_count'], 2)

    def test_add_to_cart_rejects_out_of_stock(self):
        self.product.stock_quantity = 0
        self.product.save()
        resp = self.client.post(
            reverse('cart:add_to_cart', args=[self.product.id]),
            {'quantity': 1}, HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()['success'])

    def test_add_to_cart_clamps_quantity_to_stock(self):
        resp = self.client.post(
            reverse('cart:add_to_cart', args=[self.product.id]),
            {'quantity': 999}, HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        data = resp.json()
        self.assertEqual(data['cart_item_count'], 5)  # clamped to stock

    def test_update_cart_item_quantity(self):
        self.client.post(reverse('cart:add_to_cart', args=[self.product.id]), {'quantity': 1})
        item = CartItem.objects.first()
        resp = self.client.post(
            reverse('cart:update_cart_item', args=[item.id]),
            {'quantity': 3}, HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(resp.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)

    def test_update_cart_item_to_zero_removes_it(self):
        self.client.post(reverse('cart:add_to_cart', args=[self.product.id]), {'quantity': 1})
        item = CartItem.objects.first()
        self.client.post(
            reverse('cart:update_cart_item', args=[item.id]),
            {'quantity': 0}, HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())

    def test_remove_from_cart(self):
        self.client.post(reverse('cart:add_to_cart', args=[self.product.id]), {'quantity': 1})
        item = CartItem.objects.first()
        resp = self.client.post(reverse('cart:remove_from_cart', args=[item.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())

    def test_cart_persists_across_requests_for_guest(self):
        self.client.post(reverse('cart:add_to_cart', args=[self.product.id]), {'quantity': 1})
        resp = self.client.get(reverse('cart:cart_detail'))
        self.assertContains(resp, 'Canvas Tote')

    def test_guest_cart_merges_into_user_cart_on_login(self):
        # Guest adds an item
        self.client.post(reverse('cart:add_to_cart', args=[self.product.id]), {'quantity': 2})

        # A user account already exists with an empty cart
        User.objects.create_user(username='merge_user', password='SuperSecret123!')

        # Guest logs in -> cart should merge. The merge itself completes on the
        # request *after* login (login() rotates the session key inside the view,
        # after CartMiddleware has already run for that request), so we follow
        # the real-world redirect the login view issues, exactly as a browser would.
        self.client.post(reverse('accounts:login'), {'username': 'merge_user', 'password': 'SuperSecret123!'}, follow=True)

        user_cart = Cart.objects.get(user__username='merge_user')
        self.assertEqual(user_cart.items.count(), 1)
        self.assertEqual(user_cart.items.first().quantity, 2)
