# Events & Education verification — 30 October 2026

This report records the banner and testing update after integrating the latest
`origin/develop` into `event-education`. It supersedes the testing counts and
publication scope in the historical `events-education.md` implementation report.

## Banner refinement

- Events: calendar, community participants, location pin and leaf.
- Education: open book, leaf and lightbulb representing practical learning.
- Changed only `static/events/illustrations/banner.svg`,
  `static/events/illustrations/education-banner.svg`, and the banner alternative
  text in `events/templates/events/list.html`.
- Both SVGs retain `viewBox="0 0 1120 230"`, the original abstract backgrounds
  and muted green/cream/earth palette. They are about 1.2 KB and 1.1 KB.
  Banner CSS, spacing, aspect ratios, border radius and page structure are unchanged.
- No new runtime dependency, schema change, or production Python behavior change.
  Shared root layout/style files were not edited by this update. Teammate changes
  arrived through the normal merge from `develop` and were retained.

## Test audit and additions

Baseline: **63 passing tests**. Final: **90 passing tests**, **27 added**.
Existing tests already exercised CRUD, role restrictions, private detail data,
CSRF, XSS escaping, comments/photos, participation, search, category/time filters,
pagination, template/static links, accessible feedback and article formatting.
The added tests target gaps rather than replacing those tests.

| New file | Tests | Contracts checked |
| --- | ---: | --- |
| `events/test_models_forms.py` | 15 | Model persistence, UUID/defaults, timestamps, ownership relations, required fields/choices, database date constraint, exact time boundaries, protected owners, user deletion cascades; direct valid/invalid forms, WIB conversion, equal dates, length boundaries, URL schemes, escaped text, corrupt uploads, prefixed/optional form IDs |
| `events/test_workflows.py` | 6 | Both HTML CRUD journeys, failed creates/updates without side effects, list/detail persistence, redirect/template contracts, missing objects, empty/invalid JSON filters, bounded searches, participation error feedback, banner descriptions |
| `events/test_helpers_admin.py` | 6 | Animated PNG and decompression guards, safe text blocks, all admin permission hooks, admin ownership on create/edit, seed rejection without data creation |

The CRUD request journeys exercise Django routing, forms, ORM persistence,
templates, redirects and JSON together. They are **not browser tests**.
Existing authorization tests cover anonymous, ordinary, staff and superuser
accounts, owner-only comment deletion, superuser moderation, CSRF and spoofed
ownership fields. Content management is superuser-only, not owner-only.

## Coverage

Measured with coverage.py 7.17.0 and branch measurement enabled. Tests and
migrations are the only excluded files. Admin, app configuration, URLs, image
helpers, template filters and the seed command remain included.

Baseline production coverage: **95.81% combined statement/branch coverage**,
15 missed statements and partially covered branches. Final: **100.00%**,
**471/471 statements and 126/126 branches**, no remaining uncovered lines.

| Production file | Final coverage |
| --- | ---: |
| `events/models.py` | 100.00% |
| `events/forms.py` | 100.00% |
| `events/views.py` (including permission decorator) | 100.00% |
| `events/comment_images.py` | 100.00% |
| `events/admin.py` | 100.00% |
| `events/management/commands/seed_events.py` | 100.00% |
| `events/templatetags/education_text.py` | 100.00% |
| `events/urls.py` | 100.00% |
| `events/apps.py` | 100.00% |
| `events/__init__.py`, `events/templatetags/__init__.py` | 100.00% (no executable statements) |

`.coveragerc` enforces a **95%** minimum, strictly above the rubric's 90%.
`requirements-test.txt` adds only coverage.py to the existing requirements.
Coverage data, HTML reports and preview files are ignored and not committed.

## Reproduce

From PowerShell, using the existing environment:

```powershell
.\env\Scripts\python.exe -m pip install -r requirements-test.txt
.\env\Scripts\python.exe manage.py check
.\env\Scripts\python.exe manage.py test --noinput
.\env\Scripts\python.exe manage.py makemigrations --check --dry-run
.\env\Scripts\python.exe -m coverage run manage.py test --noinput
.\env\Scripts\python.exe -m coverage report
.\env\Scripts\python.exe -m coverage html
git diff --check
```

All verification commands above passed after the merge from `origin/develop`.
Tests use Django's temporary test database; no migrations were applied to the
existing local database. The local configuration used SQLite. For environments
that may contain production connection variables, append
`--settings=EcoLove.test_settings` to each Django command to force the existing
isolated SQLite configuration. The report is written to `htmlcov/index.html`.

The test run emits the existing WhiteNoise warning that `staticfiles/` has not
been collected. Static source assets resolve in tests. Deployment collection and
PostgreSQL-specific concurrency behavior were not tested here.

## Browser and visual limitation

No Playwright/Selenium setup is installed in the project. An isolated local
preview database with synthetic data was prepared; an HTTP request to `/events/`
returned 200. Django integration tests render both listings and validate their
banner asset paths and alternative text. Both SVGs parse as valid XML.

The browser connector was unavailable. The Windows computer-use fallback stopped
before navigating to the preview because it could not determine Chrome's current
URL confidently enough to enforce its policy. UI automation was stopped and the
preview server was terminated. **Desktop/mobile visual inspection and browser
search/filter/CRUD interaction were not completed in this run.** No browser test
pass is claimed, and no browser infrastructure was added.

## Publication review

The earlier local commit `fbf2b62` (card hover overlays) was already on
`event-education` at the start and is preserved in the integrated history. This
update does not alter it. Normal merge commits preserve teammate history;
publication is restricted to `origin/event-education` and `origin/develop`.

The measured model/form/view, CRUD and authorization coverage and passing suite
provide strong evidence for the Testing & Coverage 3.5 target. The assessor makes
the final grading decision. Python coverage does not measure JavaScript, CSS or
template branch coverage, and 100% coverage is not a guarantee of correctness.
