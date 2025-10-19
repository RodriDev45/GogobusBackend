from django.db import models


# Create your models here.
class Bus(models.Model):
    placa = models.CharField(max_length=10, unique=True)  # Ej: ABC-123
    modelo = models.CharField(max_length=100)             # Ej: Mercedes-Benz
    capacidad = models.PositiveIntegerField()             # Número de asientos
    layout_config = models.JSONField(default=dict, blank=True)  
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.placa} - {self.modelo}"
    
class Seat(models.Model):
    POSITION_CHOICES = [
        ("window", "Ventana"),
        ("aisle", "Pasillo"),
        ("middle", "Centro"),
    ]

    bus = models.ForeignKey(Bus, related_name="seats", on_delete=models.CASCADE)
    number = models.PositiveIntegerField()  # Ej: 1, 2, 3...
    row = models.PositiveIntegerField()     # Fila en el bus (opcional)
    column = models.PositiveIntegerField()  # Columna en el bus (opcional)
    position = models.CharField(max_length=10, choices=POSITION_CHOICES)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('bus', 'number')
        ordering = ['number']

    def __str__(self):
        return f"Asiento {self.number} ({self.get_position_display()}) - {self.bus.placa}"