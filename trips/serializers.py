from rest_framework import serializers
from .models import Location, Trip
from buses.models import Bus
from bookings.models import BookingPassenger
from buses.serializers import BusDetailSerializer

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


class TripDetailSerializer(serializers.ModelSerializer):
    origin = serializers.StringRelatedField()
    destination = serializers.StringRelatedField()
    bus = BusDetailSerializer(read_only=True)
    occupied_seats = serializers.SerializerMethodField()
    available_seats = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            "id",
            "origin",
            "destination",
            "departure_time",
            "arrival_time",
            "price",
            "bus",
            "occupied_seats",
            "available_seats",
        ]

    def get_occupied_seats(self, obj):
        """Devuelve los números de asientos ocupados en este trip"""
        # Obtiene todos los pasajeros de las reservas asociadas a este trip
        passengers = BookingPassenger.objects.filter(
            booking__trip=obj,
            booking__status__in=["PENDING", "PAID"]  # consideramos ambos estados
        ).values_list("seat_number", flat=True)
        return list(passengers)

    def get_available_seats(self, obj):
        """Devuelve los asientos disponibles del bus"""
        total_seats = obj.bus.seats.values_list("number", flat=True)
        occupied = set(self.get_occupied_seats(obj))
        available = [num for num in total_seats if num not in occupied]
        return available