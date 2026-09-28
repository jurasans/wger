# -*- coding: utf-8 -*-

# Imported and concatenated onto companion_api.py's own urlpatterns, same
# as companion_ledger's urls_fragment.py.
from django.urls import path

from . import views

urlpatterns = [
    path('api/v2/gym/economy/', views.gym_economy, name='gym_economy'),
    path('api/v2/gym/checkin-items/', views.gym_checkin_items, name='gym_checkin_items'),
    path('api/v2/gym/checkin-items/<uuid:item_id>/', views.gym_checkin_item_detail, name='gym_checkin_item_detail'),
    path(
        'api/v2/gym/checkin-items/<uuid:item_id>/opt-out/',
        views.gym_checkin_item_opt_out,
        name='gym_checkin_item_opt_out',
    ),
]
