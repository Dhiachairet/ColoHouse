import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient
from .models import Campus, RoommateProfile, User

TEMP_MEDIA = tempfile.mkdtemp()


def make_image(name='avatar.png'):
    file = io.BytesIO()
    Image.new('RGB', (50, 50), 'blue').save(file, 'PNG')
    return SimpleUploadedFile(name, file.getvalue(), content_type='image/png')


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


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ProfileTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(
            'student@colohouse.com', 'StrongPass123!', first_name='Student', last_name='Test'
        )
        self.campus = Campus.objects.create(
            name='Main Campus', university='Test University', latitude=36.8, longitude=10.18
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        response = self.client.get(reverse('accounts:me'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['first_name'], 'Student')
        self.assertIsNone(response.data['campus'])
        self.assertIsNone(response.data['profile_picture'])

    def test_profile_requires_token(self):
        response = APIClient().get(reverse('accounts:me'))
        self.assertEqual(response.status_code, 401)

    def test_update_profile(self):
        response = self.client.patch(reverse('accounts:me'), {
            'phone': '+21612345678',
            'bio': 'Calm student, likes cooking.',
            'university': 'Test University',
            'field_of_study': 'Computer Science',
            'campus_id': self.campus.id,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['campus']['name'], 'Main Campus')
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, '+21612345678')
        self.assertEqual(self.user.field_of_study, 'Computer Science')
        self.assertEqual(self.user.campus, self.campus)

    def test_remove_campus(self):
        self.user.campus = self.campus
        self.user.save()
        response = self.client.patch(reverse('accounts:me'), {'campus_id': None}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['campus'])

    def test_unknown_campus_is_rejected(self):
        response = self.client.patch(reverse('accounts:me'), {'campus_id': 999}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_email_cannot_be_changed(self):
        self.client.patch(reverse('accounts:me'), {'email': 'other@colohouse.com'}, format='json')
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'student@colohouse.com')

    def test_invalid_phone_is_rejected(self):
        response = self.client.patch(reverse('accounts:me'), {'phone': 'abc'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('phone', response.data)

    def test_upload_profile_picture(self):
        response = self.client.patch(
            reverse('accounts:me'), {'profile_picture': make_image()}, format='multipart'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('/media/profile_pictures/', response.data['profile_picture'])

    def test_upload_non_image_is_rejected(self):
        file = SimpleUploadedFile('notes.txt', b'hello', content_type='text/plain')
        response = self.client.patch(
            reverse('accounts:me'), {'profile_picture': file}, format='multipart'
        )
        self.assertEqual(response.status_code, 400)

    def test_notification_settings(self):
        response = self.client.patch(reverse('accounts:me'), {
            'push_enabled': False,
            'notify_messages': False,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.push_enabled)
        self.assertFalse(self.user.notify_messages)
        self.assertTrue(self.user.notify_requests)

    def test_delete_account(self):
        RoommateProfile.objects.create(user=self.user)
        response = self.client.delete(reverse('accounts:me'))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(email='student@colohouse.com').exists())
        self.assertEqual(RoommateProfile.objects.count(), 0)


class PreferencesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'student@colohouse.com', 'StrongPass123!', first_name='Student', last_name='Test'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_creates_empty_preferences(self):
        response = self.client.get(reverse('accounts:preferences'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['budget'])
        self.assertFalse(response.data['looking_for_room'])
        self.assertTrue(RoommateProfile.objects.filter(user=self.user).exists())

    def test_update_preferences(self):
        response = self.client.patch(reverse('accounts:preferences'), {
            'budget': 450,
            'preferred_room_type': 'private',
            'move_in_date': '2026-11-01',
            'max_distance_to_campus': 3.5,
            'sleep_schedule': 'late',
            'noise_tolerance': 2,
            'cleanliness': 5,
            'smoker': False,
            'accepts_smokers': False,
            'looking_for_room': True,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        profile = RoommateProfile.objects.get(user=self.user)
        self.assertEqual(profile.budget, 450)
        self.assertEqual(profile.sleep_schedule, 'late')
        self.assertEqual(profile.cleanliness, 5)
        self.assertTrue(profile.looking_for_room)

    def test_cleanliness_out_of_range_is_rejected(self):
        response = self.client.patch(reverse('accounts:preferences'), {'cleanliness': 6}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_sleep_schedule_is_rejected(self):
        response = self.client.patch(
            reverse('accounts:preferences'), {'sleep_schedule': 'sometimes'}, format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_preferences_require_token(self):
        response = APIClient().get(reverse('accounts:preferences'))
        self.assertEqual(response.status_code, 401)


class CampusTests(TestCase):
    def test_campus_list_is_public(self):
        Campus.objects.create(name='Main Campus', university='Test University', latitude=36.8, longitude=10.18)
        response = APIClient().get(reverse('accounts:campuses'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Main Campus')
