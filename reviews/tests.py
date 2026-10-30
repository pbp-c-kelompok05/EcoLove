from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Review

from items.models import Item

class ReviewsTest(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(username="superuser")

        self.owner = User.objects.create(username="owner")
        self.item = Item.objects.create(
            user=self.owner,
            name="test",
            price=123,
            description="test desc",
            category="freelance",
        )

        self.reviewer = User.objects.create(username="reviewer")
        self.review = Review.objects.create(
            user=self.reviewer,
            text="test rev",
            item=self.item,
            rating=1
        )

        self.buyer = User.objects.create(username="buyer")

    def test_review_model(self):
        self.assertTrue(self.review.user, self.reviewer)
        self.assertEqual(self.review.text, "test rev")
        self.assertTrue(self.review.item, self.item)
        self.assertTrue(self.review.rating, 1)

    def test_like_review_valid(self):
        self.client.force_login(user=self.buyer)
        response = self.client.post(
            reverse("reviews:like", kwargs={'id':self.review.id}),
        )

        self.assertEqual(response.status_code, 201)

    def test_like_review_not_authenticated(self):
        response = self.client.post(
            reverse("reviews:like", kwargs={'id':self.review.id}),
        )

        self.assertEqual(response.status_code, 302)

    def test_like_review_not_found(self):
        self.client.force_login(user=self.buyer)
        response = self.client.post(
            reverse("reviews:like", kwargs={'id':'00000000-0000-0000-0000-000000000000'}),
        )

        self.assertEqual(response.status_code, 404)

    def test_dislike_review_valid(self):
        self.client.force_login(user=self.buyer)
        response = self.client.post(
            reverse("reviews:dislike", kwargs={'id':self.review.id}),
        )

        self.assertEqual(response.status_code, 201)

    def test_dislike_review_not_authenticated(self):
        response = self.client.post(
            reverse("reviews:dislike", kwargs={'id':self.review.id}),
        )

        self.assertEqual(response.status_code, 302)

    def test_dislike_review_not_found(self):
        self.client.force_login(user=self.buyer)
        response = self.client.post(
            reverse("reviews:dislike", kwargs={'id':'00000000-0000-0000-0000-000000000000'}),
        )

        self.assertEqual(response.status_code, 404)
    

    def test_add_review_valid(self):
        self.client.force_login(user=self.buyer)
        response = self.client.post(
            reverse("reviews:add_review", kwargs={'id':self.item.id}),
            {'text': 'test rev', 'rating':1}
        )

        self.assertEqual(response.status_code, 201)

    def test_add_review_form_invalid(self):
        self.client.force_login(user=self.buyer)
        response = self.client.post(
            reverse("reviews:add_review", kwargs={'id':self.item.id}),
            {'text': 'test rev', 'rating':0}
        )

        self.assertEqual(response.status_code, 400)

    def test_add_review_duplicate(self):
        self.client.force_login(user=self.reviewer)
        response = self.client.post(
            reverse("reviews:add_review", kwargs={'id':self.item.id}),
            {'text': 'test rev', 'rating':2}
        )

        self.assertEqual(response.status_code, 403)

    def test_add_review_not_authenticated(self):
        response = self.client.post(
            reverse("reviews:add_review", kwargs={'id':self.item.id}),
            {'text': 'test rev', 'rating':2}
        )

        self.assertEqual(response.status_code, 302)

    def test_add_review_item_not_found(self):
        self.client.force_login(user=self.buyer)
        response = self.client.post(
            reverse("reviews:add_review", kwargs={'id':'00000000-0000-0000-0000-000000000000'}),
            {'text': 'test rev', 'rating':1}
        )

        self.assertEqual(response.status_code, 404)

    def test_edit_review_valid(self):
        self.client.force_login(user=self.reviewer)
        response = self.client.post(
            reverse("reviews:edit_review", kwargs={'id':self.review.id}),
            {'text': 'test rev', 'rating':1}
        )

        self.assertEqual(response.status_code, 201)

    def test_edit_review_valid_superuser(self):
        self.client.force_login(user=self.superuser)
        response = self.client.post(
            reverse("reviews:edit_review", kwargs={'id':self.review.id}),
            {'text': 'test rev', 'rating':1}
        )

        self.assertEqual(response.status_code, 201)

    def test_edit_review_form_invalid(self):
        self.client.force_login(user=self.reviewer)
        response = self.client.post(
            reverse("reviews:edit_review", kwargs={'id':self.review.id}),
            {'text': 'test rev', 'rating':0}
        )

        self.assertEqual(response.status_code, 400)

    def test_edit_review_unauthorized_edit(self):
        self.client.force_login(user=self.buyer)
        response = self.client.post(
            reverse("reviews:edit_review", kwargs={'id':self.review.id}),
            {'text': 'test rev', 'rating':1}
        )

        self.assertEqual(response.status_code, 403)

    def test_edit_review_not_found(self):
        self.client.force_login(user=self.buyer)
        response = self.client.post(
            reverse("reviews:edit_review", kwargs={'id':'00000000-0000-0000-0000-000000000000'}),
            {'text': 'test rev', 'rating':1}
        )

        self.assertEqual(response.status_code, 404)

    def test_edit_review_not_authenticated(self):
        response = self.client.post(
            reverse("reviews:edit_review", kwargs={'id':self.review.id}),
            {'text': 'test rev', 'rating':2}
        )

        self.assertEqual(response.status_code, 302)

    def test_delete_review_valid(self):
        self.client.force_login(user=self.reviewer)
        response = self.client.post(
            reverse("reviews:delete", kwargs={'id':self.review.id}),
            {'text': 'test rev', 'rating':1}
        )

        self.assertEqual(response.status_code, 201)
    
    def test_delete_review_valid_superuser(self):
        self.client.force_login(user=self.superuser)
        response = self.client.post(
            reverse("reviews:delete", kwargs={'id':self.review.id}),
            {'text': 'test rev', 'rating':1}
        )

        self.assertEqual(response.status_code, 201)

    def test_delete_review_unauthorized_delete(self):
        self.client.force_login(user=self.buyer)
        response = self.client.post(
            reverse("reviews:delete", kwargs={'id':self.review.id}),
            {'text': 'test rev', 'rating':1}
        )

        self.assertEqual(response.status_code, 403)

    def test_delete_review_not_found(self):
        self.client.force_login(user=self.buyer)
        response = self.client.post(
            reverse("reviews:delete", kwargs={'id':'00000000-0000-0000-0000-000000000000'}),
            {'text': 'test rev', 'rating':1}
        )

        self.assertEqual(response.status_code, 404)

    def test_edit_review_not_authenticated(self):
        response = self.client.post(
            reverse("reviews:delete", kwargs={'id':self.review.id}),
            {'text': 'test rev', 'rating':2}
        )

        self.assertEqual(response.status_code, 302)