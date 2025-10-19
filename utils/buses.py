# utils/buses.py
from buses.models import Seat

def generar_asientos(bus):
    """
    Genera los asientos del bus según la configuración JSON layout_config.
    """
    layout = bus.layout_config or {}

    if not layout:
        raise ValueError("El bus no tiene definida una configuración de asientos (layout_config).")

    seat_number = 1
    for fila_str, columnas in layout.items():
        fila = int(fila_str)
        for columna, tipo_letra in enumerate(columnas, start=1):
            if tipo_letra == "_":  # Ejemplo: guion bajo = espacio vacío
                continue

            tipo = {
                "W": "ventana",
                "A": "pasillo",
                "M": "medio",
            }.get(tipo_letra, "medio")

            Seat.objects.create(
                bus=bus,
                number=seat_number,
                row=fila,
                column=columna,
                position=tipo
            )
            seat_number += 1

