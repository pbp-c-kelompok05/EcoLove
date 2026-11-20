from django.urls import path
from reviews import api_views

app_name = "reviews_api"
urlpatterns = [
    path("reviews/<uuid:item_id>/list/", api_views.review_list, name="review-list"),
    path("reviews/<uuid:review_id>/detail/", api_views.review_detail, name="review-detail"),
    path("reviews/<uuid:review_id>/like/", api_views.review_like, name="review-like"),
    path("reviews/<uuid:review_id>/dislike/", api_views.review_dislike, name="review-dislike"),
]