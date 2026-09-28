# -*- coding: utf-8 -*-

# wger-companion S-15/S-16 - coin shop foundation + server-side purchase/
# consumption ledger. See wger-companion's own SPEC_STUBS.md S-15/S-16 for
# the full design and the owner decisions this implements:
# - ledger lives here, in-fork, not a standalone service (S-16 A1)
# - server validates balance and rejects overspend (S-16 A2)
# - spentCopper is purely ledger-derived, never a local increment (S-15 A1)
# - one unified item model across curated/personal/trainer_consumable
#   kinds (S-15 A3) - curated items are NOT stored here, they stay in the
#   SPA's static shopCatalog.ts; only the two genuinely dynamic kinds
#   (user- and trainer/manager-defined) need a real table.
import uuid

from django.conf import settings
from django.db import models


class ItemDefinition(models.Model):
    """A user- or trainer/manager-defined purchasable item (S-21, S-24,
    S-25). Curated (app-owner) items are a static list in the SPA and never
    get a row here - kind is deliberately restricted to the two dynamic
    ones."""

    class Kind(models.TextChoices):
        PERSONAL = 'personal', 'Personal'
        TRAINER_CONSUMABLE = 'trainer_consumable', 'Trainer-consumable'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    name = models.CharField(max_length=200)
    price_copper = models.PositiveIntegerField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='companion_item_definitions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'companion_ledger'


class LedgerEntry(models.Model):
    """Append-only purchase/consumption record. `id` is client-generated
    (a UUID minted at the moment "buy"/"use" is tapped) and doubles as the
    idempotency key: a retried write with the same id must return the
    existing row rather than double-charging - enforced by this being the
    primary key, not a separate unique constraint. `item_key` is either a
    curated item's static key (from the SPA's shopCatalog.ts) or an
    ItemDefinition.id - deliberately a plain string, not a FK, since it can
    point at either.

    `user`/`identity` are always resolved server-side from the
    authenticated request, never trusted from the request body - that's
    what makes "server validates balance server-side" actually true."""

    class Kind(models.TextChoices):
        PURCHASE = 'purchase', 'Purchase'
        CONSUME = 'consume', 'Consume'

    id = models.UUIDField(primary_key=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='companion_ledger_entries')
    kind = models.CharField(max_length=16, choices=Kind.choices)
    item_key = models.CharField(max_length=200)
    cost_copper = models.PositiveIntegerField()
    at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(null=True, blank=True)

    class Meta:
        app_label = 'companion_ledger'
        indexes = [
            models.Index(fields=['user', 'kind']),
        ]
