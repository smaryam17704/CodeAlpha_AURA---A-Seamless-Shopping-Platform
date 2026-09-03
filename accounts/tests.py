from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AuthTests(TestCase):
    def test_registration_creates_user_and_logs_in(self):
        resp = self.client.post(reverse('accounts:register'), {
            'first_name': 'Ada', 'last_name': 'Lovelace', 'email': 'ada@example.com',
            'username': 'ada', 'password1': 'SuperSecret123!', 'password2': 'SuperSecret123!',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(username='ada').exists())
        # confirm session is authenticated
        resp2 = self.client.get(reverse('accounts:account_dashboard'))
        self.assertEqual(resp2.status_code, 200)

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(username='existing', email='dupe@example.com', password='pass12345')
        resp = self.client.post(reverse('accounts:register'), {
            'first_name': 'A', 'last_name': 'B', 'email': 'dupe@example.com',
            'username': 'newuser', 'password1': 'SuperSecret123!', 'password2': 'SuperSecret123!',
        })
        self.assertEqual(resp.status_code, 200)  # re-rendered with errors
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_login_and_logout(self):
        User.objects.create_user(username='bob', password='SuperSecret123!')
        resp = self.client.post(reverse('accounts:login'), {'username': 'bob', 'password': 'SuperSecret123!'})
        self.assertEqual(resp.status_code, 302)
        resp2 = self.client.get(reverse('accounts:account_dashboard'))
        self.assertEqual(resp2.status_code, 200)

        resp3 = self.client.post(reverse('accounts:logout'))
        self.assertEqual(resp3.status_code, 302)
        resp4 = self.client.get(reverse('accounts:account_dashboard'))
        self.assertEqual(resp4.status_code, 302)  # redirected to login

    def test_account_dashboard_requires_login(self):
        resp = self.client.get(reverse('accounts:account_dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)

    def test_address_crud(self):
        User.objects.create_user(username='carol', password='SuperSecret123!')
        self.client.login(username='carol', password='SuperSecret123!')

        resp = self.client.post(reverse('accounts:address_create'), {
            'full_name': 'Carol Danvers', 'phone_number': '9999999999',
            'address_line1': '1 Main St', 'city': 'Bengaluru', 'state': 'Karnataka',
            'postal_code': '560001', 'country': 'India', 'address_type': 'shipping', 'is_default': True,
        })
        self.assertEqual(resp.status_code, 302)

        from accounts.models import Address
        self.assertEqual(Address.objects.filter(user__username='carol').count(), 1)
        addr = Address.objects.get(user__username='carol')

        resp2 = self.client.post(reverse('accounts:address_edit', args=[addr.id]), {
            'full_name': 'Carol D.', 'phone_number': '9999999999',
            'address_line1': '2 Main St', 'city': 'Bengaluru', 'state': 'Karnataka',
            'postal_code': '560002', 'country': 'India', 'address_type': 'shipping', 'is_default': True,
        })
        self.assertEqual(resp2.status_code, 302)
        addr.refresh_from_db()
        self.assertEqual(addr.city, 'Bengaluru')
        self.assertEqual(addr.address_line1, '2 Main St')

        resp3 = self.client.post(reverse('accounts:address_delete', args=[addr.id]))
        self.assertEqual(resp3.status_code, 302)
        self.assertFalse(Address.objects.filter(id=addr.id).exists())
