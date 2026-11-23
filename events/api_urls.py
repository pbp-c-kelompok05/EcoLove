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
    path("education/", api_views.education_list, name="education-list"),
    path(
        "education/<uuid:education_id>/",
        api_views.education_detail,
        name="education-detail",
    ),
]
