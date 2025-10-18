# bookings/serializers.py
from rest_framework import serializers
from .models import Booking, BookingPassenger

class BookingPassengerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingPassenger
        fields = "__all__"

class BookingSerializer(serializers.ModelSerializer):
    passengers = BookingPassengerSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = "__all__"
