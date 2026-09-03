from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Profile


class PreferencesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='prefuser', password='SuperSecret123!')
        self.client.login(username='prefuser', password='SuperSecret123!')

    def test_preferences_page_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse('accounts:preferences'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)

    def test_preferences_page_loads_and_creates_profile(self):
        resp = self.client.get(reverse('accounts:preferences'))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_saving_preferences_persists(self):
        resp = self.client.post(reverse('accounts:preferences'), {
            'theme_preference': 'dark', 'newsletter_opt_in': 'on', 'order_update_emails': 'on',
        })
        self.assertEqual(resp.status_code, 302)
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.theme_preference, 'dark')
        self.assertTrue(profile.newsletter_opt_in)

    def test_unchecking_newsletter_persists_false(self):
        Profile.objects.create(user=self.user, newsletter_opt_in=True)
        self.client.post(reverse('accounts:preferences'), {
            'theme_preference': 'system',
            # newsletter_opt_in intentionally omitted -> should become False
        })
        profile = Profile.objects.get(user=self.user)
        self.assertFalse(profile.newsletter_opt_in)

    def test_dark_preference_is_reflected_in_page_render(self):
        """Regression test: saving a theme preference must actually change what's
        rendered, not just what's stored (previously localStorage silently won
        forever and the saved preference never took visible effect)."""
        Profile.objects.update_or_create(user=self.user, defaults={'theme_preference': 'dark'})
        resp = self.client.get(reverse('accounts:preferences'))
        content = resp.content.decode()
        self.assertIn('data-user-theme-pref="dark"', content)
        self.assertIn("var dbPref = 'dark';", content)

    def test_light_preference_is_reflected_in_page_render(self):
        Profile.objects.update_or_create(user=self.user, defaults={'theme_preference': 'light'})
        resp = self.client.get(reverse('accounts:preferences'))
        content = resp.content.decode()
        self.assertIn('data-user-theme-pref="light"', content)
        self.assertIn("var dbPref = 'light';", content)

    def test_system_preference_omits_user_theme_pref_attribute(self):
        Profile.objects.update_or_create(user=self.user, defaults={'theme_preference': 'system'})
        resp = self.client.get(reverse('accounts:preferences'))
        content = resp.content.decode()
        self.assertNotIn('data-user-theme-pref=', content)
        self.assertIn("var dbPref = 'system';", content)

    def test_registration_creates_profile(self):
        self.client.logout()
        self.client.post(reverse('accounts:register'), {
            'first_name': 'New', 'last_name': 'User', 'email': 'newuser@example.com',
            'username': 'newprefuser', 'password1': 'SuperSecret123!', 'password2': 'SuperSecret123!',
        })
        new_user = User.objects.get(username='newprefuser')
        self.assertTrue(Profile.objects.filter(user=new_user).exists())
