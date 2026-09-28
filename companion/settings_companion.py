# -*- coding: utf-8 -*-

# Activates the companion-app trainer-mode endpoints (SPEC.md §14am) and the
# S-15/S-16 ledger app without touching the image's own settings/main.py.
# Overrides ROOT_URLCONF to point at wger.companion_api, a brand-new module
# (see companion/companion_api.py) that only *adds* routes on top of the
# image's own wger.urls rather than replacing it, and appends
# wger.companion_ledger to INSTALLED_APPS - so nothing here needs updating
# when the base image's real settings.main or urls.py change.
#
# Mounted into the container as settings/companion.py and activated via
# DJANGO_SETTINGS_MODULE=settings.companion (set only for the `web` service
# in docker-compose.override.yml); celery keeps the image's default
# settings.main since it never serves these routes or runs these migrations.

# wger
from .main import *  # noqa: F401,F403

ROOT_URLCONF = 'wger.companion_api'

# S-15/S-16 - companion/companion_ledger/ (LedgerEntry, ItemDefinition).
# Appended, never inserted first/replacing the list, so this can never
# shadow or reorder any of wger's own apps.
INSTALLED_APPS = [*INSTALLED_APPS, 'wger.companion_ledger']
