# -*- coding: utf-8 -*-

# wger-companion S-25/S-37 - gym-manager-configurable economy overrides and
# custom pre/post-workout + daily/bi-weekly check-in items. Same pattern as
# companion_ledger (see its apps.py) - registered via INSTALLED_APPS in
# settings/companion.py, only loaded for `web`.
from django.apps import AppConfig


class CompanionGymConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wger.companion_gym'
    label = 'companion_gym'
