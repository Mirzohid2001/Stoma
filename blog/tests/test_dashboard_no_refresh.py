from django.contrib.auth import get_user_model
from django.urls import reverse

from blog.tests.base import StomaTestCase


class DashboardNoRefreshTests(StomaTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='pass')
        self.client.login(username='tester', password='pass')

    def test_dashboard_has_no_meta_refresh(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'http-equiv="refresh"')
