from django.urls import path

from events import api_views

app_name = "api"

urlpatterns = [
    path("events/", api_views.event_list, name="event-list"),
    path("events/<uuid:event_id>/", api_views.event_detail, name="event-detail"),
    path(
        "events/<uuid:event_id>/participate/",
        api_views.event_participate,
        name="event-participate",
    ),
    path(
        "events/<uuid:event_id>/comments/",
        api_views.event_comment_list,
        name="event-comment-list",
    ),
    path(
        "events/comments/<uuid:comment_id>/",
        api_views.event_comment_detail,
        name="event-comment-detail",
    ),
    path("education/", api_views.education_list, name="education-list"),
    path(
        "education/<uuid:education_id>/",
        api_views.education_detail,
        name="education-detail",
    ),
]
