from rest_framework import status, permissions, viewsets
from .models import Bus
from .serializers import BusSerializer, BusDetailSerializer
from utils.responses import error_response, success_response
from utils.buses import generar_asientos  # ← importamos la función
from utils.pagination import CustomPagination
from django.db import transaction

class BusViewSet(viewsets.ModelViewSet):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BusDetailSerializer
        return BusSerializer
    
    def get_queryset(self):
        queryset = Bus.objects.all()

        modelo_param = self.request.query_params.get("modelo")
        capacidad_param = self.request.query_params.get("capacidad")
        placa_param = self.request.query_params.get("placa")

        if modelo_param:
            queryset = queryset.filter(modelo__icontains=modelo_param)
        if capacidad_param:
            queryset = queryset.filter(capacidad__icontains=capacidad_param)
        if placa_param:
            queryset = queryset.filter(placa__icontains=placa_param)

        return queryset.order_by("-fecha_registro")
    
    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    # --- LISTAR ---
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data, "Buses obtenidos correctamente")

    # --- OBTENER UNO ---
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data, "Bus obtenido")

    # --- CREAR ---
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            bus = serializer.save()

            try:
                generar_asientos(bus)
            except Exception as e:
                return error_response(
                    "Bus creado pero ocurrió un error al generar los asientos.",
                    str(e)
                )

            return success_response(
                serializer.data,
                "Bus y asientos creados correctamente",
                status.HTTP_201_CREATED
            )
        return error_response("Error al crear el bus", serializer.errors)

    # --- ACTUALIZAR ---
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return success_response(serializer.data, "Bus actualizado")
        return error_response("Error al actualizar el Bus", serializer.errors)

    # --- ELIMINAR ---
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="Bus eliminado", data=None, status_code=status.HTTP_204_NO_CONTENT)
