from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import render, get_object_or_404, redirect

from .models import Item
from .forms import ItemForm

def show_marketplace(request):
    items = Item.objects.all()
    return render(request, 'marketplace.html', {'items': items})

def item_detail(request, id):
    item = get_object_or_404(Item, id=id)
    return render(request, 'item_detail.html', {'item': item})

@login_required(login_url='/login/')
def like_item(request, id):
    item = get_object_or_404(Item, id=id)
    
    # If the user previously disliked it, remove the dislike
    if request.user in item.dislikes.all():
        item.dislikes.remove(request.user)
        
    # Toggle like
    if request.user in item.likes.all():
        item.likes.remove(request.user)
    else:
        item.likes.add(request.user)
        
    return redirect('items:show_marketplace')

@login_required(login_url='/login/')
def dislike_item(request, id):
    item = get_object_or_404(Item, id=id)
    
    # If the user previously liked it, remove the like
    if request.user in item.likes.all():
        item.likes.remove(request.user)
        
    # Toggle dislike
    if request.user in item.dislikes.all():
        item.dislikes.remove(request.user)
    else:
        item.dislikes.add(request.user)
        
    return redirect('items:show_marketplace')

@login_required(login_url='/login/')
def add_item(request):
    if request.method == 'POST':
        # request.FILES is required for image uploads
        form = ItemForm(request.POST, request.FILES) 
        if form.is_valid():
            form.save()
            return redirect('items:show_marketplace')
    else:
        form = ItemForm()
        
    return render(request, 'add_item.html', {'form': form})

@require_GET
def get_items_json(request):
    title_query = request.GET.get("title", "").strip()
    items = Item.objects.prefetch_related("likes", "dislikes").all()

    if title_query:
        items = items.filter(title__icontains=title_query)

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
            "fields": {
                "name": item.name,
                "price": item.price,
                "description": item.description,
                "category": item.category,
                "image": item.image.path,
                "like_count": liked_users.count(),
                "is_liked": is_liked,
            }
        })

    return JsonResponse(data, safe=False)