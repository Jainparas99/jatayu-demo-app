"""Probe only this owned app via Django's in-process test client and an isolated test DB.

Exit 0 means the probe executed; read outcome to distinguish vulnerable/blocked.
Errors, failed benign controls and timeouts must never count as remediation.
"""

import hashlib
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path


def run():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.test import Client
    from django.test.utils import get_runner
    from django.urls import reverse

    from workboard.models import Card

    runner = get_runner(settings)(verbosity=0, interactive=False)
    runner.setup_test_environment()
    databases = runner.setup_databases()
    try:
        alice = get_user_model().objects.create_user("probe-alice")
        bob = get_user_model().objects.create_user("probe-bob")
        Card.objects.create(code="ALICE-001", owner=alice, title="Before")
        Card.objects.create(code="BOB-001", owner=bob, title="Must survive")
        browser = Client()
        browser.force_login(alice)
        payload = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-code": "ALICE-001",
            "form-0-title": "Benign edit",
            "form-0-status": "open",
            "form-0-estimate": "0.00",
        }
        benign = browser.post(reverse("edit-cards"), payload, follow=True)
        benign_ok = (
            benign.status_code == 200
            and Card.objects.get(pk="ALICE-001").title == "Benign edit"
            and Card.objects.filter(pk="BOB-001", owner=bob).exists()
        )
        attack = browser.post(
            reverse("edit-cards"),
            {
                **payload,
                "form-0-code": "BOB-001",
                "form-0-title": "Must survive",
                "form-0-DELETE": "on",
            },
            follow=True,
        )
        survived = Card.objects.filter(pk="BOB-001", owner=bob, title="Must survive").exists()
        if not benign_ok or attack.status_code != 200:
            outcome = "error"
        else:
            outcome = "blocked" if survived else "vulnerable"
        return {
            "scope": "owned_target_app_local_test_client",
            "case": "CVE-2026-87975",
            "django_version": django.get_version(),
            "python_version": sys.version,
            "dependencies": {name: version(name) for name in ("Django", "asgiref", "sqlparse")},
            "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "benign_control_passed": benign_ok,
            "benign_http_status": benign.status_code,
            "benign_redirects": benign.redirect_chain,
            "attack_redirects": attack.redirect_chain,
            "http_status": attack.status_code,
            "foreign_card_survived": survived,
            "outcome": outcome,
        }
    finally:
        runner.teardown_databases(databases)
        runner.teardown_test_environment()


if __name__ == "__main__":
    try:
        result = run()
    except Exception as exc:
        print(json.dumps({"outcome": "error", "error": f"{type(exc).__name__}: {exc}"}))
        raise SystemExit(1) from exc
    print(json.dumps(result, sort_keys=True))
    if result["outcome"] == "error":
        raise SystemExit(1)
