from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import User


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_data = {
            'email': 'student@colohouse.com',
            'first_name': 'Student',
            'last_name': 'Test',
            'password': 'StrongPass123!',
        }

    def test_register_creates_user(self):
        response = self.client.post(reverse('accounts:register'), self.register_data)
        self.assertEqual(response.status_code, 201)
        self.assertNotIn('password', response.data)
        user = User.objects.get(email='student@colohouse.com')
        self.assertTrue(user.check_password('StrongPass123!'))

    def test_register_duplicate_email_is_rejected(self):
        self.client.post(reverse('accounts:register'), self.register_data)
        data = {**self.register_data, 'email': 'STUDENT@colohouse.com'}
        response = self.client.post(reverse('accounts:register'), data)
        self.assertEqual(response.status_code, 400)

    def test_register_weak_password_is_rejected(self):
        data = {**self.register_data, 'password': '123'}
        response = self.client.post(reverse('accounts:register'), data)
        self.assertEqual(response.status_code, 400)

    def test_login_returns_tokens(self):
        self.client.post(reverse('accounts:register'), self.register_data)
        response = self.client.post(reverse('accounts:login'), {
            'email': 'Student@colohouse.com',
            'password': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        self.client.post(reverse('accounts:register'), self.register_data)
        response = self.client.post(reverse('accounts:login'), {
            'email': 'student@colohouse.com',
            'password': 'wrong-password',
        })
        self.assertEqual(response.status_code, 401)

    def test_me_requires_token(self):
        response = self.client.get(reverse('accounts:me'))
        self.assertEqual(response.status_code, 401)

    def test_me_with_token(self):
        self.client.post(reverse('accounts:register'), self.register_data)
        login = self.client.post(reverse('accounts:login'), {
            'email': 'student@colohouse.com',
            'password': 'StrongPass123!',
        })
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + login.data['access'])
        response = self.client.get(reverse('accounts:me'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'student@colohouse.com')
