from rest_framework import serializers
from .models import Location, Trip
from buses.models import Bus 


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = "__all__"


class TripSerializer(serializers.ModelSerializer):
    origin = LocationSerializer(read_only=True)
    destination = LocationSerializer(read_only=True)
    bus = serializers.StringRelatedField(read_only=True)

    origin_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source="origin", write_only=True
    )
    destination_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source="destination", write_only=True
    )
    bus_id = serializers.PrimaryKeyRelatedField(
        queryset=Bus.objects.all(), source="bus", write_only=True
    )

    class Meta:
        model = Trip
        fields = [
            "id",
            "bus",
            "bus_id",
            "origin",
            "origin_id",
            "destination",
            "destination_id",
            "departure_time",
            "arrival_time",
            "price",
            "created_at",
        ]
