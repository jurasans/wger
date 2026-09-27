# -*- coding: utf-8 -*-

# Activates the companion-app trainer-mode endpoints (SPEC.md §14am) without
# touching the image's own settings/main.py. Only overrides ROOT_URLCONF to
# point at wger.companion_api, a brand-new module (see patches/companion_api.py)
# that only *adds* routes on top of the image's own wger.urls rather than
# replacing it - so nothing here needs updating when the base image's real
# settings.main or urls.py change.
#
# Mounted into the container as settings/companion.py and activated via
# DJANGO_SETTINGS_MODULE=settings.companion (set only for the `web` service
# in docker-compose.override.yml; celery keeps the image's default
# settings.main since it never serves these routes).

# wger
from .main import *  # noqa: F401,F403

ROOT_URLCONF = 'wger.companion_api'
