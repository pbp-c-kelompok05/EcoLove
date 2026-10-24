from django.urls import path
from . import views

app_name = 'events'
urlpatterns = []
for kind, prefix in [('event', ''), ('education', 'education/')]:
    urlpatterns += [
        path(prefix, views.listing, {'kind': kind}, name=f'{kind}_list'),
        path(prefix + 'new/', views.edit, {'kind': kind}, name=f'{kind}_create'),
        path(prefix + '<uuid:pk>/', views.detail, {'kind': kind}, name=f'{kind}_detail'),
        path(prefix + '<uuid:pk>/edit/', views.edit, {'kind': kind}, name=f'{kind}_edit'),
        path(prefix + '<uuid:pk>/delete/', views.delete, {'kind': kind}, name=f'{kind}_delete'),
    ]
urlpatterns += [
    path('<uuid:pk>/comments/add/', views.add_comment, name='comment_add'),
    path('comments/<uuid:pk>/delete/', views.delete_comment, name='comment_delete'),
]
