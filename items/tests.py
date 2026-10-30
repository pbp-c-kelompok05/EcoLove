import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from items.models import Item
from items.forms import ItemForm

class ItemModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.item = Item.objects.create(
            user=self.user,
            name='Vintage Jacket',
            price=150,
            description='A nice secondhand jacket',
            category='CLOTHES'  # Sesuai dengan models.py
        )

    def test_item_creation(self):
        self.assertEqual(self.item.name, 'Vintage Jacket')
        self.assertEqual(self.item.price, 150)
        self.assertEqual(self.item.user, self.user)
        self.assertEqual(self.item.category, 'CLOTHES')


class ItemFormTest(TestCase):
    def test_valid_item_form(self):
        tiny_gif = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        
        image = SimpleUploadedFile(
            name='test_image.gif',
            content=tiny_gif,
            content_type='image/gif'
        )
        form_data = {
            'name': 'Reusable Water Bottle',
            'price': 15,
            'description': 'Eco-friendly stainless steel bottle',
            'category': 'OTHERS'
        }
        form = ItemForm(data=form_data, files={'image': image})
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_item_form_missing_required(self):
        form_data = {'name': '', 'price': 10}
        form = ItemForm(data=form_data)
        self.assertFalse(form.is_valid())


class ItemViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='seller', password='password123')
        self.user2 = User.objects.create_user(username='buyer', password='password123')

        self.item = Item.objects.create(
            user=self.user1,
            name='Eco Bag',
            price=25,
            description='Organic cotton bag',
            category='OTHERS'
        )

    def test_show_marketplace_view(self):
        response = self.client.get(reverse('items:show_marketplace'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'marketplace.html')

    def test_my_marketplace_unauthenticated_redirect(self):
        response = self.client.get(reverse('items:my_marketplace'))
        self.assertEqual(response.status_code, 302)

    def test_my_marketplace_authenticated(self):
        self.client.login(username='seller', password='password123')
        response = self.client.get(reverse('items:my_marketplace'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_marketplace.html')

    def test_item_detail_view(self):
        response = self.client.get(reverse('items:item_detail', args=[self.item.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'item_detail.html')

    def test_add_item_view_post(self):
        self.client.login(username='seller', password='password123')
        response = self.client.post(reverse('items:add_item'), {
            'name': 'Thrifted Shoes',
            'price': 45,
            'description': 'Size 42 good condition',
            'category': 'CLOTHES'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Item.objects.filter(name='Thrifted Shoes').exists())

    def test_edit_item_view_post(self):
        self.client.login(username='seller', password='password123')
        response = self.client.post(reverse('items:edit_item', args=[self.item.id]), {
            'name': 'Updated Eco Bag',
            'price': 30,
            'description': 'Updated description',
            'category': 'OTHERS'
        })
        self.assertEqual(response.status_code, 302)
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, 'Updated Eco Bag')

    def test_delete_item_standard(self):
        self.client.login(username='seller', password='password123')
        response = self.client.post(reverse('items:delete_item', args=[self.item.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Item.objects.filter(id=self.item.id).exists())

    def test_delete_item_ajax_success(self):
        self.client.login(username='seller', password='password123')
        response = self.client.post(
            reverse('items:delete_item_ajax', args=[self.item.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['message'], 'Item deleted successfully!')
        self.assertFalse(Item.objects.filter(id=self.item.id).exists())

    def test_delete_item_ajax_unauthorized(self):
        self.client.login(username='buyer', password='password123')
        response = self.client.post(
            reverse('items:delete_item_ajax', args=[self.item.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 403)

    def test_like_item_ajax(self):
        self.client.login(username='buyer', password='password123')
        response = self.client.post(
            reverse('items:like_item_ajax', args=[self.item.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['is_liked'])
        self.assertEqual(data['like_count'], 1)

    def test_get_items_json(self):
        response = self.client.get(reverse('items:get_items_json'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['fields']['name'], 'Eco Bag')