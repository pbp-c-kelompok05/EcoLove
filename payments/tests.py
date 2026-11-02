
import hashlib
import hmac
import json
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from items.models import Item
from payments.models import Order
from payments.views import _apply_status


@override_settings(
    MIDTRANS_SERVER_KEY="test-server-key",
    MIDTRANS_SNAP_URL="https://example.test/snap",
    MIDTRANS_STATUS_URL="https://example.test/status/{order_id}",
    MIDTRANS_CANCEL_URL="https://example.test/cancel/{order_id}",
)
class PaymentsTests(TestCase):

    def setUp(self):
        self.seller = User.objects.create_user(
            username="seller",
            password="test-password-123",
        )
        self.buyer = User.objects.create_user(
            username="buyer",
            password="test-password-123",
        )

        self.item = Item.objects.create(
            user=self.seller,
            name="Test item",
            price=100000,
        )

        self.client.force_login(self.buyer)

    def create_order(self, status="PENDING", snap_token=""):
        return Order.objects.create(
            item=self.item,
            buyer=self.buyer,
            amount=self.item.price,
            status=status,
            snap_token=snap_token,
        )

    # 1. Only POST requests can initiate payment
    def test_create_payment_requires_post(self):
        response = self.client.get(
            reverse(
                "payments:create_payment",
                kwargs={"id": self.item.id},
            )
        )
        self.assertEqual(response.status_code, 405)

    # 2. A seller cannot purchase their own item
    def test_cannot_buy_own_item(self):
        self.client.force_login(self.seller)

        response = self.client.post(
            reverse(
                "payments:create_payment",
                kwargs={"id": self.item.id},
            )
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Order.objects.exists())

    # 3. A successful Midtrans response creates a pending order
    @patch("payments.views.requests.post")
    def test_create_payment_success(self, mock_post):
        mock_post.return_value = Mock(
            status_code=201,
            json=Mock(return_value={"token": "test-snap-token"}),
        )

        response = self.client.post(
            reverse(
                "payments:create_payment",
                kwargs={"id": self.item.id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["token"], "test-snap-token")

        order = Order.objects.get()
        self.assertEqual(order.buyer, self.buyer)
        self.assertEqual(order.item, self.item)
        self.assertEqual(order.amount, self.item.price)
        self.assertEqual(order.status, "PENDING")
        self.assertEqual(order.snap_token, "test-snap-token")

        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(
            payload["transaction_details"]["order_id"],
            str(order.id),
        )
        self.assertEqual(
            payload["transaction_details"]["gross_amount"],
            self.item.price,
        )

    # 4. Reuse an existing pending order instead of creating another midtrans order
    @patch("payments.views.requests.post")
    def test_reuses_existing_pending_payment(self, mock_post):
        order = self.create_order(
            status="PENDING",
            snap_token="existing-snap-token",
        )

        response = self.client.post(
            reverse(
                "payments:create_payment",
                kwargs={"id": self.item.id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["token"],
            "existing-snap-token",
        )
        self.assertEqual(response.json()["order_id"], str(order.id))
        self.assertEqual(Order.objects.count(), 1)
        mock_post.assert_not_called()

    # 5. Handle a failed response from Midtrans
    @patch("payments.views.requests.post")
    def test_midtrans_failure_marks_order_failed(self, mock_post):
        mock_post.return_value = Mock(status_code=500)

        response = self.client.post(
            reverse(
                "payments:create_payment",
                kwargs={"id": self.item.id},
            )
        )

        self.assertEqual(response.status_code, 502)
        order = Order.objects.get()
        self.assertEqual(order.status, "FAILED")

    # 6. A valid Midtrans notification updates the order to PAID
    def test_valid_notification_marks_order_paid(self):
        order = self.create_order()
        status_code = "200"
        gross_amount = str(order.amount)

        raw_signature = (
            str(order.id)
            + status_code
            + gross_amount
            + "test-server-key"
        )
        signature = hashlib.sha512(
            raw_signature.encode()
        ).hexdigest()

        payload = {
            "order_id": str(order.id),
            "status_code": status_code,
            "gross_amount": gross_amount,
            "signature_key": signature,
            "transaction_status": "settlement",
        }

        response = self.client.post(
            reverse("payments:midtrans_notification"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, "PAID")

    # 7. Reject notifications with an invalid signature
    def test_invalid_notification_signature_is_rejected(self):
        order = self.create_order()

        payload = {
            "order_id": str(order.id),
            "status_code": "200",
            "gross_amount": str(order.amount),
            "signature_key": "invalid-signature",
            "transaction_status": "settlement",
        }

        response = self.client.post(
            reverse("payments:midtrans_notification"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        self.assertEqual(order.status, "PENDING")

    # 8. The status-mapping logic handles Midtrans outcomes
    def test_apply_status_maps_midtrans_statuses(self):
        cases = [
            ({"transaction_status": "settlement"}, "PAID"),
            (
                {
                    "transaction_status": "capture",
                    "fraud_status": "accept",
                },
                "PAID",
            ),
            ({"transaction_status": "cancel"}, "CANCELLED"),
            ({"transaction_status": "deny"}, "FAILED"),
            ({"transaction_status": "expire"}, "EXPIRED"),
            ({"transaction_status": "pending"}, "PENDING"),
        ]

        for data, expected_status in cases:
            with self.subTest(data=data):
                order = self.create_order()
                _apply_status(order, data)

                order.refresh_from_db()
                self.assertEqual(order.status, expected_status)

    # 9. A buyer only sees their own paid purchases
    def test_my_purchases_shows_only_paid_orders(self):
        paid_order = self.create_order(status="PAID")
        self.create_order(status="PENDING")

        other_buyer = User.objects.create_user(
            username="another-buyer",
            password="test-password-123",
        )
        Order.objects.create(
            item=self.item,
            buyer=other_buyer,
            amount=self.item.price,
            status="PAID",
        )

        response = self.client.get(
            reverse("payments:my_purchases")
        )

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(
            response.context["orders"],
            [paid_order],
        )

    # 10. Buyers cannot sync another user's payment status
    def test_cannot_sync_another_users_order(self):
        other_buyer = User.objects.create_user(
            username="another-buyer",
            password="test-password-123",
        )
        order = Order.objects.create(
            item=self.item,
            buyer=other_buyer,
            amount=self.item.price,
            status="PENDING",
        )

        response = self.client.get(
            reverse(
                "payments:sync_payment_status",
                kwargs={"id": order.id},
            )
        )

        self.assertEqual(response.status_code, 404)
