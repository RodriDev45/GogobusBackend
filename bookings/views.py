# bookings/views.py
from rest_framework import status, permissions, viewsets, decorators
from django.db import transaction
from .models import Booking, BookingPassenger
from trips.models import Trip
from .serializers import BookingSerializer
from utils.responses import success_response, error_response
from utils.pagination import CustomPagination

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        - Si el usuario es admin, puede ver todos los bookings.
        - Si no, solo los suyos.
        - Admite filtros por status, trip y user (solo admin).
        """
        user = self.request.user
        queryset = Booking.objects.all() if user.is_staff else Booking.objects.filter(user=user)

        # --- Filtrado dinámico ---
        status_param = self.request.query_params.get("status")
        trip_param = self.request.query_params.get("trip")
        user_param = self.request.query_params.get("user")

        if status_param:
            queryset = queryset.filter(status=status_param.upper())

        if trip_param:
            queryset = queryset.filter(trip_id=trip_param)

        # Solo admin puede filtrar por usuario
        if user.is_staff and user_param:
            queryset = queryset.filter(user_id=user_param)

        return queryset.order_by("-created_at")

    def list(self, request, *args, **kwargs):
        """
        Lista de reservas con paginación y filtros aplicados.
        """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data, "Reservas obtenidas correctamente")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data, "Reserva obtenida")
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            trip_id = request.data.get("trip")
            passengers_data = request.data.get("passengers", [])

            # --- Validaciones básicas ---
            if not trip_id or not passengers_data:
                return error_response("Debes enviar el ID del viaje y los pasajeros")

            if len(passengers_data) == 0:
                return error_response("Debe haber al menos un pasajero en la reserva")

            # --- Validar existencia del viaje ---
            try:
                trip = Trip.objects.get(id=trip_id)
            except Trip.DoesNotExist:
                return error_response("El viaje especificado no existe")

            # --- Validar asientos duplicados en el mismo request ---
            seat_numbers = [p.get("seat_number") for p in passengers_data]
            if len(seat_numbers) != len(set(seat_numbers)):
                return error_response("Hay asientos duplicados en la solicitud")

            # --- Validar asientos ya ocupados en otras reservas ---
            taken_seats = BookingPassenger.objects.filter(
                booking__trip_id=trip_id,
                seat_number__in=seat_numbers
            ).values_list("seat_number", flat=True)

            if taken_seats.exists():
                return error_response(
                    f"Los asientos {', '.join(map(str, taken_seats))} ya están reservados"
                )

            # --- Calcular total ---
            total_amount = trip.price * len(passengers_data)

            # --- Crear la reserva principal ---
            booking = Booking.objects.create(
                user=request.user,
                trip=trip,
                total_amount=total_amount
            )

            # --- Crear los pasajeros asociados ---
            passengers = []
            for p in passengers_data:
                passenger = BookingPassenger.objects.create(
                    booking=booking,
                    full_name=p.get("full_name"),
                    dni=p.get("dni"),
                    seat_number=p.get("seat_number"),
                )
                passengers.append({
                    "id": passenger.id,
                    "full_name": passenger.full_name,
                    "dni": passenger.dni,
                    "seat_number": passenger.seat_number,
                })

            serializer = self.get_serializer(booking)
            booking_data = serializer.data
            booking_data["passengers"] = passengers
            booking_data["total_amount"] = float(total_amount)

            return success_response(
                booking_data,
                "Reserva creada correctamente",
                status.HTTP_201_CREATED
            )

        except Exception as e:
            return error_response("Error al crear la reserva", str(e))

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        try:
            booking = self.get_object()

            # No se puede modificar si ya fue pagada
            if booking.status != Booking.Status.PENDING:
                return error_response("Solo puedes modificar reservas pendientes")

            trip_id = request.data.get("trip", booking.trip_id)
            passengers_data = request.data.get("passengers", [])

            # Validar que haya pasajeros
            if not passengers_data:
                return error_response("Debes enviar al menos un pasajero para actualizar")

            # Validar que el viaje exista
            try:
                trip = Trip.objects.get(id=trip_id)
            except Trip.DoesNotExist:
                return error_response("El viaje especificado no existe")

            # Validar asientos duplicados
            seat_numbers = [p.get("seat_number") for p in passengers_data]
            if len(seat_numbers) != len(set(seat_numbers)):
                return error_response("Hay asientos duplicados en la solicitud")

            # Validar asientos ya ocupados por otras reservas
            taken_seats = BookingPassenger.objects.filter(
                booking__trip_id=trip_id,
                seat_number__in=seat_numbers
            ).exclude(booking=booking).values_list("seat_number", flat=True)

            if taken_seats.exists():
                return error_response(
                    f"Los asientos {', '.join(map(str, taken_seats))} ya están reservados"
                )

            # Eliminar pasajeros antiguos y crear nuevos
            booking.passengers.all().delete()

            for p in passengers_data:
                BookingPassenger.objects.create(
                    booking=booking,
                    full_name=p.get("full_name"),
                    dni=p.get("dni"),
                    seat_number=p.get("seat_number"),
                )

            # Actualizar total
            booking.total_amount = trip.price * len(passengers_data)
            booking.trip = trip
            booking.save()

            serializer = self.get_serializer(booking)
            booking_data = serializer.data
            booking_data["passengers"] = passengers_data
            booking_data["total_amount"] = float(booking.total_amount)

            return success_response(booking_data, "Reserva actualizada correctamente")

        except Exception as e:
            return error_response("Error al actualizar la reserva", str(e))
        

    @transaction.atomic
    @decorators.action(detail=True, methods=["patch"], url_path="cancel")
    def cancel_booking(self, request, pk=None):
        try:
            booking = self.get_object()

            # Solo se pueden cancelar reservas pendientes
            if booking.status == Booking.Status.CANCELLED:
                return error_response("Esta reserva ya fue cancelada")

            if booking.status == Booking.Status.PAID:
                return error_response("No puedes cancelar una reserva ya pagada")

            # Cambiar estado
            booking.status = Booking.Status.CANCELLED
            booking.save()

            # (Opcional) Aquí podrías liberar asientos en otro modelo si existiera
            # pero en este diseño, los asientos se controlan solo desde BookingPassenger

            return success_response(
                message="Reserva cancelada correctamente",
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response("Error al cancelar la reserva", str(e))
        
    def destroy(self, request, *args, **kwargs):
        booking = self.get_object()
        booking.delete()
        return success_response(message="Reserva eliminada", status_code=status.HTTP_204_NO_CONTENT)
