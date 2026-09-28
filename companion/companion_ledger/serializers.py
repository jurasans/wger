# -*- coding: utf-8 -*-
from rest_framework import serializers

from .models import LedgerEntry


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        # `user` deliberately excluded - identity is implicit from the
        # authenticated request, never exposed/echoed back to the client.
        fields = ['id', 'kind', 'item_key', 'cost_copper', 'at', 'meta']
