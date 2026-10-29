from django.urls import path
from .views import (
    like,
    dislike,
    add_review,
    edit_review,
    delete,
    get_reviews_json
)

app_name = 'reviews'

urlpatterns = [
    path('api/reviews/<uuid:id>/', get_reviews_json, name='get_reviews_json'),

    # === REVIEW/REPLY CRUD === 
    path('like/<uuid:id>/', like, name='like'),
    path('dislike/<uuid:id>/', dislike, name='dislike'),
    path('add/review/<uuid:id>/', add_review, name='add_review'),
    path('edit/review/<uuid:id>/', edit_review, name='edit_review'),
    path('delete/<uuid:id>/', delete, name='delete'),
]