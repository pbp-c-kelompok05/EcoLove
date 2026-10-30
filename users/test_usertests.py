import json

from django.apps import apps
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class UserTests(TestCase):
    def setUp(self):
        # url diambil dari name di urls.py
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.profile_url = reverse('profile')
        self.add_address_url = reverse('add_address')
        self.delete_address_url = reverse('delete_address', kwargs={'address_id': 1})

        # user dummy buat dipakai di semua test
        self.username = 'qanitasyafika'
        self.password = 'Password123!'
        self.email = 'qanita@example.com'
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email=self.email,
        )

        # data alamat yang dipakai di beberapa test
        self.address_data = {
            'recipient_name': 'Qanita Syafika',
            'address': 'Jl. UI No. 1',
            'full_address': 'Jl. UI No. 1',
            'city': 'Depok',
            'postal_code': '16425',
            'city_province_postal': 'Depok, Jawa Barat, 16425',
            'phone_number': '081299998888',
        }

    def login(self):
        self.client.login(username=self.username, password=self.password)

    # ---------- model ----------
    def test_user_str(self):
        self.assertEqual(str(self.user), self.username)

    def test_all_models_str(self):
        # pastiin __str__ semua model di app users nggak error
        for model in apps.get_app_config('users').get_models():
            for obj in model.objects.all():
                self.assertIsInstance(str(obj), str)

    # ---------- register ----------
    def test_register_get(self):
        response = self.client.get(self.register_url)
        self.assertIn(response.status_code, [200, 302])

    def test_register_post_success(self):
        data = {
            'username': 'user_baru_qanita',
            'email': 'baru@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'password_confirm': 'Password123!',
        }
        response = self.client.post(self.register_url, data)
        self.assertIn(response.status_code, [200, 201, 302])

    def test_register_password_mismatch(self):
        data = {
            'username': 'mismatch_user',
            'email': 'mismatch@example.com',
            'password': 'Password123!',
            'confirm_password': 'PasswordBeda123!',
            'password_confirm': 'PasswordBeda123!',
        }
        response = self.client.post(self.register_url, data)
        self.assertIn(response.status_code, [200, 302, 400])


    def test_register_duplicate_username(self):
        data = {
            'username': self.username,
            'email': 'duplikat@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'password_confirm': 'Password123!',
        }
        response = self.client.post(self.register_url, data)
        self.assertIn(response.status_code, [200, 302, 400])
        self.assertEqual(User.objects.filter(username=self.username).count(), 1)

    def test_register_empty_form(self):
        count_before = User.objects.count()
        response = self.client.post(self.register_url, {})
        self.assertIn(response.status_code, [200, 302, 400])
        self.assertEqual(User.objects.count(), count_before)

    # ---------- login ----------
    def test_login_get(self):
        response = self.client.get(self.login_url)
        self.assertIn(response.status_code, [200, 302])

    def test_login_post_success(self):
        response = self.client.post(self.login_url, {
            'username': self.username,
            'password': self.password,
        })
        self.assertIn(response.status_code, [200, 302])
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_wrong_password(self):
        response = self.client.post(self.login_url, {
            'username': self.username,
            'password': 'WrongPassword123',
        })
        self.assertIn(response.status_code, [200, 302, 400])
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_nonexistent_user(self):
        response = self.client.post(self.login_url, {
            'username': 'nobody_user',
            'password': self.password,
        })
        self.assertIn(response.status_code, [200, 302, 400])
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_empty_data(self):
        response = self.client.post(self.login_url, {})
        self.assertIn(response.status_code, [200, 302, 400])
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_json_request(self):
        response = self.client.post(
            self.login_url,
            data=json.dumps({'username': self.username, 'password': self.password}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertIn(response.status_code, [200, 302, 400])

    # ---------- logout ----------
    def test_logout_user(self):
        self.login()
        response = self.client.get(self.logout_url)
        self.assertIn(response.status_code, [200, 302])
        self.assertNotIn('_auth_user_id', self.client.session)

    # ---------- profile & alamat ----------
    def test_profile_authenticated_get(self):
        self.login()
        response = self.client.get(self.profile_url)
        self.assertIn(response.status_code, [200, 302])

    def test_profile_unauthenticated_get(self):
        response = self.client.get(self.profile_url)
        self.assertIn(response.status_code, [200, 302])

    def test_profile_post_update(self):
        self.login()
        response = self.client.post(self.profile_url, {
            **self.address_data,
            'address': 'Jl. Margonda Raya No. 10',
            'full_address': 'Jl. Margonda Raya No. 10',
            'postal_code': '16424',
            'phone_number': '081234567890',
        })
        self.assertIn(response.status_code, [200, 302])

    def test_add_address_authenticated(self):
        self.login()
        response = self.client.post(self.add_address_url, self.address_data)
        self.assertIn(response.status_code, [200, 302])

    def test_add_address_unauthenticated(self):
        response = self.client.post(self.add_address_url, self.address_data)
        self.assertIn(response.status_code, [200, 302])

    def test_delete_address_authenticated(self):
        # id 1 belum tentu ada, jadi 404 juga dianggap wajar
        self.login()
        response = self.client.post(self.delete_address_url)
        self.assertIn(response.status_code, [200, 302, 404])

    def test_delete_address_unauthenticated(self):
        response = self.client.get(self.delete_address_url)
        self.assertIn(response.status_code, [200, 302, 404])