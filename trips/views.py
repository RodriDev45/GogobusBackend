from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import permission_classes
from .models import Location, Trip
from .serializers import LocationSerializer, TripSerializer, TripDetailSerializer
from utils.responses import success_response, error_response
from utils.pagination import CustomPagination
from datetime import datetime

# Create your views here.
# -------------------- LOCATIONS --------------------
class LocationViewSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
    
    def get_queryset(self):
        queryset = Location.objects.all()

        name_param = self.request.query_params.get("name")
        terminal_param = self.request.query_params.get("terminal")
        address_param = self.request.query_params.get("address")
        region_param = self.request.query_params.get("region")

        if name_param:
            queryset = queryset.filter(name__icontains=name_param)
        if terminal_param:
            queryset = queryset.filter(terminal__icontains=terminal_param)
        if address_param:
            queryset = queryset.filter(address__icontains=address_param)
        if region_param:
            queryset = queryset.filter(region__icontains=region_param)

        return queryset.order_by("-created_at")
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data, "Ubicaciones obtenidas correctamente")
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data, "Ubicación obtenida")
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response(serializer.data, "Ubicación creada", status.HTTP_201_CREATED)
        return error_response("Error al crear la ubicación", serializer.errors)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return success_response(serializer.data, "Ubicación actualizada")
        return error_response("Error al actualizar la ubicación", serializer.errors)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="Ubicación eliminada", data=None, status_code=status.HTTP_204_NO_CONTENT)

# -------------------- TRIPS --------------------
class TripViewSet(viewsets.ModelViewSet):
    serializer_class = TripSerializer
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TripDetailSerializer
        return TripSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
    
    def get_queryset(self):
        queryset = Trip.objects.all()

        # --- Parámetros ---
        bus_param = self.request.query_params.get("bus")
        origin_param = self.request.query_params.get("origin")
        destination_param = self.request.query_params.get("destination")
        date_param = self.request.query_params.get("date")
        date_from_param = self.request.query_params.get("date_from")
        date_to_param = self.request.query_params.get("date_to")
        price_param = self.request.query_params.get("price")

        # --- Filtrado por IDs ---
        if bus_param:
            queryset = queryset.filter(bus_id=bus_param)
        if origin_param:
            queryset = queryset.filter(origin_id=origin_param)
        if destination_param:
            queryset = queryset.filter(destination_id=destination_param)

        # --- Helper: detectar formato ---
        def parse_datetime(value):
            """Intenta parsear fecha o fecha-hora en formato ISO."""
            try:
                # formato con hora: 2025-10-18T12:30:00
                return datetime.fromisoformat(value)
            except ValueError:
                try:
                    # solo fecha: 2025-10-18
                    return datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    return None

        # --- Filtrado por fecha/hora ---
        if date_param:
            parsed_date = parse_datetime(date_param)
            if parsed_date:
                queryset = queryset.filter(
                    departure_time__date=parsed_date.date()
                ) if parsed_date.time() == datetime.min.time() else queryset.filter(
                    departure_time__date=parsed_date.date(),
                    departure_time__hour=parsed_date.hour,
                    departure_time__minute=parsed_date.minute
                )
        else:
            parsed_from = parse_datetime(date_from_param) if date_from_param else None
            parsed_to = parse_datetime(date_to_param) if date_to_param else None

            if parsed_from and parsed_to:
                queryset = queryset.filter(
                    departure_time__range=[parsed_from, parsed_to]
                )
            elif parsed_from:
                queryset = queryset.filter(departure_time__gte=parsed_from)
            elif parsed_to:
                queryset = queryset.filter(departure_time__lte=parsed_to)

        # --- Filtrado por precio ---
        if price_param:
            queryset = queryset.filter(price__lte=price_param)

        return queryset.order_by("-created_at")

    # Respuestas estandarizadas
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data, "Viajes obtenidas correctamente")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data, "Viaje obtenido")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response(serializer.data, "Viaje creado", status.HTTP_201_CREATED)
        return error_response("Error al crear el viaje", serializer.errors)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return success_response(serializer.data, "Viaje actualizado")
        return error_response("Error al actualizar el viaje", serializer.errors)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="Viaje eliminado", data=None, status_code=status.HTTP_204_NO_CONTENT)