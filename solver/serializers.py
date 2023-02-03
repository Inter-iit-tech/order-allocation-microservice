from django.conf import settings
from rest_framework import serializers
from datetime import timedelta
from solver.models import (
    Point,
    Order,
    Package,
    Vehicle,
    Depot,
    RiderStartMeta,
    RiderUpdateMeta,
    TourStop,
    StartDayMeta,
    AddPickupMeta,
)


DEFAULT_START_TIME = settings.OPTIRIDER_SETTINGS["CONSTANTS"]["GLOBAL_START_TIME"]


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


class OrderSerializer(serializers.Serializer):
    id = serializers.CharField(trim_whitespace=False)
    orderType = serializers.ChoiceField(choices=["delivery", "pickup"])
    point = PointSerializer()
    expectedTime = serializers.DurationField(min_value=timedelta())
    package = PackageSerializer()
    serviceTime = serializers.DurationField(default=timedelta(), min_value=timedelta())

    def create(self, validated_data):
        return Order(**validated_data)

    def update(self, instance, validated_data):
        instance.id = validated_data.get("id", instance.id)
        instance.orderType = validated_data.get("orderType", instance.orderType)
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


class TourStopSerializer(serializers.Serializer):
    orderId = serializers.CharField(trim_whitespace=False)
    timing = serializers.DurationField(min_value=timedelta())

    def create(self, validated_data):
        return TourStop(**validated_data)

    def update(self, instance, validated_data):
        instance.orderId = validated_data.get("orderId", instance.orderId)
        instance.timing = validated_data.get("timing", instance.timing)
        return instance


class RiderStartMetaSerializer(serializers.Serializer):
    id = serializers.CharField(trim_whitespace=False)
    vehicle = VehicleSerializer()
    startTime = serializers.DurationField(
        min_value=timedelta(), default=DEFAULT_START_TIME
    )
    tours = serializers.ListField(child=TourStopSerializer(many=True), read_only=True)

    def create(self, validated_data):
        return RiderStartMeta(**validated_data)

    def update(self, instance, validated_data):
        instance.id = validated_data.get("id", instance.id)
        if "vehicle" in validated_data:
            instance.vehicle = Vehicle(**validated_data["vehicle"])
        instance.startTime = validated_data.get("startTime", instance.startTime)
        return instance


class RiderUpdateMetaSerializer(serializers.Serializer):
    id = serializers.CharField(trim_whitespace=False)
    vehicle = VehicleSerializer()
    tours = serializers.ListField(child=TourStopSerializer(many=True))
    headingTo = serializers.CharField(trim_whitespace=False, required=False)
    updatedCurrentTour = serializers.BooleanField(read_only=True)

    def create(self, validated_data):
        return RiderUpdateMeta(**validated_data)

    def update(self, instance, validated_data):
        instance.id = validated_data.get("id", instance.id)
        if "vehicle" in validated_data:
            instance.vehicle = Vehicle(**validated_data["vehicle"])
        if "tours" in validated_data:
            instance.tours = [
                [TourStop(**stop) for stop in tour] for tour in validated_data["tours"]
            ]
        instance.headingTo = validated_data.get("headingTo", instance.headingTo)
        return instance


class DepotSerializer(serializers.Serializer):
    id = serializers.CharField(trim_whitespace=False)
    point = PointSerializer()

    def create(self, validated_data):
        return Depot(**validated_data)

    def update(self, instance, validated_data):
        instance.id = validated_data.get("id", instance.id)
        if "point" in validated_data:
            instance.point = Point(**validated_data["point"])
        return instance


class StartDaySerializer(serializers.Serializer):
    riders = RiderStartMetaSerializer(many=True)
    orders = OrderSerializer(many=True)
    depot = DepotSerializer()

    def create(self, validated_data):
        return StartDayMeta(**validated_data)

    def update(self, instance, validated_data):
        return instance


class AddPickupSerializer(serializers.Serializer):
    riders = RiderUpdateMetaSerializer(many=True)
    orders = OrderSerializer(many=True)
    depot = DepotSerializer()
    newOrder = OrderSerializer(write_only=True)

    def create(self, validated_data):
        return AddPickupMeta(**validated_data)

    def update(self, instance, validated_data):
        return instance
