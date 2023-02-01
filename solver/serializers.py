from rest_framework import serializers
from datetime import timedelta
from solver.models import (
    Point,
    Consignment,
    Package,
    Vehicle,
    RiderMeta,
    TourStop,
    StartDay,
)


class PointSerializer(serializers.Serializer):
    longitude = serializers.FloatField(min_value=-180.0, max_value=180.0)
    latitude = serializers.FloatField(min_value=-90.0, max_value=90.0)

    def create(self, validated_data):
        return Point(**validated_data)

    def update(self, instance, validated_data):
        instance.longitude = validated_data.get("longitude", instance.longitude)
        instance.latitude = validated_data.get("latitude", instance.latitude)
        instance.coords = instance.get_coords()
        return instance


class PackageSerializer(serializers.Serializer):
    volume = serializers.IntegerField(min_value=0)

    def update(self, instance, validated_data):
        instance.volume = validated_data.get("volume", instance.volume)
        return instance

    def create(self, validated_data):
        return Package(**validated_data)


class ConsignmentSerializer(serializers.Serializer):
    consignmentType = serializers.ChoiceField(choices=["delivery", "pickup"])
    point = PointSerializer()
    expectedTime = serializers.DurationField(min_value=timedelta())
    package = PackageSerializer()
    serviceTime = serializers.DurationField(default=timedelta(), min_value=timedelta())

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
    startTime = serializers.DurationField(min_value=timedelta())

    def create(self, validated_data):
        return RiderMeta(**validated_data)

    def update(self, instance, validated_data):
        if "vehicle" in validated_data:
            instance.vehicle = Vehicle(**validated_data["vehicle"])
        instance.startTime = validated_data.get("startTime", instance.startTime)


class TourStopSerializer(serializers.Serializer):
    locationIndex = serializers.IntegerField(min_value=0)
    timing = serializers.DurationField(min_value=timedelta())

    def create(self, validated_data):
        return TourStop(**validated_data)

    def update(self, instance, validated_data):
        instance.locationIndex = validated_data.get(
            "locationIndex", instance.locationIndex
        )
        instance.timing = validated_data.get("timing", instance.timing)


class StartDaySerializer(serializers.Serializer):
    riders = serializers.ListField(child=RiderMetaSerializer(), min_length=1)
    consignments = serializers.ListField(child=ConsignmentSerializer())
    depotPoint = PointSerializer()
    tours = serializers.ListField(
        child=serializers.ListField(
            child=serializers.ListField(child=TourStopSerializer())
        ),
        read_only=True,
    )

    def create(self, validated_data):
        return StartDay(**validated_data)

    def update(self, instance, validated_data):
        return instance
