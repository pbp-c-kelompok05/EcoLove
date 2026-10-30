import hashlib, hmac, json, requests

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import requires_csrf_token, csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Exists, OuterRef
from django.conf import settings

from .models import Item, Order

# Payments
def _apply_status(order, data):
    ts = data.get('transaction_status')
    fraud = data.get('fraud_status')
    if ts == 'settlement' or (ts == 'capture' and fraud == 'accept'):
        order.status = 'PAID'
    elif ts in ('cancel', 'deny'):
        order.status = 'FAILED'
    elif ts == 'expire':
        order.status = 'EXPIRED'
    else:
        order.status = 'PENDING'
    order.save()

@login_required(login_url='/login/')
@require_POST
def create_payment(request, id):
    item = get_object_or_404(Item, id=id)
    if item.user == request.user:
        return JsonResponse({"message": "You cannot buy your own item."}, status=403)

    existing = Order.objects.filter(
        item=item, buyer=request.user, status='PENDING'
    ).exclude(snap_token='').first()
    if existing:
        return JsonResponse({"token": existing.snap_token, "order_id": str(existing.id)})

    order = Order.objects.create(item=item, buyer=request.user, amount=item.price)

    payload = {
        "transaction_details": {"order_id": str(order.id), "gross_amount": item.price},
        "item_details": [{
            "id": str(item.id), "price": item.price,
            "quantity": 1, "name": item.name[:50],
        }],
        "customer_details": {"first_name": request.user.username},
    }
    resp = requests.post(
        settings.MIDTRANS_SNAP_URL, json=payload,
        auth=(settings.MIDTRANS_SERVER_KEY, ''),  # HTTP Basic: server key as username, empty password
        timeout=15,
    )
    if resp.status_code not in (200, 201):
        order.status = 'FAILED'
        order.save()
        return JsonResponse({"message": "Failed to create payment."}, status=502)

    order.snap_token = resp.json()['token']
    order.save()
    return JsonResponse({"token": order.snap_token, "order_id": str(order.id)})

@csrf_exempt
@require_POST
def midtrans_notification(request):
    data = json.loads(request.body)
    raw = data['order_id'] + data['status_code'] + data['gross_amount'] + settings.MIDTRANS_SERVER_KEY
    expected = hashlib.sha512(raw.encode()).hexdigest()
    if not hmac.compare_digest(expected, data.get('signature_key', '')):
        return HttpResponse(status=403)

    order = get_object_or_404(Order, id=data['order_id'])
    _apply_status(order, data)
    return HttpResponse(status=200)

@login_required(login_url='/login/')
def sync_payment_status(request, id):
    """Fallback: ask Midtrans directly. Useful on localhost where webhooks can't reach you."""
    order = get_object_or_404(Order, id=id, buyer=request.user)
    resp = requests.get(
        settings.MIDTRANS_STATUS_URL.format(order_id=order.id),
        auth=(settings.MIDTRANS_SERVER_KEY, ''), timeout=15,
    )
    if resp.status_code == 200:
        _apply_status(order, resp.json())
    return JsonResponse({"status": order.status})

@login_required(login_url='/login/')
def my_purchases(request):
    orders = Order.objects.filter(buyer=request.user, status='PAID').select_related('item').order_by('-created_at')
    return render(request, 'my_purchases.html', {'orders': orders})
