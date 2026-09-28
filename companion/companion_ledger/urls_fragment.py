# -*- coding: utf-8 -*-

# Imported and concatenated onto companion_api.py's own urlpatterns, which
# stays the ONE urlconf module (ROOT_URLCONF=wger.companion_api) - this
# file is never its own urlconf.
#
# No gym-scoped read endpoint yet (S-24's trainer view of members'
# trainer-consumable items) - nothing calls it until that stub is actually
# designed/enabled, and the permission/gym-scoping shape it'd need
# (has_perm + is_same_gym, same as trainer_gym_members) is already proven
# elsewhere in this fork, so there's nothing to spike by adding it early.
from django.urls import path

from . import views

urlpatterns = [
    path('api/v2/ledger/purchase/', views.ledger_purchase, name='ledger_purchase'),
    path('api/v2/ledger/consume/', views.ledger_consume, name='ledger_consume'),
    path('api/v2/ledger/balance/', views.ledger_balance, name='ledger_balance'),
    path('api/v2/ledger/inventory/', views.ledger_inventory, name='ledger_inventory'),
]
