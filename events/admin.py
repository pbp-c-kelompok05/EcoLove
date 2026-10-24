from django.contrib import admin
from django.utils import timezone
from .forms import EventForm, WIB
from .models import Event, Education, EventComment

class SuperuserOnlyAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    has_add_permission = has_view_permission
    has_change_permission = has_view_permission
    has_delete_permission = has_view_permission

@admin.register(Event)
class EventAdmin(SuperuserOnlyAdmin):
    form = EventForm
    readonly_fields = ['creator']
    list_display = ['title', 'category', 'starts_at_wib', 'is_online', 'creator']
    list_filter = ['category', 'is_online']
    search_fields = ['title', 'description']

    @admin.display(description='Mulai (WIB)', ordering='starts_at')
    def starts_at_wib(self, obj):
        return timezone.localtime(obj.starts_at, WIB).strftime('%d-%m-%Y %H:%M WIB')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        super().save_model(request, obj, form, change)

@admin.register(Education)
class EducationAdmin(SuperuserOnlyAdmin):
    readonly_fields = ['author']
    list_display = ['title', 'category', 'author', 'updated_at']
    list_filter = ['category']
    search_fields = ['title', 'summary', 'body']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.author = request.user
        super().save_model(request, obj, form, change)

@admin.register(EventComment)
class CommentAdmin(SuperuserOnlyAdmin):
    readonly_fields = ['user']
    list_display = ['event', 'user', 'created_at']
    search_fields = ['body', 'user__username']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        super().save_model(request, obj, form, change)
