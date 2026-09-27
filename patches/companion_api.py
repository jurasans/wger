# -*- coding: utf-8 -*-

# SPEC.md §14am (wger-companion) - trainer-mode API additions for this
# deployment, kept entirely OUTSIDE the upstream source tree.
#
# This is a brand-new module, mounted into the container at
# wger/companion_api.py (see docker-compose.override.yml) - it never
# replaces or overlays wger/urls.py or wger/core/api/views.py. It only
# imports their live urlpatterns/helpers as the image ships them and
# appends two routes on top. That means a wger image upgrade never
# requires regenerating anything here: whatever the new image's urls.py
# already contains keeps working unmodified, and only these two extra
# endpoints get stapled on.
#
# Activated by ROOT_URLCONF=wger.companion_api, set in
# settings/companion.py (itself only imported when
# DJANGO_SETTINGS_MODULE=settings.companion, set for the `web` service in
# docker-compose.override.yml).

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.urls import path

# Third Party
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# wger
from wger.gym.helpers import is_same_gym
from wger.gym.models import Gym
from wger.urls import urlpatterns as _base_urlpatterns
from wger.utils.headless_long_lived import mint_long_lived_refresh_token


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trainer_login_as(request, user_id):
    """
    Mints a real headless JWT refresh token for another user, on behalf of a
    trainer/gym-manager - for the companion app's trainer mode (SPEC.md
    §14am). Deliberately NOT the session-swap `trainer_login` view
    (core/views/user.py) - that's a plain Django view gated by a session
    cookie the companion app's JWT-only client never establishes, and its
    own handoff (app_auth_handoff) redirects to a custom `wger://` URL
    scheme meant for the native app to intercept, which a browser tab can't
    catch. This stays entirely in the JSON API layer the companion app
    already speaks (authenticated by the SAME JWT it already holds - DRF's
    IsAuthenticated is enough, HeadlessJWTAuthentication is already wired
    into DEFAULT_AUTHENTICATION_CLASSES), reusing the exact same
    permission/scoping checks trainer_login already enforces so a trainer
    gets no more access here than they already have through wger's own UI.

    Mirrors the old issue_refresh_token (removed upstream in 2.7) - same
    mint call, just for a different, permission-checked target user instead
    of request.user.
    """
    if not (
        request.user.has_perm('gym.gym_trainer')
        or request.user.has_perm('gym.manage_gym')
        or request.user.has_perm('gym.manage_gyms')
    ):
        return Response(status=status.HTTP_403_FORBIDDEN)

    target = get_object_or_404(User, pk=user_id)

    # Same privileged-account guard as trainer_login: a trainer can view a
    # regular member, never another trainer/manager account.
    if (
        target.has_perm('gym.gym_trainer')
        or target.has_perm('gym.manage_gym')
        or target.has_perm('gym.manage_gyms')
    ):
        return Response(status=status.HTTP_403_FORBIDDEN)

    # Same gym-scoping as trainer_login/UserDetailView - 404, not 403, so
    # this doesn't leak whether a user id exists in a gym you can't see.
    if not request.user.has_perm('gym.manage_gyms') and not is_same_gym(request.user, target):
        return Response(status=status.HTTP_404_NOT_FOUND)

    refresh_token = mint_long_lived_refresh_token(
        target,
        settings.HEADLESS_JWT_REFRESH_TOKEN_EXPIRES_IN,
    )
    return Response({'refresh_token': refresh_token, 'user_id': target.id, 'username': target.username})


@api_view()
@permission_classes([IsAuthenticated])
def trainer_gym_members(request):
    """
    JSON member list for the companion app's trainer-mode picker (SPEC.md
    §14am). Reuses Gym.objects.get_members() directly - the exact same
    queryset GymUserListView (gym/views/gym.py) already renders as HTML at
    /en/gym/<pk>/members. That page was the original plan (scrape it
    instead of adding an endpoint), but this deployment's reverse proxy
    only forwards /api/ and /allauth/ to wger - /en/gym/... isn't reachable
    from the companion app's own origin at all, so a real JSON endpoint
    through the SAME proxy that already works is the actual fix, not a
    workaround.

    No gym id param - always the requesting trainer's own gym
    (request.user.userprofile.gym_id), same as GymUserListView's own
    dispatch() check (request.user.userprofile.gym_id == kwargs['pk']) -
    just doesn't need the param since it's the only gym this could ever
    legitimately mean for a non-general-manager.

    Multi-gym trainers explicitly deferred (SPEC.md §14am): UserProfile.gym
    is a single FK, not a set, and is_same_gym() (gym/helpers.py) already
    only ever compares this one field - there IS no second gym to fall back
    to in wger's own data model as it stands, so "fall back to the default
    gym" is already exactly what both this endpoint and trainer_login_as
    do, not a gap to close later. Revisit only if wger's own model ever
    grows real multi-gym membership.
    """
    if not (
        request.user.has_perm('gym.gym_trainer')
        or request.user.has_perm('gym.manage_gym')
        or request.user.has_perm('gym.manage_gyms')
    ):
        return Response(status=status.HTTP_403_FORBIDDEN)

    gym_id = request.user.userprofile.gym_id
    if not gym_id:
        return Response({'members': []})

    members = Gym.objects.get_members(gym_id)
    return Response(
        {
            'members': [
                {'id': u.id, 'username': u.username, 'full_name': u.get_full_name()} for u in members
            ]
        }
    )


urlpatterns = _base_urlpatterns + [
    # SPEC.md §14am - trainer companion mode's token mint, JSON-API-only
    # counterpart to core/views/user.py's session-based trainer_login.
    path(
        'api/v2/trainer/login-as/<int:user_id>/',
        trainer_login_as,
        name='trainer_login_as',
    ),
    # SPEC.md §14am - trainer companion mode's member picker. JSON
    # counterpart to gym/views/gym.py's GymUserListView (/en/gym/<pk>/members)
    # - that page isn't reachable from the companion app's own origin at all
    # (its reverse proxy only forwards /api/ and /allauth/).
    path(
        'api/v2/trainer/members/',
        trainer_gym_members,
        name='trainer_gym_members',
    ),
]
