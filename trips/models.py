from django.db import models

# Create your models here.
class Location(models.Model):
    name = models.CharField(max_length=100)  # Ej: "Lima"
    terminal = models.CharField(max_length=150, blank=True, null=True)  # Ej: "Plaza Norte"
    address = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.terminal}" if self.terminal else self.name


class Trip(models.Model):
    bus = models.ForeignKey("buses.Bus", on_delete=models.CASCADE, related_name="trips")

    origin = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="trips_origin"
    )
    destination = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="trips_destination"
    )

    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.origin} → {self.destination} | {self.departure_time.strftime('%d-%m-%Y %H:%M')}"