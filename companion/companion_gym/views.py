# -*- coding: utf-8 -*-

# wger-companion S-25/S-37. Same style as companion_api.py/companion_ledger
# - plain @api_view function views, identity always request.user, gym
# always request.user.userprofile.gym_id. Manager-only writes gated on
# wger's own gym.manage_gym permission (confirmed: no new role needed).
import uuid

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import GymCheckInItem, GymEconomyOverride, MemberItemOptOut
from .serializers import GymCheckInItemSerializer, GymEconomyOverrideSerializer


def _is_manager(user) -> bool:
    return user.has_perm('gym.manage_gym') or user.has_perm('gym.manage_gyms')


def _gym_id(request):
    return request.user.userprofile.gym_id


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def gym_economy(request):
    """GET: this identity's gym's override rows (any member - used to merge
    over the app-wide defaults client-side). POST: upsert one {section,
    key, value} row, or delete it by sending value=null - manager only."""
    gym_id = _gym_id(request)
    if not gym_id:
        return Response([])

    if request.method == 'GET':
        overrides = GymEconomyOverride.objects.filter(gym_id=gym_id)
        return Response(GymEconomyOverrideSerializer(overrides, many=True).data)

    if not _is_manager(request.user):
        return Response(status=status.HTTP_403_FORBIDDEN)

    section = request.data.get('section')
    key = request.data.get('key')
    value = request.data.get('value')
    if not section or not key:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    if value is None:
        GymEconomyOverride.objects.filter(gym_id=gym_id, section=section, key=key).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    override, _created = GymEconomyOverride.objects.update_or_create(
        gym_id=gym_id, section=section, key=key, defaults={'value': str(value)}
    )
    return Response(GymEconomyOverrideSerializer(override).data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def gym_checkin_items(request):
    """GET: this gym's check-in items, each with the requesting member's
    own opted_out state. POST: create an item - manager only."""
    gym_id = _gym_id(request)
    if not gym_id:
        return Response([])

    if request.method == 'GET':
        items = GymCheckInItem.objects.filter(gym_id=gym_id)
        opted_out_ids = set(
            MemberItemOptOut.objects.filter(user=request.user, item__gym_id=gym_id).values_list('item_id', flat=True)
        )
        return Response(GymCheckInItemSerializer(items, many=True, context={'opted_out_ids': opted_out_ids}).data)

    if not _is_manager(request.user):
        return Response(status=status.HTTP_403_FORBIDDEN)

    serializer = GymCheckInItemSerializer(data=request.data, context={'opted_out_ids': set()})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    item = GymCheckInItem.objects.create(gym_id=gym_id, **serializer.validated_data)
    return Response(GymCheckInItemSerializer(item, context={'opted_out_ids': set()}).data)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def gym_checkin_item_detail(request, item_id):
    """PATCH: edit name / unit / kind / value_type / order. DELETE: remove.
    Manager only."""
    if not _is_manager(request.user):
        return Response(status=status.HTTP_403_FORBIDDEN)
    item = get_object_or_404(GymCheckInItem, id=item_id, gym_id=_gym_id(request))
    if request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = GymCheckInItemSerializer(item, data=request.data, partial=True, context={'opted_out_ids': set()})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def gym_checkin_item_opt_out(request, item_id):
    """A member's own opt-out toggle - no manager permission needed, this
    only ever touches the requesting user's own row. {opted_out: true|false}."""
    item = get_object_or_404(GymCheckInItem, id=item_id, gym_id=_gym_id(request))
    opted_out = bool(request.data.get('opted_out'))
    if opted_out:
        MemberItemOptOut.objects.get_or_create(item=item, user=request.user)
    else:
        MemberItemOptOut.objects.filter(item=item, user=request.user).delete()
    return Response({'opted_out': opted_out})
