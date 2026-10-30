from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import requires_csrf_token
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, get_object_or_404, redirect

from .models import Comment, Review, Reply
from .forms import ReviewForm

from items.models import Item, Order

@requires_csrf_token
@require_POST
def like(request, id):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"message": "Only logged-in users allowed to give likes."},
            status=403,
        )

    comment = get_object_or_404(Comment, id=id)
        
    if request.user in comment.disliked_by.all():
        comment.disliked_by.remove(request.user)
        
    liked_users = comment.liked_by.all()
    is_liked = request.user in liked_users
    if is_liked:
        comment.liked_by.remove(request.user)
    else:
        comment.liked_by.add(request.user)

    liked_users = comment.liked_by.all()
    is_liked = request.user in liked_users
    disliked_users = comment.disliked_by.all()
    is_disliked = request.user in disliked_users

    return JsonResponse(
        {
            "like_count": liked_users.count(),
            "is_liked": is_liked,
            "dislike_count": disliked_users.count(),
            "is_disliked": is_disliked,
        },
        status=201
    )

@requires_csrf_token
@require_POST
def dislike(request, id):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"message": "Only logged-in users allowed to give dislikes."},
            status=403,
        )

    comment = get_object_or_404(Comment, id=id)
        
    if request.user in comment.liked_by.all():
        comment.liked_by.remove(request.user)
        
    disliked_users = comment.disliked_by.all()
    is_disliked = request.user in disliked_users
    if is_disliked:
        comment.disliked_by.remove(request.user)
    else:
        comment.disliked_by.add(request.user)

    liked_users = comment.liked_by.all()
    is_liked = request.user in liked_users
    disliked_users = comment.disliked_by.all()
    is_disliked = request.user in disliked_users

    return JsonResponse(
        {
            "like_count": liked_users.count(),
            "is_liked": is_liked,
            "dislike_count": disliked_users.count(),
            "is_disliked": is_disliked,
        },
        status=201
    )

@requires_csrf_token
@require_POST
@login_required(login_url='/login/')
def add_review(request, id):
    item = get_object_or_404(Item, id=id)

    if request.user == item.user:
        return JsonResponse(
            {
                'message': 'Cannot give review to owned item.' 
            },
            status=403
        )

    #if not Order.objects.filter(item=item, buyer=request.user, status="PAID").exists():
    #   return JsonResponse(
    #       {
    #           'message': 'Review can only be given after purchase.' 
    #       },
    #       status=403
    #   )

    if item.reviews.filter(user=request.user):
        return JsonResponse(
            {
                'message': 'Cannot add duplicate review.' 
            },
            status=403
        )

    form = ReviewForm(request.POST) 
    if form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.item = item
        review.save()
        return JsonResponse(
            {
                'review': {
                    "pk": str(review.id),
                    "user": {
                        "pk": str(review.user.pk),
                        "name": str(review.user),
                    },
                    "fields": {
                        "text": review.text,
                        "rating": review.rating,
                        "like_count": 0,
                        "is_liked": False,
                        "dislike_count": 0,
                        "is_disliked": False,
                    }
                },
                'message': 'Successfully added review.' 
            },
            status=201
        )

    return JsonResponse(
        {
            'message': 'Failed to add review.' 
        },
        status=400
    )

@requires_csrf_token
@require_POST
@login_required(login_url='/login/')
def edit_review(request, id):
    review = get_object_or_404(Review, id=id)

    if not request.user.is_superuser and request.user != review.user:
        return JsonResponse(
            {
                'message': 'Cannot edit someone else\'s review.' 
            },
            status=403
        )
    
    form = ReviewForm(request.POST, instance=review)
    if form.is_valid():
        form.save()
        return JsonResponse(
        {
            'message': 'Successfully edited.',
            'text': review.text,
            'rating': review.rating,
        },
        status=201
    )

    return JsonResponse(
        {
            'message': 'Failed to edit.' 
        },
        status=400
    )

@requires_csrf_token
@require_POST
@login_required(login_url='/login/')
def delete(request, id):
    comment = get_object_or_404(Comment, id=id)

    if not request.user.is_superuser and request.user != comment.user:
        return JsonResponse(
            {
                'message': 'Cannot delete someone else\'s comment.' 
            },
            status=403
        )
    
    comment.delete()
    return JsonResponse(
        {
            'message': 'Successfully deleted.' 
        },
        status=201
    )
    

@require_GET
def get_reviews_json(request, id):
    item = get_object_or_404(Item, id=id)
    reviews = Review.objects.filter(item=item).prefetch_related("liked_by", "disliked_by")

    data = []
    for review in reviews:
        liked_users = review.liked_by.all()
        disliked_users = review.disliked_by.all()
        is_liked = request.user in liked_users \
            if request.user.is_authenticated and not request.user in disliked_users \
            else False
        is_disliked = request.user in disliked_users \
            if request.user.is_authenticated and not request.user in liked_users \
            else False

        review_data = {
            "pk": str(review.id),
            "user": {
                "pk": str(review.user.pk),
                "name": str(review.user),
            },
            "fields": {
                "text": review.text,
                "rating": review.rating,
                "like_count": liked_users.count(),
                "is_liked": is_liked,
                "dislike_count": disliked_users.count(),
                "is_disliked": is_disliked,
            }
        }

        if review.user == request.user:
            data.insert(0, review_data)
        else:
            data.append(review_data)

    return JsonResponse(data, safe=False)