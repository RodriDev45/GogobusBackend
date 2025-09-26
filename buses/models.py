from django.db import models

# Create your models here.
class Bus(models.Model):
    placa = models.CharField(max_length=10, unique=True)  # Ej: ABC-123
    modelo = models.CharField(max_length=100)             # Ej: Mercedes-Benz
    capacidad = models.PositiveIntegerField()             # Número de asientos
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.placa} - {self.modelo}"