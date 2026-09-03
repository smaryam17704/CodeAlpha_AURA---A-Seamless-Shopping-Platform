from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from store.models import Category, Product


class CoreTests(TestCase):
    def test_home_page_loads(self):
        resp = self.client.get(reverse('core:home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Find Your Kind of')

    def test_journal_page_loads(self):
        resp = self.client.get(reverse('core:journal'))
        self.assertEqual(resp.status_code, 200)

    def test_newsletter_signup_valid_email(self):
        resp = self.client.post(
            reverse('core:newsletter_signup'), {'email': 'sub@example.com'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        data = resp.json()
        self.assertTrue(data['success'])
        from store.models import NewsletterSubscriber
        self.assertTrue(NewsletterSubscriber.objects.filter(email='sub@example.com').exists())

    def test_newsletter_signup_invalid_email(self):
        resp = self.client.post(
            reverse('core:newsletter_signup'), {'email': 'not-an-email'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        data = resp.json()
        self.assertFalse(data['success'])

    def test_custom_404_page_renders_when_debug_false(self):
        with self.settings(DEBUG=False, ALLOWED_HOSTS=['testserver']):
            resp = self.client.get('/this-page-does-not-exist/')
            self.assertEqual(resp.status_code, 404)
            self.assertContains(resp, 'wandered off', status_code=404)


class AdminAccessTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_superuser(username='staffadmin', email='s@a.com', password='SuperSecret123!')
        self.regular = User.objects.create_user(username='regular', password='SuperSecret123!')
        self.category = Category.objects.create(name='Essentials')

    def test_non_staff_cannot_reach_admin(self):
        self.client.login(username='regular', password='SuperSecret123!')
        resp = self.client.get('/admin/store/product/add/')
        self.assertNotEqual(resp.status_code, 200)  # redirected away, never sees the form

    def test_staff_can_create_product_via_admin(self):
        self.client.login(username='staffadmin', password='SuperSecret123!')
        resp = self.client.post('/admin/store/product/add/', {
            'name': 'Admin Created Item', 'category': self.category.id, 'short_description': 'x',
            'description': 'Created in a test.', 'price': '500.00', 'sku': 'ADM-TST-001',
            'stock_quantity': '5', 'is_active': 'on',
            'variants-TOTAL_FORMS': '0', 'variants-INITIAL_FORMS': '0',
            'variants-MIN_NUM_FORMS': '0', 'variants-MAX_NUM_FORMS': '1000',
            'gallery_images-TOTAL_FORMS': '0', 'gallery_images-INITIAL_FORMS': '0',
            'gallery_images-MIN_NUM_FORMS': '0', 'gallery_images-MAX_NUM_FORMS': '1000',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Product.objects.filter(sku='ADM-TST-001').exists())

    def test_staff_can_delete_product_via_admin(self):
        product = Product.objects.create(
            name='To Delete', category=self.category, price=100, stock_quantity=1, sku='DEL-001',
        )
        self.client.login(username='staffadmin', password='SuperSecret123!')
        resp = self.client.post(f'/admin/store/product/{product.id}/delete/', {'post': 'yes'})
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Product.objects.filter(id=product.id).exists())
