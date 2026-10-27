from django.urls import path
from . import views

app_name = 'events'
urlpatterns = []
for kind, prefix in [('event', ''), ('education', 'education/')]:
    urlpatterns += [
        path(prefix, views.listing, {'kind': kind}, name=f'{kind}_list'),
        path(prefix + 'new/', views.edit, {'kind': kind}, name=f'{kind}_create'),
        path(prefix + 'manage/', views.management, {'kind': kind}, name=f'{kind}_manage'),
        path(prefix + '<uuid:pk>/', views.detail, {'kind': kind}, name=f'{kind}_detail'),
        path(prefix + '<uuid:pk>/edit/', views.edit, {'kind': kind}, name=f'{kind}_edit'),
        path(prefix + '<uuid:pk>/delete/', views.delete, {'kind': kind}, name=f'{kind}_delete'),
        path(prefix + '<uuid:pk>/delete/confirm/', views.delete_confirmation, {'kind': kind}, name=f'{kind}_delete_confirm'),
    ]
urlpatterns += [
    path('<uuid:pk>/participation/', views.participation, name='event_participation'),
    path('<uuid:pk>/comments/add/', views.add_comment, name='comment_add'),
    path('comments/<uuid:pk>/delete/', views.delete_comment, name='comment_delete'),
]
