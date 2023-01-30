from rest_framework import serializers
from drf_extra_fields.geo_fields import PointField
from solver.models import Consignment, Package


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
        return instance
