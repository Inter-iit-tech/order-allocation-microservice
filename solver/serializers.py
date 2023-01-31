from rest_framework import serializers
from datetime import timedelta
from drf_extra_fields.geo_fields import PointField
from solver.models import Consignment, Package, Vehicle, RiderMeta


class PackageSerializer(serializers.Serializer):
    volume = serializers.FloatField(min_value=0.0)

    def update(self, instance, validated_data):
        instance.volume = validated_data.get("volume", instance.volume)
        return instance

    def create(self, validated_data):
        return Package(**validated_data)


class ConsignmentSerializer(serializers.Serializer):
    consignmentType = serializers.ChoiceField(choices=["delivery", "pickup"])
    point = PointField()
    expectedTime = serializers.DateTimeField()
    package = PackageSerializer()
    serviceTime = serializers.DurationField(default=timedelta())

    def create(self, validated_data):
        return Consignment(**validated_data)

    def update(self, instance, validated_data):
        instance.consignment_type = validated_data.get(
            "consignmentType", instance.consignment_type
        )
        instance.point = validated_data.get("point", instance.point)
        instance.expected_time = validated_data.get(
            "expectedTime", instance.expected_time
        )
        if "package" in validated_data:
            instance.package = Package(**validated_data["package"])
        instance.service_time = validated_data.get("serviceTime", instance.service_time)
        return instance


class VehicleSerializer(serializers.Serializer):
    capacity = serializers.FloatField(min_value=0.0)

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
        instance.start_time = validated_data.get("startTime", instance.start_time)
