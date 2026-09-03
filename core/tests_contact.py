from django.test import TestCase
from django.urls import reverse

from .models import ContactMessage


class ContactTests(TestCase):
    def test_contact_page_loads(self):
        resp = self.client.get(reverse('core:contact'))
        self.assertEqual(resp.status_code, 200)

    def test_valid_contact_submission_persists(self):
        resp = self.client.post(reverse('core:contact'), {
            'name': 'Test User', 'email': 'test@example.com',
            'subject': 'Question about an order', 'message': 'Hello, when will my order ship?',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(ContactMessage.objects.count(), 1)
        msg = ContactMessage.objects.first()
        self.assertEqual(msg.email, 'test@example.com')

    def test_invalid_contact_submission_rejected(self):
        resp = self.client.post(reverse('core:contact'), {
            'name': '', 'email': 'not-an-email', 'subject': '', 'message': '',
        })
        self.assertEqual(resp.status_code, 200)  # re-rendered with errors
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_contact_message_visible_in_admin(self):
        from django.contrib.auth.models import User
        ContactMessage.objects.create(name='A', email='a@example.com', subject='S', message='M')
        admin = User.objects.create_superuser(username='ctadmin', email='a@a.com', password='SuperSecret123!')
        self.client.login(username='ctadmin', password='SuperSecret123!')
        resp = self.client.get('/admin/core/contactmessage/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'S')
