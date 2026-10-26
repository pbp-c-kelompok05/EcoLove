# Events & Education — PNG implementation

Implemented on `event-education`, 26 October 2026. The implementation stayed on this branch. Commit and push to `origin/event-education` were subsequently authorized by the project owner; merge, rebase, PR creation, and deployment remain outside the authorized scope.

## Inspection and scope

The repository already had an `events` Django app containing `Event`, `Education`, `EventComment`, ModelForms, generic content views, HTML/JSON listings, AJAX filters, image uploads, comments, and superuser-only CRUD. Public and authenticated users share Django's existing authentication. The README explicitly limits content management to superusers, including staff accounts with model permissions.

Existing uncommitted changes in forms, views, templates, tests, and JavaScript were retained, including accessible error holders, success messages, empty states, pagination rules, request cancellation, and browser history handling. A copy of the initial modified/untracked files was saved outside the repository before editing. Marketplace, product, checkout, user models, login behavior, project settings, and existing migrations were preserved.

The attached PNG was the visual reference. No PNG, Figma export, previous Pendev design, or temporary design reference was added to the repository. The new SVGs are production UI assets authored for this implementation.

## Implemented flows

- Events: illustrated listing → search title/description/location and filter category/time → event detail → existing login if needed → register → registered state → optional cancellation.
- Event details retain public information and restrict organizer contact, meeting links, and comments to authenticated users. Existing comment submission/moderation remains available.
- Education: illustrated listing → search title/summary/body and filter category → readable article → return to listing.
- Superuser management: Events/Education tabs → searchable, paginated table → create/edit form → detail; delete links lead to a dedicated confirmation page before a CSRF-protected POST.
- Guest/ordinary-user management requests show styled access guidance with HTTP 401/403; AJAX requests retain JSON errors. Ordinary users never receive content-management privileges.
- Loading feedback, request cancellation, failed-request feedback, form validation, empty collections, empty searches, success notices, hover/focus, and disabled states are supported.
- Shared module templates provide navigation, footer, buttons, cards, field errors, illustration fallbacks, and pagination. Existing global navigation/footer gain override blocks whose default markup is preserved for unrelated pages.

## Backend and data

The only schema addition is `EventRegistration`: UUID, event, user, creation timestamp, and a database uniqueness constraint on `(event, user)`. Registration takes the user from the session, validates the action, locks the event on databases with row-lock support, and uses `get_or_create`. Event deletion cascades to its registrations; existing content and user ownership rules are retained. Participant identities are not exposed by public JSON; authenticated detail JSON includes only the current user's participation flag.

`POST /events/<uuid>/participation/` accepts `action=register` or `action=cancel`. Repeated registration/cancellation is idempotent. New registration at or after the start time returns HTTP 409 to AJAX clients or redirects with an error notice for normal forms. Existing participation can still be viewed/cancelled after that boundary.

There is no capacity, waitlist, payment, approval, separate registration deadline, or independent closed-status field in the existing backend/reference. Registration therefore closes at `starts_at`, as explained in the UI. These additional business rules were not invented.

Articles retain their existing text field. An escaped, dependency-free formatter supports paragraphs, `#`/`##`/`###` headings, `-`/`*` bullet lists, and `1.` numbered lists. Raw HTML remains escaped. Existing plain-text articles still render.

Migration `0003_eventregistration` was verified to contain only `CreateModel` and applied to the existing local `db.sqlite3`. A consistent SQLite backup was made first outside the repository. No existing event, article, user, comment, upload, or product was deleted or overwritten. No deployment database was accessed for writes. Browser fixtures and test accounts were created only in a separate temporary preview database.

## Files

Modified during this task (some already had uncommitted changes):

- `events/models.py` — registration relation and event status helpers.
- `events/forms.py` — layout ordering, placeholders, invalid-field accessibility, article formatting hint; pre-existing accessibility work retained.
- `events/views.py` — management, confirmation, participation, location search, access/error feedback.
- `events/urls.py` — new module routes.
- `events/templates/events/base.html` — module navigation/footer and notices.
- `events/templates/events/list.html` — listing composition, banners, search, category chips, status filter.
- `events/templates/events/cards.html` — image fallbacks, metadata, actions, empty states.
- `events/templates/events/detail.html` — event sidebar/participation and centered education article.
- `events/templates/events/form.html` — create/edit screens.
- `events/templates/events/comment.html` — module button styling.
- `events/templates/events/fields.html` — pre-existing untracked partial extended with layout classes/private-field heading.
- `static/events/module.css` — scoped PNG-based visual and responsive styling.
- `static/events/module.js` — participation/confirmation submission; pre-existing accessibility/history fixes retained; action-field URL shadowing corrected.
- `templates/base.html` — compatible navigation/footer override blocks only.
- `README.md` — module behavior and validation documentation.

Created:

- `events/migrations/0003_eventregistration.py`
- `events/templates/events/access_denied.html`
- `events/templates/events/confirm_delete.html`
- `events/templates/events/illustration.html`
- `events/templates/events/manage.html`
- `events/templates/events/pagination.html`
- `events/templatetags/__init__.py`
- `events/templatetags/education_text.py`
- `events/test_participation.py`
- `static/events/illustrations/banner.svg`
- `static/events/illustrations/education-banner.svg`
- `static/events/illustrations/community.svg`
- `static/events/illustrations/plant.svg`
- `docs/events-education.md`

`events/tests.py` was already modified when the task began. Its existing 28 tests and local additions were retained unchanged during this task.

## Validation

Commands:

```powershell
.\env\Scripts\python.exe manage.py check --settings=EcoLove.test_settings
.\env\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=EcoLove.test_settings
.\env\Scripts\python.exe manage.py test --settings=EcoLove.test_settings
node --check static/events/module.js
git diff --check
```

All checks passed; 40 Django tests passed using the isolated SQLite test configuration. Coverage includes existing CRUD, permission checks (including staff), private HTML/JSON, uploads, safe URLs, WIB boundaries, CSRF/XSS, filters/pagination, plus new participation uniqueness, session ownership, cancellation, closure boundary, missing records, invalid actions, management access/search, confirmation and actual backend deletion, cascade behavior, structured text, and module links/static resolution.

Browser verification used synthetic content/accounts in a temporary SQLite database and separate preview cookies. Actual DOM widths of 390, 768, and 1280 CSS pixels were checked: one/two/three card columns, stacked mobile form fields, and no document overflow on inspected pages. Screenshots of listings, event details, an article, management, form errors, and confirmation pages were inspected against the visible PNG. A subsequent visible manual test exercised search by location, category filtering, empty results/reset, guest/login/reader/admin access, registration persistence after refresh, registration cancellation, comment creation/deletion, create/edit/delete of test Events and Education entries, server date validation, WIB edit values, and cancellation of the event delete-confirmation screen. Deletion was confirmed only for synthetic records in the temporary preview database. No missing images were found on the inspected pages.

A harmless existing WhiteNoise warning occurs in tests because `staticfiles/` has not been collected. PostgreSQL/deployment and concurrent multi-process browser registration were not exercised; the uniqueness constraint is independently tested.

## Visual limits and manual actions

The supplied composite is displayed at reduced resolution. Layout hierarchy, colors, spacing, typography, card treatment, banners, and illustrations were compared visually, but this is not a pixel-perfect comparison against individually exported original-size frames. The new SVGs approximate the illustrated clothing, community, and plant scenes. Content, dates, category labels, and private fields come from the existing database/schema, so they can differ from the sample copy. Delete confirmation uses a dedicated responsive page rather than the reference's small modal. Education create/edit uses the same reusable form system because a separate complete editor is not legible in the composite.

Existing login still redirects to Marketplace; the event page explains that users should return after login. Authentication was intentionally preserved. No new dependencies are required. Local migration is complete; restart an existing development server if it does not reload automatically. For a different database run `python manage.py migrate`, and collect static files through the project's existing hosting workflow when deploying. The existing optional idempotent `seed_events --username YOUR_LOCAL_SUPERUSER` command remains available; it was not run against the project database.

The visible manual-test preview was left open at the user's request after testing. Its SQLite database, accounts, and screenshot evidence are temporary artifacts outside the repository and are not included in the commit.

## Integration review before branch publication

The authorized destination is `origin`, repository `pbp-c-kelompok05/EcoLove`, branch `event-education`. At review time this remote branch did not exist. The branch also contains the earlier module implementation commit `6d82b57`, including app/URL integration, isolated test settings, the existing grid runtime, and its BSD license.

Comparison with fetched `origin/develop` found overlapping changes in `static/css/style.css` from the earlier module commit. Review those shared styles when integrating later; no merge or rebase was performed. The new PNG styling remains scoped to `static/events/module.css`.

No repository CI/deployment workflow or active local Git hook was found during this review. No workflow was modified, and no deployment was performed. Hosting integrations configured outside the repository were not inspected.
