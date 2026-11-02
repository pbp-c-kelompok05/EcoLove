from functools import wraps
from zoneinfo import ZoneInfo
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .forms import EventForm, EducationForm, EventCommentForm
from .models import Event, Education, EventComment, EventRegistration, CATEGORIES

KINDS = {'event': (Event, EventForm, 'Events'), 'education': (Education, EducationForm, 'Education')}

def ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def superuser_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if ajax(request):
                return JsonResponse({'error': 'Silakan login terlebih dahulu.'}, status=401)
            return render(request, 'events/access_denied.html', {'kind': kwargs.get('kind', 'event')}, status=401)
        if not request.user.is_superuser:
            if ajax(request):
                return JsonResponse({'error': 'Hanya superuser yang dapat mengelola konten.'}, status=403)
            return render(request, 'events/access_denied.html', {'kind': kwargs.get('kind', 'event')}, status=403)
        return view(request, *args, **kwargs)
    return wrapped

def content_url(kind, action, pk=None):
    return reverse(f'events:{kind}_{action}', kwargs={'pk': pk} if pk else None)

def public_data(obj, request, detail=False):
    kind = 'event' if isinstance(obj, Event) else 'education'
    data = {'id': str(obj.pk), 'title': obj.title, 'category': obj.category,
            'category_label': obj.get_category_display(), 'url': content_url(kind, 'detail', obj.pk),
            'image': obj.image.url if obj.image else None}
    if kind == 'event':
        data.update(description=obj.description, location=obj.location, is_online=obj.is_online,
                    starts_at=obj.starts_at.isoformat(), ends_at=obj.ends_at.isoformat(),
                    status=obj.status_label, registration_open=obj.registration_open)
        if detail and request.user.is_authenticated:
            data.update(organizer_contact=obj.organizer_contact, meeting_link=obj.safe_meeting_link,
                        is_registered=obj.registrations.filter(user=request.user).exists(),
                        comments=[{'id': str(c.pk), 'body': c.body, 'username': c.user.username,
                                   'image': c.image.url if c.image else None,
                                   'created_at': c.created_at.isoformat()} for c in obj.comments.select_related('user')])
    else:
        data.update(summary=obj.summary)
        if detail:
            data['body'] = obj.body
    return data

@require_GET
def listing(request, kind):
    model, _, label = KINDS[kind]
    objects = model.objects.all()
    query = request.GET.get('q', '').strip()[:200]
    category = request.GET.get('category', '')
    if category == 'community':
        # Keep legacy links usable without an unavailable, invisible filter.
        params = request.GET.copy()
        del params['category']
        url = content_url(kind, 'list')
        if params:
            url += '?' + params.urlencode()
        return redirect(url)
    status = request.GET.get('status', '')
    if query:
        text_field = 'description' if kind == 'event' else 'body'
        condition = Q(title__icontains=query) | Q(**{f'{text_field}__icontains': query})
        if kind == 'event':
            condition |= Q(location__icontains=query)
        if kind == 'education':
            condition |= Q(summary__icontains=query)
        objects = objects.filter(condition)
    if category:
        objects = objects.filter(category=category)
    now = timezone.now()
    if kind == 'event':
        if status == 'upcoming':
            objects = objects.filter(starts_at__gt=now)
        elif status == 'ongoing':
            objects = objects.filter(starts_at__lte=now, ends_at__gte=now)
        elif status == 'finished':
            objects = objects.filter(ends_at__lt=now)
    page = Paginator(objects, 12).get_page(request.GET.get('page'))
    categories = [choice for choice in CATEGORIES if choice[0] != 'community']
    context = {'kind': kind, 'label': label, 'page': page, 'categories': categories,
               'query': query, 'category': category, 'status': status, 'now': now,
               'list_url': content_url(kind, 'list'), 'create_url': content_url(kind, 'create'),
               'manage_url': content_url(kind, 'manage')}
    with timezone.override(ZoneInfo('Asia/Jakarta')):
        if request.GET.get('format') == 'json' or ajax(request):
            return JsonResponse({'results': [public_data(o, request) for o in page],
                                 'html': render_to_string('events/cards.html', context, request=request),
                                 'page': page.number, 'pages': page.paginator.num_pages})
        return render(request, 'events/list.html', context)

@require_GET
def detail(request, kind, pk):
    obj = get_object_or_404(KINDS[kind][0], pk=pk)
    if request.GET.get('format') == 'json':
        return JsonResponse(public_data(obj, request, detail=True))
    context = {'object': obj, 'kind': kind, 'list_url': content_url(kind, 'list'),
               'edit_url': content_url(kind, 'edit', pk), 'delete_url': content_url(kind, 'delete', pk)}
    if kind == 'event' and request.user.is_authenticated:
        context.update(comments=obj.comments.select_related('user'), comment_form=EventCommentForm(),
                       is_registered=obj.registrations.filter(user=request.user).exists())
    with timezone.override(ZoneInfo('Asia/Jakarta')):
        return render(request, 'events/detail.html', context)

@require_http_methods(['GET', 'POST'])
@superuser_required
def edit(request, kind, pk=None):
    model, form_class, label = KINDS[kind]
    obj = get_object_or_404(model, pk=pk) if pk else None
    form = form_class(request.POST if request.method == 'POST' else None, request.FILES if request.method == 'POST' else None, instance=obj)
    if request.method == 'POST':
        if form.is_valid():
            saved = form.save(commit=False)
            if obj is None:
                setattr(saved, 'creator' if kind == 'event' else 'author', request.user)
            saved.save()
            messages.success(request, f'{label} berhasil {"diperbarui" if obj else "ditambahkan"}.')
            url = content_url(kind, 'detail', saved.pk)
            if ajax(request):
                return JsonResponse({'url': url}, status=200 if obj else 201)
            return redirect(url)
        if ajax(request):
            return JsonResponse({'error': 'Periksa kembali kolom yang ditandai.', 'errors': form.errors.get_json_data()}, status=400)
    return render(request, 'events/form.html', {'form': form, 'object': obj, 'label': label,
                  'kind': kind, 'list_url': content_url(kind, 'list')})


@require_GET
@superuser_required
def management(request, kind='event'):
    model, _, label = KINDS[kind]
    query = request.GET.get('q', '').strip()[:200]
    entries = model.objects.filter(title__icontains=query)
    context = {'kind': kind, 'label': label, 'query': query,
               'page': Paginator(entries, 12).get_page(request.GET.get('page')),
               'create_url': content_url(kind, 'create'), 'list_url': content_url(kind, 'list')}
    with timezone.override(ZoneInfo('Asia/Jakarta')):
        return render(request, 'events/manage.html', context)


@require_GET
@superuser_required
def delete_confirmation(request, kind, pk):
    obj = get_object_or_404(KINDS[kind][0], pk=pk)
    return render(request, 'events/confirm_delete.html', {
        'object': obj, 'kind': kind, 'delete_url': content_url(kind, 'delete', pk),
        'manage_url': content_url(kind, 'manage'),
    })

@require_POST
@superuser_required
def delete(request, kind, pk):
    get_object_or_404(KINDS[kind][0], pk=pk).delete()
    messages.success(request, f'{KINDS[kind][2]} berhasil dihapus.')
    url = content_url(kind, 'list')
    return JsonResponse({'url': url}) if ajax(request) else redirect(url)

@require_POST
def add_comment(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Silakan login untuk berkomentar.'}, status=401)
    event = get_object_or_404(Event, pk=pk)
    form = EventCommentForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({'error': 'Periksa kembali komentar yang ditandai.', 'errors': form.errors.get_json_data()}, status=400)
    comment = form.save(commit=False)
    comment.event, comment.user = event, request.user
    comment.save()
    with timezone.override(ZoneInfo('Asia/Jakarta')):
        html = render_to_string('events/comment.html', {'comment': comment}, request=request)
    return JsonResponse({'html': html}, status=201)

@require_POST
def delete_comment(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Silakan login terlebih dahulu.'}, status=401)
    comment = get_object_or_404(EventComment, pk=pk)
    if comment.user_id != request.user.pk and not request.user.is_superuser:
        return JsonResponse({'error': 'Anda hanya boleh menghapus komentar sendiri.'}, status=403)
    comment.delete()
    return JsonResponse({'message': 'Komentar dihapus.'})


@require_POST
def participation(request, pk):
    if not request.user.is_authenticated:
        if ajax(request):
            return JsonResponse({'error': 'Silakan masuk untuk mendaftar event.'}, status=401)
        messages.info(request, 'Silakan masuk, lalu kembali ke event untuk mendaftar.')
        return redirect('login')
    action = request.POST.get('action', 'register')
    if action not in ('register', 'cancel'):
        if ajax(request):
            return JsonResponse({'error': 'Pilihan pendaftaran tidak valid.'}, status=400)
        messages.error(request, 'Pilihan pendaftaran tidak valid.')
        return redirect(content_url('event', 'detail', pk))
    # Lock the event on databases supporting row locks. The unique constraint also
    # prevents duplicate registrations from concurrent requests.
    with transaction.atomic():
        event = get_object_or_404(Event.objects.select_for_update(), pk=pk)
        registrations = event.registrations.filter(user=request.user)
        code = 200
        if action == 'cancel':
            registrations.delete()
            notice = 'Keikutsertaan dibatalkan.'
        elif registrations.exists():
            notice = 'Kamu sudah terdaftar pada event ini.'
        elif not event.registration_open:
            notice = 'Pendaftaran ditutup karena event sudah dimulai atau selesai.'
            code = 409
        else:
            EventRegistration.objects.get_or_create(event=event, user=request.user)
            notice = 'Pendaftaran berhasil. Sampai bertemu di kegiatan!'
    if code == 409:
        messages.error(request, notice)
    else:
        messages.success(request, notice)
    url = content_url('event', 'detail', pk)
    if ajax(request):
        return JsonResponse({'url': url, 'message': notice, **({'error': notice} if code != 200 else {})}, status=code)
    return redirect(url)
