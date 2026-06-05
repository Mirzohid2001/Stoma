from django.test import TestCase

from blog.middleware import set_current_user


class StomaTestCase(TestCase):
    """ActivityLog signal va thread-local user aralashuvini oldini oladi."""

    def setUp(self):
        set_current_user(None)
        super().setUp()

    def tearDown(self):
        set_current_user(None)
        super().tearDown()
