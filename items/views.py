from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import requires_csrf_token
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, get_object_or_404, redirect

from .models import Item
from .forms import ItemForm

def show_marketplace(request):
    all_items = Item.objects.all().order_by('-id')
    return render(request, 'marketplace.html', {'items': all_items})

@login_required(login_url='/login/')
def my_marketplace(request):
    user_items = Item.objects.filter(user=request.user).order_by('-id')
    return render(request, 'my_marketplace.html', {'user_items': user_items})

def item_detail(request, id):
    item = get_object_or_404(Item, id=id)
    return render(request, 'item_detail.html', {'item': item})

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

@login_required(login_url='/login/')
def add_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES) 
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            return redirect('items:my_marketplace')
    else:
        form = ItemForm()
        
    return render(request, 'item_form.html', {'form': form})

@login_required(login_url='/login/')
def edit_item(request, id):
    item = get_object_or_404(Item, id=id, user=request.user)
    
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('items:item_detail', id=item.id)
    else:
        form = ItemForm(instance=item)
    
    return render(request, 'item_form.html', {'form': form, 'item': item})

@login_required(login_url='/login/')
def delete_item(request, id):
    item = get_object_or_404(Item, id=id, user=request.user)
    
    if request.method == 'POST':
        item.delete()
        return redirect('items:my_marketplace')
  
    return redirect('items:show_marketplace')

@require_GET
def get_items_json(request):
    title_query = request.GET.get("title", "").strip()
    items = Item.objects.prefetch_related("liked_by", "disliked_by").all()

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
