# -*- coding: utf-8 -*-

# wger-companion S-15/S-16. Mirrors companion_api.py's own style (plain
# @api_view function views, no DRF viewsets/routers) - identity is always
# request.user, resolved server-side from the authenticated JWT, never
# trusted from the request body. That's also what makes "server validates
# balance server-side" actually true rather than just documented (S-16 A2).
#
# A trainer acting on a member's behalf (S-24's not-yet-built
# trainer-consume flow) must go through trainer-login-as first, same as
# every other on-behalf-of write in this app (trainerSlice.ts's
# selectMember()) - request.user is then genuinely the member, so these
# views need no separate on-behalf-of branch at all.
import uuid

from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import LedgerEntry
from .serializers import LedgerEntrySerializer


def _spent_copper(user) -> int:
    return LedgerEntry.objects.filter(user=user, kind=LedgerEntry.Kind.PURCHASE).aggregate(total=Sum('cost_copper'))[
        'total'
    ] or 0


def _parse_entry_id(raw):
    try:
        return uuid.UUID(str(raw))
    except (TypeError, ValueError):
        return None


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ledger_purchase(request):
    """Idempotent by `id` (client-generated) - insert-or-return-existing,
    never a second row for a retried request. Rejects overspend: the
    client's own lifetime_copper (its client-derived earned total) minus
    this identity's already-spent total (summed from THIS table, not
    client-supplied) must cover cost_copper."""
    entry_id = _parse_entry_id(request.data.get('id'))
    item_key = request.data.get('item_key')
    cost_copper = request.data.get('cost_copper')
    lifetime_copper = request.data.get('lifetime_copper')
    if entry_id is None or not item_key or cost_copper is None or lifetime_copper is None:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    existing = LedgerEntry.objects.filter(id=entry_id).first()
    if existing:
        if existing.user_id != request.user.id:
            # Same id, different user - either a UUID collision or a bug on
            # the caller's side; never hand back someone else's entry.
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(LedgerEntrySerializer(existing).data)

    try:
        cost_copper = int(cost_copper)
        lifetime_copper = int(lifetime_copper)
    except (TypeError, ValueError):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    if lifetime_copper - _spent_copper(request.user) < cost_copper:
        return Response({'detail': 'insufficient_balance'}, status=status.HTTP_402_PAYMENT_REQUIRED)

    entry = LedgerEntry.objects.create(
        id=entry_id,
        user=request.user,
        kind=LedgerEntry.Kind.PURCHASE,
        item_key=item_key,
        cost_copper=cost_copper,
        meta=request.data.get('meta') if isinstance(request.data.get('meta'), dict) else None,
    )
    return Response(LedgerEntrySerializer(entry).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ledger_consume(request):
    """Same idempotent-by-id shape as purchase. No balance check - consuming
    an already-owned item doesn't spend coins again. Full redemption
    semantics (matching against an unconsumed purchase) are S-24/S-25's to
    build when their trainer-consume UI lands; only the `kind` distinction
    needs to exist today."""
    entry_id = _parse_entry_id(request.data.get('id'))
    item_key = request.data.get('item_key')
    if entry_id is None or not item_key:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    existing = LedgerEntry.objects.filter(id=entry_id).first()
    if existing:
        if existing.user_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(LedgerEntrySerializer(existing).data)

    entry = LedgerEntry.objects.create(
        id=entry_id,
        user=request.user,
        kind=LedgerEntry.Kind.CONSUME,
        item_key=item_key,
        cost_copper=0,
        meta=request.data.get('meta') if isinstance(request.data.get('meta'), dict) else None,
    )
    return Response(LedgerEntrySerializer(entry).data)


@api_view()
@permission_classes([IsAuthenticated])
def ledger_balance(request):
    return Response({'spent_copper': _spent_copper(request.user)})


@api_view()
@permission_classes([IsAuthenticated])
def ledger_inventory(request):
    entries = LedgerEntry.objects.filter(user=request.user).order_by('-at')
    paginator = LimitOffsetPagination()
    page = paginator.paginate_queryset(entries, request)
    return paginator.get_paginated_response(LedgerEntrySerializer(page, many=True).data)
