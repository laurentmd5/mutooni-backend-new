from django.test import TestCase
from django.urls import reverse

class BasicTests(TestCase):
    def test_home_page(self):
        response = self.client.get('/')
        self.assertIn(response.status_code, [200, 301, 302])
    
    def test_admin_page(self):
        response = self.client.get('/admin/')
        self.assertIn(response.status_code, [200, 302])