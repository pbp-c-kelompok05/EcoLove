from datetime import timedelta
from io import StringIO
from zoneinfo import ZoneInfo
from django.contrib import admin
from django.contrib.auth.models import User, Permission
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .forms import EventForm
from .models import Event, Education, EventComment

AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}

class EventsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('admin', 'admin@example.test', 'password')
        cls.user = User.objects.create_user('user', password='password')
        cls.other = User.objects.create_user('other', password='password')
        cls.staff = User.objects.create_user('staff', password='password', is_staff=True)
        cls.now = timezone.now()
        cls.event = Event.objects.create(title='Repair pakaian', description='Belajar menjahit', category='reuse',
            starts_at=cls.now + timedelta(days=1), ends_at=cls.now + timedelta(days=1, hours=2),
            location='Depok', organizer_contact='PRIVATE-CONTACT', meeting_link='https://example.test/PRIVATE-MEETING', creator=cls.admin)
        cls.education = Education.objects.create(title='Kompos', summary='Sisa dapur', body='Panduan kompos', category='waste', author=cls.admin)
        cls.comment = EventComment.objects.create(event=cls.event, user=cls.user, body='PRIVATE-COMMENT')

    def url(self, kind, action, obj=None):
        return reverse(f'events:{kind}_{action}', kwargs={'pk': obj.pk} if obj else None)

    def payload(self, kind):
        if kind == 'event':
            return {'title':'Acara baru', 'description':'Deskripsi', 'category':'reuse', 'starts_at':'2027-01-10T09:00',
                    'ends_at':'2027-01-10T11:00', 'location':'Jakarta', 'meeting_link':'https://example.test/meet'}
        return {'title':'Artikel baru', 'summary':'Ringkasan', 'body':'Isi artikel', 'category':'waste'}

    def test_module_pages_inherit_shared_shell_for_each_user_role(self):
        import re
        from django.templatetags.static import static

        for actor in [None, self.user, self.admin]:
            self.client.logout()
            if actor:
                self.client.force_login(actor)
            home = self.client.get(reverse('home')).content.decode()
            shared_header = re.search(r'<header\b.*?</header>', home, re.S).group()
            shared_footer = re.search(r'<footer\b.*?</footer>', home, re.S).group()
            for kind, obj in [('event', self.event), ('education', self.education)]:
                for action in ['list', 'detail', 'create', 'edit', 'manage', 'delete_confirm']:
                    with self.subTest(actor=actor and actor.username, kind=kind, action=action):
                        target = obj if action in ['detail', 'edit', 'delete_confirm'] else None
                        response = self.client.get(self.url(kind, action, target))
                        protected = action not in ['list', 'detail']
                        status = (403 if actor else 401) if protected and not (actor and actor.is_superuser) else 200
                        self.assertEqual(response.status_code, status)
                        self.assertTemplateUsed(response, 'base.html')
                        self.assertTemplateUsed(response, 'events/base.html')
                        html = response.content.decode()
                        for tag in ['html', 'body', 'header', 'main', 'footer']:
                            self.assertEqual(len(re.findall(rf'<{tag}\b', html)), 1)
                            self.assertEqual(html.count(f'</{tag}>'), 1)
                        header = re.search(r'<header\b.*?</header>', html, re.S).group()
                        footer = re.search(r'<footer\b.*?</footer>', html, re.S).group()
                        self.assertHTMLEqual(header, shared_header)
                        self.assertHTMLEqual(footer, shared_footer)
                        self.assertEqual(len(re.findall(r'<nav\b', header)), 1)
                        self.assertIn(static('img/logo-ecolove.png'), header)
                        self.assertNotIn('ee-navbar', html)
                        self.assertNotIn('ee-footer', html)
                        for asset in ['css/style.css', 'events/module.css', 'events/module.js',
                                      'events/vendor/grids-min.css', 'events/vendor/grids-responsive-min.css']:
                            self.assertEqual(html.count(f'"{static(asset)}"'), 1)
                        self.assertIn('id="ee-feedback"', html)
                        if actor and actor.is_superuser and action == 'list':
                            self.assertIn(f'href="{self.url(kind, "manage")}"', html)
                            self.assertIn(f'href="{self.url(kind, "create")}"', html)

    def test_shared_layout_preserves_filter_controls_and_ajax_fragments(self):
        for kind in ['event', 'education']:
            with self.subTest(kind=kind):
                url = self.url(kind, 'list')
                page = self.client.get(url)
                self.assertContains(page, 'id="ee-filter"')
                self.assertContains(page, 'id="ee-search"')
                self.assertContains(page, 'name="category" value="community"')
                self.assertContains(page, 'id="ee-results"')
                fragment = self.client.get(url, {}, **AJAX).json()['html']
                self.assertIn('ee-grid', fragment)
                for shell in ['<header', '<main', '<footer', 'events/module.css', 'events/module.js']:
                    self.assertNotIn(shell, fragment)

    def test_guest_reads_both_modules_but_no_private_html_or_json(self):
        for kind, obj in [('event', self.event), ('education', self.education)]:
            for action in ['list', 'detail']:
                url = self.url(kind, action, obj if action == 'detail' else None)
                for params, headers in [({}, {}), ({'format':'json'}, {}), ({}, AJAX)]:
                    response = self.client.get(url, params, **headers)
                    self.assertEqual(response.status_code, 200)
                    for secret in ['PRIVATE-CONTACT', 'PRIVATE-MEETING', 'PRIVATE-COMMENT']:
                        self.assertNotContains(response, secret)
        data = self.client.get(self.url('event', 'detail', self.event), {'format':'json'}).json()
        for key in ['organizer_contact', 'meeting_link', 'comments']:
            self.assertNotIn(key, data)

    def test_logged_in_private_detail_and_list_omission(self):
        self.client.force_login(self.user)
        url = self.url('event', 'detail', self.event)
        response = self.client.get(url)
        self.assertContains(response, 'PRIVATE-CONTACT')
        self.assertContains(response, 'PRIVATE-COMMENT')
        data = self.client.get(url, {'format':'json'}).json()
        self.assertEqual(data['organizer_contact'], 'PRIVATE-CONTACT')
        self.assertEqual(data['comments'][0]['body'], 'PRIVATE-COMMENT')
        listing = self.client.get(self.url('event','list'), {'format':'json'}).json()
        self.assertNotIn('organizer_contact', listing['results'][0])

    def test_mutation_permissions_for_guest_user_and_staff(self):
        for actor, status in [(None,401),(self.user,403),(self.staff,403)]:
            self.client.logout()
            if actor: self.client.force_login(actor)
            for kind, obj in [('event',self.event),('education',self.education)]:
                for action in ['create','edit','delete']:
                    url = self.url(kind, action, obj if action != 'create' else None)
                    self.assertEqual(self.client.post(url,self.payload(kind),**AJAX).status_code,status)
                    if action != 'delete': self.assertEqual(self.client.get(url).status_code,status)
        self.assertEqual(Event.objects.count(),1)
        self.assertEqual(Education.objects.count(),1)

    def test_superuser_ajax_crud_both_types_and_owner_not_spoofable(self):
        self.client.force_login(self.admin)
        for kind, model in [('event',Event),('education',Education)]:
            payload = self.payload(kind)
            payload.update(creator=self.other.pk, author=self.other.pk)
            response = self.client.post(self.url(kind,'create'),payload,**AJAX)
            self.assertEqual(response.status_code,201)
            obj = model.objects.get(title=payload['title'])
            self.assertEqual(getattr(obj,'creator_id' if kind == 'event' else 'author_id'),self.admin.pk)
            self.assertEqual(self.client.get(self.url(kind,'edit',obj)).status_code,200)
            payload['title'] = 'Diubah'
            self.assertEqual(self.client.post(self.url(kind,'edit',obj),payload,**AJAX).status_code,200)
            obj.refresh_from_db(); self.assertEqual(obj.title,'Diubah')
            self.assertEqual(self.client.post(self.url(kind,'delete',obj),**AJAX).status_code,200)
            self.assertFalse(model.objects.filter(pk=obj.pk).exists())

    def test_required_fields_and_invalid_end(self):
        self.client.force_login(self.admin)
        for kind in ['event','education']:
            response = self.client.post(self.url(kind,'create'),{},**AJAX)
            self.assertEqual(response.status_code,400)
            self.assertIn('title',response.json()['errors'])
        payload=self.payload('event'); payload['ends_at']='2027-01-09T08:00'
        response=self.client.post(self.url('event','create'),payload,**AJAX)
        self.assertEqual(response.status_code,400)
        self.assertIn('ends_at',response.json()['errors'])
        self.event.ends_at=self.event.starts_at-timedelta(minutes=1)
        with self.assertRaises(ValidationError): self.event.full_clean()

    def test_wib_round_trip_and_aware_storage(self):
        form=EventForm(data=self.payload('event'))
        self.assertTrue(form.is_valid(),form.errors)
        start=form.cleaned_data['starts_at']
        self.assertTrue(timezone.is_aware(start))
        self.assertEqual(start.astimezone(ZoneInfo('UTC')).hour,2)
        self.client.force_login(self.admin)
        self.client.post(self.url('event','create'),self.payload('event'),**AJAX)
        obj=Event.objects.get(title='Acara baru')
        html=self.client.get(self.url('event','edit',obj))
        self.assertContains(html,'2027-01-10T09:00')
        self.assertContains(self.client.get(self.url('event','detail',obj)),'10 Jan 2027 09:00')

    def test_search_category_status_and_pagination(self):
        Event.objects.create(title='Bersih pantai',description='Komunitas',category='community',location='Pantai',
            starts_at=self.now-timedelta(days=2),ends_at=self.now-timedelta(days=1),creator=self.admin)
        Event.objects.create(title='Sedang berlangsung',description='Repair',category='reuse',location='Depok',
            starts_at=self.now-timedelta(hours=1),ends_at=self.now+timedelta(hours=1),creator=self.admin)
        url=self.url('event','list')
        for params,title in [({'q':'menjahit'},'Repair pakaian'),({'category':'community'},'Bersih pantai'),
                             ({'status':'finished'},'Bersih pantai'),({'status':'upcoming'},'Repair pakaian'),
                             ({'status':'ongoing'},'Sedang berlangsung')]:
            data=self.client.get(url,dict(params,format='json')).json()
            self.assertEqual([o['title'] for o in data['results']],[title])
        self.assertEqual(self.client.get(url,{'q':'tidakada','format':'json'}).json()['results'],[])
        data=self.client.get(self.url('education','list'),{'q':'dapur','category':'waste','format':'json'}).json()
        self.assertEqual(data['results'][0]['title'],'Kompos')
        for i in range(14): Education.objects.create(title=f'Panduan {i}',summary='s',body='b',category='reuse',author=self.admin)
        data=self.client.get(self.url('education','list'),{'format':'json','page':2}).json()
        self.assertEqual(len(data['results']),3)

    def test_comments_auth_ownership_validation_and_moderation(self):
        add=reverse('events:comment_add',args=[self.event.pk])
        delete=reverse('events:comment_delete',args=[self.comment.pk])
        self.assertEqual(self.client.post(add,{'body':'Halo'}).status_code,401)
        self.assertEqual(self.client.post(delete).status_code,401)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(delete).status_code,403)
        self.assertEqual(self.client.post(add,{'body':'  '}).status_code,400)
        self.assertEqual(self.client.post(add,{'body':'x'*2001}).status_code,400)
        response=self.client.post(add,{'body':'Halo','user':self.admin.pk})
        self.assertEqual(response.status_code,201)
        self.assertEqual(EventComment.objects.get(body='Halo').user,self.other)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(delete).status_code,200)
        self.client.force_login(self.admin)
        own=EventComment.objects.get(body='Halo')
        self.assertEqual(self.client.post(reverse('events:comment_delete',args=[own.pk])).status_code,200)

    def test_get_cannot_mutate_and_missing_object(self):
        self.client.force_login(self.admin)
        for kind,obj in [('event',self.event),('education',self.education)]:
            self.assertEqual(self.client.get(self.url(kind,'delete',obj)).status_code,405)
            self.assertEqual(self.client.get(self.url(kind,'create')).status_code,200)
        for name,pk in [('comment_add',self.event.pk),('comment_delete',self.comment.pk)]:
            self.assertEqual(self.client.get(reverse('events:'+name,args=[pk])).status_code,405)
        import uuid
        self.assertEqual(self.client.get(reverse('events:event_detail',args=[uuid.uuid4()])).status_code,404)

    def test_csrf_is_enforced_for_all_writes(self):
        client=Client(enforce_csrf_checks=True); client.force_login(self.admin)
        urls=[self.url(k,a,o if a!='create' else None) for k,o in [('event',self.event),('education',self.education)] for a in ['create','edit','delete']]
        urls += [reverse('events:comment_add',args=[self.event.pk]),reverse('events:comment_delete',args=[self.comment.pk])]
        for url in urls: self.assertEqual(client.post(url,{},**AJAX).status_code,403)
        client.get(self.url('event','create'))
        token=client.cookies['csrftoken'].value
        self.assertEqual(client.post(self.url('event','create'),self.payload('event'),HTTP_X_CSRFTOKEN=token,**AJAX).status_code,201)

    def test_xss_escaped_in_html_and_ajax_partials(self):
        attack='<img src=x onerror=alert(1)>'
        self.event.title=attack; self.event.description=attack; self.event.save()
        self.education.body=attack; self.education.save()
        self.comment.body=attack; self.comment.save()
        self.client.force_login(self.user)
        for url in [self.url('event','detail',self.event),self.url('education','detail',self.education)]:
            response=self.client.get(url)
            self.assertNotContains(response,attack)
            self.assertContains(response,'&lt;img')
        data=self.client.get(self.url('event','list'),{},**AJAX).json()
        self.assertNotIn(attack,data['html'])
        response=self.client.post(reverse('events:comment_add',args=[self.event.pk]),{'body':attack})
        self.assertNotIn(attack,response.json()['html'])
        self.assertIn('&lt;img',response.json()['html'])

    def test_staff_with_model_permissions_still_denied_in_admin(self):
        self.staff.user_permissions.add(*Permission.objects.filter(content_type__app_label='events'))
        for model in [Event,Education,EventComment]:
            instance=admin.site._registry[model]
            from django.test import RequestFactory
            request=RequestFactory().get('/admin/'); request.user=self.staff
            for action in ['view','add','change','delete']:
                self.assertFalse(getattr(instance,f'has_{action}_permission')(request))

    def test_seed_idempotent_and_no_education_interactions(self):
        for _ in range(2): call_command('seed_events',username='admin',stdout=StringIO())
        self.assertEqual(Event.objects.filter(title__startswith='[DEMO]').count(),3)
        self.assertEqual(Education.objects.filter(title__startswith='[DEMO]').count(),3)
        self.client.force_login(self.user)
        html=self.client.get(self.url('education','detail',self.education))
        self.assertNotContains(html,'ee-comment-form')
        self.assertNotContains(html,'Diskusi event')

    def test_images_and_unsafe_meeting_url_validation(self):
        import tempfile
        from PIL import Image
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.force_login(self.admin)
        payload=self.payload('event'); payload['meeting_link']='javascript:alert(1)'
        response=self.client.post(self.url('event','create'),payload,**AJAX)
        self.assertEqual(response.status_code,400)
        self.assertIn('meeting_link',response.json()['errors'])
        for kind in ['event','education']:
            payload=self.payload(kind)
            payload['image']=SimpleUploadedFile('fake.png',b'not an image',content_type='image/png')
            self.assertEqual(self.client.post(self.url(kind,'create'),payload,**AJAX).status_code,400)
            image=BytesIO(); Image.new('RGB',(2,2)).save(image,format='PNG')
            payload['image']=SimpleUploadedFile('sample.png',image.getvalue(),content_type='image/png')
            with tempfile.TemporaryDirectory() as uploads, self.settings(MEDIA_ROOT=uploads):
                response=self.client.post(self.url(kind,'create'),payload,**AJAX)
                self.assertEqual(response.status_code,201)
                model=Event if kind=='event' else Education
                obj=model.objects.get(title=payload['title'])
                self.assertTrue(obj.image.storage.exists(obj.image.name))
                self.assertContains(self.client.get(self.url(kind,'detail',obj)),obj.image.url)

    def test_wib_midnight_crosses_utc_date_on_create_edit_and_lists(self):
        from datetime import datetime, timezone as dt_timezone
        self.client.force_login(self.admin)
        payload=self.payload('event')
        payload.update(starts_at='2027-01-10T00:30',ends_at='2027-01-10T01:30')
        result=self.client.post(self.url('event','create'),payload,**AJAX)
        self.assertEqual(result.status_code,201)
        event=Event.objects.get(title=payload['title'])
        self.assertEqual(event.starts_at,datetime(2027,1,9,17,30,tzinfo=dt_timezone.utc))
        edit=self.client.get(self.url('event','edit',event))
        self.assertContains(edit,'2027-01-10T00:30')
        self.assertContains(self.client.get(self.url('event','detail',event)),'10 Jan 2027 00:30')
        self.assertContains(self.client.get(self.url('event','list')),'10 Jan 2027 00:30')
        result=self.client.post(self.url('event','edit',event),payload,**AJAX)
        self.assertEqual(result.status_code,200)
        event.refresh_from_db()
        self.assertEqual(event.starts_at,datetime(2027,1,9,17,30,tzinfo=dt_timezone.utc))
        payload['ends_at']='2027-01-10T00:29'
        self.assertEqual(self.client.post(self.url('event','edit',event),payload,**AJAX).status_code,400)
        event.refresh_from_db()
        self.assertEqual(event.ends_at,datetime(2027,1,9,18,30,tzinfo=dt_timezone.utc))

    def test_filtered_pagination_preserves_filters_and_handles_invalid_pages(self):
        from html import unescape
        from urllib.parse import urlsplit,parse_qs
        for i in range(14):
            Event.objects.create(title=f'Repair series {i:02}',description='Materi',category='reuse',
                location='Depok',starts_at=self.now+timedelta(days=2),ends_at=self.now+timedelta(days=2,hours=1),creator=self.admin)
        params={'q':'Repair series','category':'reuse','status':'upcoming'}
        url=self.url('event','list')
        response=self.client.get(url,params)
        # Parse only the pagination URL to prove it works without JavaScript too.
        import re
        link=re.search(r'href="([^"]+)" data-page="2"',response.content.decode()).group(1)
        parsed=parse_qs(urlsplit(unescape(link)).query)
        self.assertEqual(parsed,dict((key,[value]) for key,value in dict(params,page='2').items()))
        page=self.client.get(url,dict(params,page='2',format='json')).json()
        self.assertEqual(len(page['results']),2)
        self.assertEqual(page['pages'],2)
        self.assertTrue(all(o['title'].startswith('Repair series') for o in page['results']))
        for value,expected in [('nonsense',1),('999',2),('-1',2)]:
            data=self.client.get(url,dict(params,page=value,format='json')).json()
            self.assertEqual(data['page'],expected)

    def test_all_disallowed_http_methods_and_guest_json_mutations(self):
        for kind,obj in [('event',self.event),('education',self.education)]:
            for action in ['list','detail']:
                url=self.url(kind,action,obj if action=='detail' else None)
                self.assertEqual(self.client.post(url).status_code,405)
            for action in ['create','edit','delete']:
                url=self.url(kind,action,obj if action!='create' else None)
                for verb in ['put','patch','delete']:
                    self.assertEqual(getattr(self.client,verb)(url).status_code,405)
                response=self.client.post(url,{'format':'json'},**AJAX)
                self.assertEqual(response.status_code,401)
                for secret in ['PRIVATE-CONTACT','PRIVATE-MEETING','PRIVATE-COMMENT']:
                    self.assertNotIn(secret,response.content.decode())
        for name,pk in [('comment_add',self.event.pk),('comment_delete',self.comment.pk)]:
            url=reverse('events:'+name,args=[pk])
            response=self.client.post(url,**AJAX)
            self.assertEqual(response.status_code,401)
            self.assertNotIn('PRIVATE-',response.content.decode())
            for verb in ['get','put','patch','delete']:
                self.assertEqual(getattr(self.client,verb)(url).status_code,405)

    def test_csrf_valid_update_comment_delete_and_invalid_token_no_side_effects(self):
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        client.get(self.url('event','edit',self.event))
        token=client.cookies['csrftoken'].value
        update=self.url('event','edit',self.event)
        payload=self.payload('event')
        for headers in [{},{'HTTP_X_CSRFTOKEN':'x'*32}]:
            self.assertEqual(client.post(update,payload,**headers,**AJAX).status_code,403)
            self.event.refresh_from_db(); self.assertEqual(self.event.title,'Repair pakaian')
        valid={'HTTP_X_CSRFTOKEN':token,**AJAX}
        self.assertEqual(client.post(update,payload,**valid).status_code,200)
        add=reverse('events:comment_add',args=[self.event.pk])
        self.assertEqual(client.post(add,{'body':'CSRF valid'},**valid).status_code,201)
        comment=EventComment.objects.get(body='CSRF valid')
        self.assertEqual(client.post(reverse('events:comment_delete',args=[comment.pk]),**valid).status_code,200)
        self.assertEqual(client.post(self.url('event','delete',self.event),**valid).status_code,200)
        self.assertFalse(EventComment.objects.filter(event_id=self.event.pk).exists())

    def test_owner_preserved_on_update_and_admin_form_excludes_owner(self):
        from django.test import RequestFactory
        self.client.force_login(self.admin)
        request=RequestFactory().get('/admin/'); request.user=self.admin
        for kind,obj,owner in [('event',self.event,'creator'),('education',self.education,'author')]:
            payload=self.payload(kind); payload[owner]=self.other.pk
            response=self.client.post(self.url(kind,'edit',obj),payload,**AJAX)
            self.assertEqual(response.status_code,200)
            obj.refresh_from_db(); self.assertEqual(getattr(obj,owner+'_id'),self.admin.pk)
            form_class=admin.site._registry[type(obj)].get_form(request,obj)
            self.assertNotIn(owner,form_class.base_fields)
        self.client.force_login(self.staff)
        self.staff.user_permissions.add(*Permission.objects.filter(content_type__app_label='events'))
        for model,obj in [('event',self.event),('education',self.education),('eventcomment',self.comment)]:
            for action,args in [('add',[]),('change',[obj.pk]),('delete',[obj.pk])]:
                url=reverse(f'admin:events_{model}_{action}',args=args)
                self.assertEqual(self.client.post(url,{}).status_code,403)

    def test_dangerous_url_schemes_rejected_and_legacy_rows_render_inert(self):
        self.client.force_login(self.admin)
        for url in ['javascript:alert(1)','data:text/html,<script>alert(1)</script>',
                    'ftp://example.test/file','file:///tmp/a','//example.test/meet']:
            payload=self.payload('event'); payload['meeting_link']=url
            # A scheme-relative URL is normalized by Django to HTTP(S) and is safe.
            response=self.client.post(self.url('event','edit',self.event),payload,**AJAX)
            if url.startswith('//'):
                self.assertEqual(response.status_code,200)
                self.event.refresh_from_db(); self.assertTrue(self.event.meeting_link.startswith(('http://','https://')))
            else:
                self.assertEqual(response.status_code,400)
                self.assertIn('meeting_link',response.json()['errors'])
        Event.objects.filter(pk=self.event.pk).update(meeting_link='javascript:alert(1)')
        self.client.force_login(self.user)
        html=self.client.get(self.url('event','detail',self.event))
        self.assertNotContains(html,'javascript:')
        data=self.client.get(self.url('event','detail',self.event),{'format':'json'}).json()
        self.assertEqual(data['meeting_link'],'')

    def test_event_delete_cascades_comments_but_retains_other_events_and_images(self):
        import tempfile
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image
        from io import BytesIO
        other=Event.objects.create(title='Lain',description='d',category='reuse',location='l',
            starts_at=self.now,ends_at=self.now,creator=self.admin)
        other_comment=EventComment.objects.create(event=other,user=self.user,body='Tetap ada')
        image=BytesIO(); Image.new('RGB',(2,2)).save(image,format='PNG')
        self.client.force_login(self.admin)
        with tempfile.TemporaryDirectory() as uploads,self.settings(MEDIA_ROOT=uploads):
            self.event.image.save('retained.png',SimpleUploadedFile('x.png',image.getvalue()))
            name=self.event.image.name; storage=self.event.image.storage
            response=self.client.post(self.url('event','delete',self.event),**AJAX)
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json()['url'],self.url('event','list'))
            self.assertFalse(EventComment.objects.filter(pk=self.comment.pk).exists())
            self.assertTrue(EventComment.objects.filter(pk=other_comment.pk).exists())
            self.assertTrue(storage.exists(name))

    def test_seed_second_run_preserves_existing_edited_demo(self):
        call_command('seed_events',username='admin',stdout=StringIO())
        event=Event.objects.filter(title__startswith='[DEMO]').first()
        start=event.starts_at
        Event.objects.filter(pk=event.pk).update(description='Disunting')
        Education.objects.filter(title__startswith='[DEMO]').update(body='Disunting')
        call_command('seed_events',username='admin',stdout=StringIO())
        event.refresh_from_db()
        self.assertEqual(event.starts_at,start)
        self.assertEqual(event.description,'Disunting')
        self.assertEqual(Education.objects.filter(title__startswith='[DEMO]',body='Disunting').count(),3)
        self.assertEqual(Event.objects.filter(title__startswith='[DEMO]').count(),3)

    def test_legacy_media_routing_is_scoped_and_shared_pages_do_not_load_pure(self):
        import importlib,tempfile
        from pathlib import Path
        from django.conf import settings
        from django.urls import clear_url_caches,resolve,Resolver404
        import EcoLove.urls as root_urls
        storages=dict(settings.STORAGES)
        with tempfile.TemporaryDirectory() as uploads:
            storages['default']={'BACKEND':'django.core.files.storage.FileSystemStorage','OPTIONS':{'location':uploads}}
            try:
                with self.settings(DEBUG=True,MEDIA_ROOT='',MEDIA_URL='/',STORAGES=storages):
                    importlib.reload(root_urls); clear_url_caches()
                    for folder in ['item_images','event_images','education_images']:
                        path=Path(uploads)/folder; path.mkdir()
                        (path/'sample.png').write_bytes(b'isolated fixture')
                        response=self.client.get(f'/{folder}/sample.png')
                        self.assertEqual(response.status_code,200)
                        self.assertEqual(b''.join(response.streaming_content),b'isolated fixture')
                    for url in ['/manage.py','/.env','/EcoLove/settings.py']:
                        self.assertEqual(self.client.get(url).status_code,404)
                    with self.assertLogs('django.security.SuspiciousFileOperation',level='ERROR'):
                        self.assertEqual(self.client.get('/event_images/../manage.py').status_code,400)
            finally:
                importlib.reload(root_urls); clear_url_caches()
        for url in ['/login/','/marketplace/']:
            response=self.client.get(url)
            self.assertEqual(response.status_code,200)
            self.assertNotContains(response,'events/vendor/')
            self.assertNotContains(response,'events/module.css')
        page=self.client.get(self.url('event','list'))
        self.assertContains(page,'events/vendor/grids-min.css')
        self.assertContains(page,'pure-u-md-1-2')

    def test_admin_event_form_and_list_use_wib(self):
        from datetime import datetime,timezone as dt_timezone
        from django.test import RequestFactory
        self.event.starts_at=datetime(2027,1,9,17,30,tzinfo=dt_timezone.utc)
        self.event.ends_at=self.event.starts_at+timedelta(hours=1)
        request=RequestFactory().get('/admin/'); request.user=self.admin
        registered=admin.site._registry[Event]
        form=registered.get_form(request,self.event)(instance=self.event)
        self.assertIn('2027-01-10T00:30',str(form['starts_at']))
        self.assertEqual(registered.starts_at_wib(self.event),'10-01-2027 00:30 WIB')

    def test_pagination_hidden_for_single_page_and_empty_results(self):
        for kind in ['event', 'education']:
            url = self.url(kind, 'list')
            for params in [{}, {'q': 'tidak-ditemukan'}]:
                response = self.client.get(url, params)
                self.assertNotContains(response, 'class="ee-pagination"')
                html = self.client.get(url, params, **AJAX).json()['html']
                self.assertNotIn('class="ee-pagination"', html)

    def test_empty_collection_and_filtered_results_have_distinct_guidance(self):
        for kind, model in [('event', Event), ('education', Education)]:
            url = self.url(kind, 'list')
            filtered = self.client.get(url, {'q': 'tidak-ditemukan'})
            self.assertContains(filtered, 'Reset pencarian dan filter')
            self.assertContains(filtered, f'href="{url}"')
            model.objects.all().delete()
            empty = self.client.get(url)
            self.assertContains(empty, 'Belum ada')
            self.assertNotContains(empty, 'Reset pencarian dan filter')

    def test_validation_descriptions_reference_rendered_help_and_error_holders(self):
        from html.parser import HTMLParser

        class FormElements(HTMLParser):
            def __init__(self):
                super().__init__()
                self.ids = set()
                self.descriptions = []

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if attrs.get('id'):
                    self.ids.add(attrs['id'])
                if attrs.get('aria-describedby'):
                    self.descriptions.extend(attrs['aria-describedby'].split())

        self.client.force_login(self.admin)
        for kind in ['event', 'education']:
            url = self.url(kind, 'create')
            for response in [self.client.get(url), self.client.post(url, {})]:
                parsed = FormElements()
                parsed.feed(response.content.decode())
                self.assertTrue(parsed.descriptions)
                self.assertTrue(set(parsed.descriptions).issubset(parsed.ids))
                self.assertContains(response, 'id="id_title_errors" data-errors-for="title"')
        comment = self.client.get(self.url('event', 'detail', self.event))
        self.assertContains(comment, 'aria-describedby="id_body_errors"')
        self.assertContains(comment, 'id="id_body_errors" data-errors-for="body"')

    def test_success_feedback_survives_ajax_redirect_and_plain_form_posts(self):
        self.client.force_login(self.admin)
        for kind, model in [('event', Event), ('education', Education)]:
            created = self.client.post(self.url(kind, 'create'), self.payload(kind), **AJAX)
            self.assertEqual(created.status_code, 201)
            self.assertContains(self.client.get(created.json()['url']), 'berhasil ditambahkan.')
            obj = model.objects.get(title=self.payload(kind)['title'])
            edited = self.client.post(self.url(kind, 'edit', obj), self.payload(kind), follow=True)
            self.assertContains(edited, 'berhasil diperbarui.')
            deleted = self.client.post(self.url(kind, 'delete', obj), **AJAX)
            self.assertContains(self.client.get(deleted.json()['url']), 'berhasil dihapus.')
