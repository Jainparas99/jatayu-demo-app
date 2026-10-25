# Jatayu demo app — QueueDesk

An owned, purpose-built Django 4.2 migration target, written fresh on 2026-10-25.
QueueDesk tracks each user's work queue, bulk-edits cards, schedules UTC deadlines,
and exports CSV reports using a dedicated storage backend. SQLite is the only database.
It is intentionally a legacy training/demo target, not production software or an existing customer deployment.

## Run

Use Python 3.12:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
DJANGO_DEBUG=1 python manage.py runserver 127.0.0.1:8001
```

Sign in, then create work cards from the Django shell (no admin app is installed):

```python
from django.contrib.auth import get_user_model
from workboard.models import Card

owner = get_user_model().objects.first()
Card.objects.create(code="OPS-001", owner=owner, title="Rotate CI runner", estimate="120.00")
```

## Application checks

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --verbosity 2
```

The business suite checks ownership, bulk edits/deletes, validation, CSRF protection,
status filters, deadlines, localization behavior, CSV isolation, and export storage.
It does not assert a particular Django version. Preserve its behavioral assertions during migration;
renaming a removed assertion API is allowed, but weakening, skipping, or deleting checks is not.

## Legacy surfaces verified against official release notes

| Legacy use | Location / purpose | Removed in | Official notes |
|---|---|---|---|
| `USE_L10N=False` | settings; billing decimals stay unlocalized | 5.0 | [5.0 removals](https://docs.djangoproject.com/en/5.2/releases/5.0/#features-removed-in-5-0) |
| `timezone.utc` | services; UTC scheduling | 5.0 | [5.0 removals](https://docs.djangoproject.com/en/5.2/releases/5.0/#features-removed-in-5-0) |
| `Meta.index_together` | models and initial migration; owner/status index | 5.1 | [5.1 removals](https://docs.djangoproject.com/en/5.2/releases/5.1/#features-removed-in-5-1) |
| `length_is` | board template; empty/single-item queues | 5.1 | [5.1 removals](https://docs.djangoproject.com/en/5.2/releases/5.1/#features-removed-in-5-1) |
| `assertQuerysetEqual` | tests; owned queue order and status filtering | 5.1 | [5.1 removals](https://docs.djangoproject.com/en/5.2/releases/5.1/#features-removed-in-5-1) |
| `DEFAULT_FILE_STORAGE` | settings + export backend; separate report directory | 5.1 | [5.1 removals](https://docs.djangoproject.com/en/5.2/releases/5.1/#features-removed-in-5-1) |

Removed settings may be silently ignored. Tests cover their intended behavior, not just their presence.

## Separate security probe

```bash
python security_probe.py
```

The actual `/cards/edit/` route uses an owner-filtered model formset with editable natural
primary key `Card.code` and deletion enabled. The probe logs in as Alice, proves an ordinary
edit succeeds, then submits Bob's key through the same route and checks Bob's record survives.
This matches the preconditions in Django's [CVE-2026-87975 advisory](https://www.djangoproject.com/weblog/2026/oct/06/security-releases/#cve-2026-87975-privilege-abuse-in-model-formsets-with-editable-primary-keys).
It uses a disposable test database and in-process HTTP only. It never targets another host.
The script returns JSON and its own hash. Exit zero means the probe ran; require `outcome=blocked`
AND `benign_control_passed=true` for remediation. Exceptions are errors, never blocked results.

Keep this probe byte-for-byte unchanged during migration. Preserve every business assertion;
the old assertion-method spelling in the test suite needs the documented API rename. A local result does not establish
sandbox provenance, an Argon-generated upgrade, or applicability to other repositories.

## Local proof

Observed locally on Python 3.12.11, with asgiref 3.13.0 and sqlparse 0.6.0 held constant:

| Input | Observed result |
|---|---|
| Django 4.2.30 | All 25 application tests pass; system checks and migration drift check pass. |
| Django 5.2.18, changing only requirements.txt | Test command exits 1 during app setup: `Meta.index_together` is invalid. Tests cannot start. |
| Separate real-route probe on 4.2.30 | Normal owner edit succeeds; forged deletion removes the other owner's card (`vulnerable`). |

These are local observations, not sandbox verification. The bump-only failure is a startup failure,
not a count of 25 failed tests. No migrated-app security remediation has been claimed.
Raw stdout/stderr, exact runtime versions, source hashes, and the single-file comparison are in
ignored `.proof/proof.json` on the development machine. They are deliberately not GitHub demo metrics.

To reproduce the comparison, copy this source into a temporary directory, replace only
`Django==4.2.30` with `Django==5.2.18` in requirements.txt, install that file in a separate Python 3.12
virtualenv, and run the same `python manage.py test --verbosity 2`. Leave the source and tests unchanged for this bump-only comparison.
The original source remains pinned to 4.2.30.

For Jatayu's target adapter: project `config.settings`; model `workboard.Card`; editable primary key
`code`; ownership field `owner`; route `/cards/edit/`; authentication uses Django sessions.
`security_probe.py` follows the normal successful redirect and records both redirect chains plus the
final HTTP statuses. It emits JSON compatible with Jatayu's raw Django probe parser. After migration,
require this identical probe hash, a passing benign control, and `blocked`, then establish provenance
independently before enabling approval.
