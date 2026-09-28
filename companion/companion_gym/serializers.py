# -*- coding: utf-8 -*-
from rest_framework import serializers

from .models import GymCheckInItem, GymEconomyOverride


class GymEconomyOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymEconomyOverride
        fields = ['section', 'key', 'value']


class GymCheckInItemSerializer(serializers.ModelSerializer):
    opted_out = serializers.SerializerMethodField()

    class Meta:
        model = GymCheckInItem
        fields = ['id', 'kind', 'name', 'unit', 'value_type', 'order', 'opted_out']

    def get_opted_out(self, obj) -> bool:
        # Annotated onto each row by the view (a per-user set of opted-out
        # item ids) rather than a query per row here.
        return obj.id in self.context.get('opted_out_ids', set())
