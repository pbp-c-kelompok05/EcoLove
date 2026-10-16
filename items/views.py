from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Item
from .forms import ItemForm

def show_marketplace(request):
    all_items = Item.objects.all().order_by('-id')
    user_items = []
    
    if request.user.is_authenticated:
        user_items = Item.objects.filter(user=request.user).order_by('-id')[:8]
        
    return render(request, 'marketplace.html', {
        'items': all_items,
        'user_items': user_items
    })

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
    
    return render(request, 'edit_item.html', {'form': form, 'item': item})

@login_required(login_url='/login/')
def delete_item(request, id):
    item = get_object_or_404(Item, id=id, user=request.user)
    
    if request.method == 'POST':
        item.delete()
        return redirect('items:show_marketplace')
  
    return render(request, 'delete_confirm.html', {'item': item})