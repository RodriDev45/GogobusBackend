from rest_framework import serializers
from .models import Bus, Seat

class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = '__all__'

class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ["number", "row", "column", "position"]


class BusDetailSerializer(serializers.ModelSerializer):
    seats = serializers.SerializerMethodField()

    class Meta:
        model = Bus
        fields = ["id", "placa", "modelo", "capacidad", "layout_config", "seats"]

    def get_seats(self, obj):
        seats = obj.seats.all().order_by("row", "column")
        result = {}
        for seat in seats:
            result.setdefault(seat.row, []).append({
                "number": seat.number,
                "column": seat.column,
                "position": seat.position
            })
        return result
    
class BusSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = ["id", "modelo", "placa", "capacidad"]
