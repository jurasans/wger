# -*- coding: utf-8 -*-

# wger-companion S-15/S-16 (coin shop + server-side ledger) - see this
# fork's companion/companion_api.py header for the general pattern this
# follows. Registered via INSTALLED_APPS in settings/companion.py, not
# settings/main.py, so celery_worker/celery_beat (which keep the image's
# default settings module) never load this app - only `web` needs it.
from django.apps import AppConfig


class CompanionLedgerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wger.companion_ledger'
    label = 'companion_ledger'
