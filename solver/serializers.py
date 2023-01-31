from rest_framework import serializers
from datetime import timedelta
from drf_extra_fields.geo_fields import PointField
from solver.models import Consignment, Package, Vehicle, RiderMeta, StartDay
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes


@extend_schema_field(OpenApiTypes.OBJECT)
class SpectacularPointField(PointField):
    pass


class PackageSerializer(serializers.Serializer):
    volume = serializers.IntegerField(min_value=0)

    def update(self, instance, validated_data):
        instance.volume = validated_data.get("volume", instance.volume)
        return instance

    def create(self, validated_data):
        return Package(**validated_data)


class ConsignmentSerializer(serializers.Serializer):
    consignmentType = serializers.ChoiceField(choices=["delivery", "pickup"])
    point = SpectacularPointField()
    expectedTime = serializers.DateTimeField()
    package = PackageSerializer()
    serviceTime = serializers.DurationField(default=timedelta())

    def create(self, validated_data):
        return Consignment(**validated_data)

    def update(self, instance, validated_data):
        instance.consignmentType = validated_data.get(
            "consignmentType", instance.consignmentType
        )
        instance.point = validated_data.get("point", instance.point)
        instance.expectedTime = validated_data.get(
            "expectedTime", instance.expectedTime
        )
        if "package" in validated_data:
            instance.package = Package(**validated_data["package"])
        instance.serviceTime = validated_data.get("serviceTime", instance.serviceTime)
        return instance


class VehicleSerializer(serializers.Serializer):
    capacity = serializers.IntegerField(min_value=0)

    def create(self, validated_data):
        return Vehicle(**validated_data)

    def update(self, instance, validated_data):
        instance.capacity = validated_data.get("capacity", instance.capacity)
        return instance


class RiderMetaSerializer(serializers.Serializer):
    vehicle = VehicleSerializer()
    startTime = serializers.DateTimeField()

    def create(self, validated_data):
        return RiderMeta(**validated_data)

    def update(self, instance, validated_data):
        if "vehicle" in validated_data:
            instance.vehicle = Vehicle(**validated_data["vehicle"])
        instance.startTime = validated_data.get("startTime", instance.startTime)


class StartDaySerializer(serializers.Serializer):
    riders = serializers.ListField(child=RiderMetaSerializer(), min_length=1)
    consignments = serializers.ListField(child=ConsignmentSerializer())
    depotPoint = SpectacularPointField()
    tours = serializers.ReadOnlyField()
    timings = serializers.ReadOnlyField()

    def create(self, validated_data):
        return StartDay(**validated_data)

    def update(self, instance, validated_data):
        return instance
