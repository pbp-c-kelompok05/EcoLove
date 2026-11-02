import hashlib, hmac, json, requests

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import requires_csrf_token, csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Exists, OuterRef
from django.conf import settings

from .models import Item
from .forms import ItemForm
from payments.models import Order

#marketplace umum (karen)
def show_marketplace(request):
    all_items = Item.objects.all().order_by('-id')
    return render(request, 'marketplace.html', {'items': all_items})

#marketplace pribadi milik user (karen)
@login_required(login_url='/login/')
def my_marketplace(request):
    user_items = Item.objects.filter(user=request.user).annotate(
        sold=Exists(Order.objects.filter(item=OuterRef('pk'), status='PAID'))
    ).order_by('-id')
    return render(request, 'my_marketplace.html', {'user_items': user_items})

def item_detail(request, id):
    item = get_object_or_404(Item, id=id)
    pending_order = None
    if request.user.is_authenticated:
        pending_order = Order.objects.filter(
            item=item, buyer=request.user, status='PENDING'
        ).first()
    return render(request, 'item_detail.html', {
        'item': item,
        'pending_order': pending_order,
        'midtrans_client_key': settings.MIDTRANS_CLIENT_KEY,
        'midtrans_snap_js': settings.MIDTRANS_SNAP_JS,
    })

@login_required(login_url='/login/')
def like_item(request, id):
    item = get_object_or_404(Item, id=id)
    
    if request.user in item.disliked_by.all():
        item.disliked_by.remove(request.user)
        
    if request.user in item.liked_by.all():
        item.liked_by.remove(request.user)
    else:
        item.liked_by.add(request.user)
        
    return redirect('items:show_marketplace')

@requires_csrf_token
@require_POST
def like_item_ajax(request, id):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"message": "Only logged-in users allowed to give likes."},
            status=403,
        )

    item = get_object_or_404(Item, id=id)

    if request.user == item.user:
        return JsonResponse(
            {"message": "Cannot give likes to owned items."},
            status=403,
        )
        
    if request.user in item.disliked_by.all():
        item.disliked_by.remove(request.user)
        
    liked_users = item.liked_by.all()
    is_liked = request.user in liked_users
    if is_liked:
        item.liked_by.remove(request.user)
        message = "Sucessfully removed like from item."
    else:
        item.liked_by.add(request.user)
        message = "Sucessfully gave like to item."

    liked_users = item.liked_by.all()
    is_liked = request.user in liked_users
    disliked_users = item.disliked_by.all()
    is_disliked = request.user in disliked_users

    return JsonResponse(
        {
            "message": message,
            "like_count": liked_users.count(),
            "is_liked": is_liked,
            "dislike_count": disliked_users.count(),
            "is_disliked": is_disliked,
        },
        status=201
    )

@login_required(login_url='/login/')
def dislike_item(request, id):
    item = get_object_or_404(Item, id=id)
    
    if request.user in item.liked_by.all():
        item.liked_by.remove(request.user)
        
    if request.user in item.disliked_by.all():
        item.disliked_by.remove(request.user)
    else:
        item.disliked_by.add(request.user)
        
    return redirect('items:show_marketplace')

@requires_csrf_token
@require_POST
def dislike_item_ajax(request, id):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"message": "Only logged-in users allowed to give dislikes."},
            status=403,
        )

    item = get_object_or_404(Item, id=id)

    if request.user == item.user:
        return JsonResponse(
            {"message": "Cannot give dislikes to owned items."},
            status=403,
        )
        
    if request.user in item.liked_by.all():
        item.liked_by.remove(request.user)
        
    disliked_users = item.disliked_by.all()
    is_disliked = request.user in disliked_users
    if is_disliked:
        item.disliked_by.remove(request.user)
        message = "Sucessfully removed dislike from item."
    else:
        item.disliked_by.add(request.user)
        message = "Sucessfully gave dislike to item."

    liked_users = item.liked_by.all()
    is_liked = request.user in liked_users
    disliked_users = item.disliked_by.all()
    is_disliked = request.user in disliked_users

    return JsonResponse(
        {
            "message": message,
            "like_count": liked_users.count(),
            "is_liked": is_liked,
            "dislike_count": disliked_users.count(),
            "is_disliked": is_disliked,
        },
        status=201
    )

#karen
@login_required(login_url='/login/')
def add_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES) 
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, f"Item succesfully added!")
            return redirect('items:my_marketplace')
    else:
        form = ItemForm()
        
    return render(request, 'item_form.html', {'form': form})

#karen
@login_required(login_url='/login/')
def edit_item(request, id):
    item = get_object_or_404(Item, id=id, user=request.user)
    
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"Item successfully updated!")
            return redirect('items:my_marketplace')
    else:
        form = ItemForm(instance=item)
    
    return render(request, 'item_form.html', {'form': form, 'item': item})

#karen
@login_required(login_url='/login/')
def delete_item(request, id):
    item = get_object_or_404(Item, id=id, user=request.user)
    
    if request.method == 'POST':
        item.delete()
        return redirect('items:my_marketplace')
  
    return redirect('items:show_marketplace')

@login_required(login_url='/login/')
@require_POST
def delete_item_ajax(request, id):
    item = Item.objects.filter(id=id).first()
    
    if not item:
        return JsonResponse({"message": "Item already deleted or not found."}, status=404)
        
    if item.user != request.user:
        return JsonResponse({"message": "You don't have permission to delete this item."}, status=403)

    item.delete()
    return JsonResponse({"message": "Item deleted successfully!"}, status=200)

@require_GET
def get_items_json(request):
    title_query = request.GET.get("title", "").strip()
    items = Item.objects.select_related("user").prefetch_related("liked_by", "disliked_by").exclude(order__status='PAID')

    if title_query:
        items = items.filter(name__icontains=title_query) # Diubah dari 'title' menjadi 'name'

    data = []
    for item in items:
        liked_users = item.liked_by.all()
        disliked_users = item.disliked_by.all()
        is_liked = request.user in liked_users \
            if request.user.is_authenticated and not request.user in disliked_users \
            else False
        is_disliked = request.user in disliked_users \
            if request.user.is_authenticated and not request.user in liked_users \
            else False

        data.append({
            "pk": str(item.id),
            "user_id": str(item.user.id),
            "fields": {
                "name": item.name,
                "price": item.price,
                "seller": item.user.username,
                "description": item.description,
                "category": item.category,
                "image": item.image.url if item.image else '',
                "like_count": liked_users.count(),
                "is_liked": is_liked,
                "dislike_count": disliked_users.count(),
                "is_disliked": is_disliked,
            }
        })

    return JsonResponse(data, safe=False)

