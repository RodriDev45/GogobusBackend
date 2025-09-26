from rest_framework.decorators import api_view, permission_classes
from rest_framework import status, permissions, viewsets
from .models import Bus
from .serializers import BusSerializer
from utils.responses import error_response, success_response

class BusViewSet(viewsets.ModelViewSet):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    # Respuestas estandarizadas
    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(serializer.data, "Lista de buses obtenida")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data, "Bus obtenido")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_response(serializer.data, "Bus creado", status.HTTP_201_CREATED)
        return error_response("Error al crear el bus", serializer.errors)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return success_response(serializer.data, "Bus actualizado")
        return error_response("Error al actualizar el Bus", serializer.errors)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success_response(message="Bus eliminado", data=None, status_code=status.HTTP_204_NO_CONTENT)
