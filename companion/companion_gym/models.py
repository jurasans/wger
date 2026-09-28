# -*- coding: utf-8 -*-

# wger-companion S-25/S-37. Gated by wger's own existing gym.manage_gym
# permission - no new role (confirmed: wger already has a built-in gym
# manager permission, use it directly).
import uuid

from django.conf import settings
from django.db import models

from wger.gym.models import Gym


class GymEconomyOverride(models.Model):
    """S-37 - per-gym override of one economy.csv key. A gym with no rows
    here uses the app-wide defaults (economy.generated.ts) unchanged - this
    table only ever holds what a manager actually changed, so "migration"
    is just this table existing, not backfilling every gym. `section`/`key`
    mirror economy.csv's own columns exactly (currency/earn/streak/level/
    badge/policy); `value` stays a string, same as the CSV - the SPA parses
    it per its own per-section type rules (economyCodegen.mjs), this table
    doesn't need to know bool vs int vs enum."""

    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='economy_overrides')
    section = models.CharField(max_length=32)
    key = models.CharField(max_length=64)
    value = models.CharField(max_length=200)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'companion_gym'
        unique_together = [('gym', 'section', 'key')]


class GymCheckInItem(models.Model):
    """S-25 - a gym-manager-defined pre/post-workout or daily/bi-weekly
    check-in item. Every answer upserts into ONE wger measurement metric
    named after the item (confirmed: one metric per item, manager sets
    unit/value_type when defining it)."""

    class Kind(models.TextChoices):
        PRE = 'pre', 'Pre-workout'
        POST = 'post', 'Post-workout'
        DAILY = 'daily', 'Daily'
        BIWEEKLY = 'biweekly', 'Bi-weekly'

    class ValueType(models.TextChoices):
        NUMBER = 'number', 'Number'
        SCALE_1_5 = 'scale_1_5', '1-5 scale'
        YES_NO = 'yes_no', 'Yes/No'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='checkin_items')
    kind = models.CharField(max_length=16, choices=Kind.choices)
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=32, blank=True)
    value_type = models.CharField(max_length=16, choices=ValueType.choices)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'companion_gym'
        ordering = ['kind', 'order', 'created_at']


class MemberItemOptOut(models.Model):
    """S-25 - a member opting out of one specific gym check-in item.
    All-at-once opt-out is derived client-side (opted out of every item
    currently returned for the gym), not a separate flag - keeps this
    table the single source of truth with no risk of the two disagreeing."""

    item = models.ForeignKey(GymCheckInItem, on_delete=models.CASCADE, related_name='opt_outs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='companion_checkin_opt_outs')

    class Meta:
        app_label = 'companion_gym'
        unique_together = [('item', 'user')]
