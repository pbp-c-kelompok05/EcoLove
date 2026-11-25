from datetime import timedelta
import uuid

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from events.models import Education, Event, EventComment


class EventAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com"
        )
        self.visitor = User.objects.create_user(
            username="visitor", password="test-password"
        )
        self.staff = User.objects.create_user(
            username="staff", password="test-password", is_staff=True
        )
        self.now = timezone.now()
        self.event = Event.objects.create(
            title="Repair Pakaian",
            category="reuse",
            description="Belajar menjahit bersama komunitas.",
            starts_at=self.now + timedelta(days=2),
            ends_at=self.now + timedelta(days=2, hours=2),
            location="Depok",
            is_online=False,
            organizer_contact="PRIVATE-CONTACT",
            meeting_link="https://example.com/private-meet",
            creator=self.owner,
        )
        self.list_url = reverse("api:event-list")
        self.detail_url = reverse("api:event-detail", args=[self.event.id])
        self.participate_url = reverse("api:event-participate", args=[self.event.id])
        self.payload = {
            "title": "Workshop Kompos",
            "category": "waste",
            "description": "Mengolah sampah organik rumah tangga.",
            "starts_at": (self.now + timedelta(days=5)).isoformat(),
            "ends_at": (self.now + timedelta(days=5, hours=3)).isoformat(),
            "location": "Jakarta",
            "is_online": True,
            "organizer_contact": "kompos@example.com",
            "meeting_link": "https://example.com/kompos",
        }

    def test_public_list_and_detail(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], str(self.event.id))
        self.assertFalse(response.data[0]["is_registered"])
        self.assertNotIn("fields", response.data[0])
        self.assertNotIn("organizer_contact", response.data[0])
        self.assertNotIn("meeting_link", response.data[0])

        detail = self.client.get(self.detail_url)
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertNotIn("organizer_contact", detail.data)
        self.assertNotIn("meeting_link", detail.data)

    def test_authenticated_user_sees_private_event_fields(self):
        self.client.force_authenticate(user=self.visitor)
        detail = self.client.get(self.detail_url)
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["organizer_contact"], "PRIVATE-CONTACT")
        self.assertEqual(detail.data["meeting_link"], "https://example.com/private-meet")

    def test_search_filter_and_empty_results(self):
        for params in ({"q": "REPAIR"}, {"title": "REPAIR"}, {"category": "reuse", "status": "upcoming"}):
            response = self.client.get(self.list_url, params)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), 1)

        empty = self.client.get(self.list_url, {"q": "not-found"})
        self.assertEqual(empty.status_code, status.HTTP_200_OK)
        self.assertEqual(empty.data, [])

    def test_missing_event(self):
        url = reverse("api:event-detail", args=[uuid.uuid4()])
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_guest_visitor_and_staff_cannot_write(self):
        for user in (None, self.visitor, self.staff):
            self.client.force_authenticate(user=user)
            self.assertEqual(
                self.client.post(self.list_url, self.payload, format="json").status_code,
                status.HTTP_403_FORBIDDEN,
            )
            self.assertEqual(
                self.client.patch(self.detail_url, {"title": "Changed"}, format="json").status_code,
                status.HTTP_403_FORBIDDEN,
            )
            self.assertEqual(
                self.client.put(self.detail_url, self.payload, format="json").status_code,
                status.HTTP_403_FORBIDDEN,
            )
            self.assertEqual(
                self.client.delete(self.detail_url).status_code,
                status.HTTP_403_FORBIDDEN,
            )
        self.assertEqual(Event.objects.count(), 1)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Repair Pakaian")

    def test_owner_can_create_and_creator_not_spoofable(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.list_url,
            {**self.payload, "creator": self.visitor.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Event.objects.get(pk=response.data["id"])
        self.assertEqual(created.creator, self.owner)
        self.assertEqual(response.data["creator_name"], self.owner.username)

    def test_validation(self):
        self.client.force_authenticate(user=self.owner)
        invalid_cases = [
            ({"title": "   "}, "title"),
            ({"title": '<img src="x" onerror="alert(1)">'}, "title"),
            ({"description": "<b></b>"}, "description"),
            ({"location": "   "}, "location"),
            ({"meeting_link": "javascript:alert(1)"}, "meeting_link"),
            (
                {
                    "starts_at": (self.now + timedelta(days=5)).isoformat(),
                    "ends_at": (self.now + timedelta(days=4)).isoformat(),
                },
                "ends_at",
            ),
        ]
        for changes, field in invalid_cases:
            response = self.client.post(
                self.list_url, {**self.payload, **changes}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)
        self.assertEqual(Event.objects.count(), 1)

    def test_patch_put_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        patch_resp = self.client.patch(
            self.detail_url, {"title": "Changed Event"}, format="json"
        )
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Changed Event")
        self.assertEqual(self.event.description, "Belajar menjahit bersama komunitas.")

        bad_put = self.client.put(self.detail_url, {"title": "Incomplete"}, format="json")
        self.assertEqual(bad_put.status_code, status.HTTP_400_BAD_REQUEST)

        good_put = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(good_put.status_code, status.HTTP_200_OK)

        delete_resp = self.client.delete(self.detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(delete_resp.content, b"")
        self.assertFalse(Event.objects.filter(pk=self.event.id).exists())

    def test_participate_requires_login_and_toggles(self):
        self.assertEqual(
            self.client.post(self.participate_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.client.force_authenticate(user=self.visitor)
        resp1 = self.client.post(self.participate_url)
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)
        self.assertTrue(resp1.data["is_registered"])
        self.assertEqual(resp1.data["registration_count"], 1)

        resp2 = self.client.post(self.participate_url)
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertFalse(resp2.data["is_registered"])
        self.assertEqual(resp2.data["registration_count"], 0)

        self.event.starts_at = self.now - timedelta(hours=2)
        self.event.ends_at = self.now - timedelta(hours=1)
        self.event.save()
        closed_resp = self.client.post(self.participate_url)
        self.assertEqual(closed_resp.status_code, status.HTTP_409_CONFLICT)

    def test_computed_fields_are_read_only(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.list_url,
            {
                **self.payload,
                "registration_count": 99,
                "is_registered": True,
                "creator_name": "forged",
                "status_label": "Selesai",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["registration_count"], 0)
        self.assertFalse(response.data["is_registered"])
        self.assertEqual(response.data["creator_name"], self.owner.username)
        self.assertEqual(response.data["status_label"], "Mendatang")

    def test_wrong_method(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(
            self.client.delete(self.list_url).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )
        self.assertEqual(
            self.client.get(self.participate_url).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="owner", password="test-password"))
        response = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Event.objects.count(), 1)

    def test_session_write_with_csrf_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="owner", password="test-password"))
        page = client.get(self.list_url, HTTP_ACCEPT="text/html")
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        token = client.cookies["csrftoken"].value
        response = client.post(
            self.list_url,
            self.payload,
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class EducationAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com"
        )
        self.visitor = User.objects.create_user(
            username="visitor", password="test-password"
        )
        self.staff = User.objects.create_user(
            username="staff", password="test-password", is_staff=True
        )
        self.article = Education.objects.create(
            title="Panduan Kompos",
            category="waste",
            summary="Mengolah sisa dapur menjadi pupuk.",
            body="Pisahkan sampah organik dari plastik lalu diamkan di komposter.",
            author=self.owner,
        )
        self.list_url = reverse("api:education-list")
        self.detail_url = reverse("api:education-detail", args=[self.article.id])
        self.payload = {
            "title": "Membawa Tas Belanja",
            "category": "lifestyle",
            "summary": "Kurangi kantong plastik sekali pakai.",
            "body": "Selalu siapkan tas kain di dalam tas harian.",
        }

    def test_public_list_and_detail(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], str(self.article.id))
        self.assertEqual(response.data[0]["author_name"], self.owner.username)
        self.assertNotIn("fields", response.data[0])
        self.assertEqual(
            self.client.get(self.detail_url).status_code, status.HTTP_200_OK
        )

    def test_search_filter_and_empty_results(self):
        for params in ({"q": "kompos"}, {"title": "kompos"}, {"category": "waste"}):
            response = self.client.get(self.list_url, params)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), 1)

        empty = self.client.get(self.list_url, {"q": "tidak-ada"})
        self.assertEqual(empty.status_code, status.HTTP_200_OK)
        self.assertEqual(empty.data, [])

    def test_missing_education(self):
        url = reverse("api:education-detail", args=[uuid.uuid4()])
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_guest_visitor_and_staff_cannot_write(self):
        for user in (None, self.visitor, self.staff):
            self.client.force_authenticate(user=user)
            self.assertEqual(
                self.client.post(self.list_url, self.payload, format="json").status_code,
                status.HTTP_403_FORBIDDEN,
            )
            self.assertEqual(
                self.client.patch(self.detail_url, {"title": "Changed"}, format="json").status_code,
                status.HTTP_403_FORBIDDEN,
            )
            self.assertEqual(
                self.client.put(self.detail_url, self.payload, format="json").status_code,
                status.HTTP_403_FORBIDDEN,
            )
            self.assertEqual(
                self.client.delete(self.detail_url).status_code,
                status.HTTP_403_FORBIDDEN,
            )
        self.assertEqual(Education.objects.count(), 1)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "Panduan Kompos")

    def test_owner_can_create_and_author_not_spoofable(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.list_url,
            {**self.payload, "author": self.visitor.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Education.objects.get(pk=response.data["id"])
        self.assertEqual(created.author, self.owner)
        self.assertEqual(response.data["author_name"], self.owner.username)

    def test_validation(self):
        self.client.force_authenticate(user=self.owner)
        for changes, field in (
            ({"title": "   "}, "title"),
            ({"title": '<img src="x" onerror="alert(1)">'}, "title"),
            ({"summary": "   "}, "summary"),
            ({"body": "<div></div>"}, "body"),
            ({"category": "invalid-category"}, "category"),
        ):
            response = self.client.post(
                self.list_url, {**self.payload, **changes}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)
        self.assertEqual(Education.objects.count(), 1)

    def test_patch_put_and_delete(self):
        self.client.force_authenticate(user=self.owner)
        patch_resp = self.client.patch(
            self.detail_url, {"title": "Kompos Lanjutan"}, format="json"
        )
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "Kompos Lanjutan")
        self.assertEqual(self.article.summary, "Mengolah sisa dapur menjadi pupuk.")

        bad_put = self.client.put(self.detail_url, {"title": "Incomplete"}, format="json")
        self.assertEqual(bad_put.status_code, status.HTTP_400_BAD_REQUEST)

        good_put = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(good_put.status_code, status.HTTP_200_OK)

        delete_resp = self.client.delete(self.detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(delete_resp.content, b"")
        self.assertFalse(Education.objects.filter(pk=self.article.id).exists())

    def test_computed_fields_are_read_only(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            self.list_url,
            {**self.payload, "author_name": "forged"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author_name"], self.owner.username)

    def test_wrong_method(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(
            self.client.delete(self.list_url).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_session_write_without_csrf_is_rejected(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="owner", password="test-password"))
        response = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Education.objects.count(), 1)

    def test_session_write_with_csrf_succeeds(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="owner", password="test-password"))
        page = client.get(self.list_url, HTTP_ACCEPT="text/html")
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        token = client.cookies["csrftoken"].value
        response = client.post(
            self.list_url,
            self.payload,
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class EventCommentAPITest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            username="owner", password="test-password", email="owner@example.com"
        )
        self.visitor = User.objects.create_user(
            username="visitor", password="test-password"
        )
        self.other = User.objects.create_user(
            username="other", password="test-password"
        )
        self.now = timezone.now()
        self.event = Event.objects.create(
            title="Repair Pakaian",
            category="reuse",
            description="Belajar menjahit bersama komunitas.",
            starts_at=self.now + timedelta(days=2),
            ends_at=self.now + timedelta(days=2, hours=2),
            location="Depok",
            creator=self.owner,
        )
        self.comment = EventComment.objects.create(
            event=self.event,
            user=self.visitor,
            body="Seru banget acaranya!",
        )
        self.list_url = reverse("api:event-comment-list", args=[self.event.id])
        self.detail_url = reverse("api:event-comment-detail", args=[self.comment.id])

    def test_public_can_list_comments(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["username"], "visitor")
        self.assertFalse(response.data[0]["can_delete"])

        missing_url = reverse("api:event-comment-list", args=[uuid.uuid4()])
        self.assertEqual(self.client.get(missing_url).status_code, status.HTTP_404_NOT_FOUND)

    def test_guest_cannot_create_or_delete_comment(self):
        self.assertEqual(
            self.client.post(self.list_url, {"body": "Halo"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.delete(self.detail_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_authenticated_user_can_post_and_validate_comment(self):
        self.client.force_authenticate(user=self.visitor)
        response = self.client.post(
            self.list_url,
            {"body": "Ikut daftar ya!", "user": self.owner.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "visitor")
        self.assertTrue(response.data["can_delete"])

        invalid = self.client.post(
            self.list_url,
            {"body": "<b>   </b>"},
            format="json",
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("body", invalid.data)

    def test_delete_comment_permissions(self):
        self.client.force_authenticate(user=self.other)
        list_resp = self.client.get(self.list_url)
        self.assertFalse(list_resp.data[0]["can_delete"])
        self.assertEqual(
            self.client.delete(self.detail_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.client.force_authenticate(user=self.visitor)
        self.assertEqual(
            self.client.delete(self.detail_url).status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(EventComment.objects.filter(pk=self.comment.id).exists())

    def test_superuser_can_delete_any_comment(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(
            self.client.delete(self.detail_url).status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(EventComment.objects.filter(pk=self.comment.id).exists())
