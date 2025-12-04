from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from utils.responses import success_response, error_response
from django.conf import settings
from decimal import Decimal
import json
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
import mercadopago

from .models import Payment
from bookings.models import Booking
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Payment.objects.all() if user.is_staff else Booking.objects.filter(user=user)
        return queryset.order_by("-created_at")

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(serializer.data, "Pagos obtenidos correctamente")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data, "Pago obtenido correctamente")

    @action(detail=False, methods=["post"], url_path="process")
    def process_payment(self, request):
        """
        Procesa un pago con tarjeta (Checkout API - Core Methods)
        según la documentación oficial de Mercado Pago.
        """
        user = request.user

        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

        required_fields = [
            "transaction_amount",
            "token",
            "description",
            "installments",
            "payment_method_id",
            "email",
            "type",
            "number",
            "booking_id",
        ]

        missing = [f for f in required_fields if f not in request.data]
        if missing:
            return error_response(
                f"Faltan los siguientes campos requeridos: {', '.join(missing)}"
            )

        try:
            booking = Booking.objects.get(id=request.data["booking_id"], user=user)
        except Booking.DoesNotExist:
            return error_response("No se encontró la reserva indicada", status_code=404)

        try:
            payment_data = {
                "transaction_amount": float(request.data["transaction_amount"]),
                "token": request.data["token"],
                "description": request.data["description"],
                "installments": int(request.data["installments"]),
                "payment_method_id": request.data["payment_method_id"],
                "payer": {
                    "email": request.data["email"],
                    "identification": {
                        "type": request.data["type"],
                        "number": request.data["number"],
                    },
                },
            }   
            print(json.dumps(payment_data, indent=2))

            payment_response = sdk.payment().create(payment_data)
            payment_info = payment_response["response"]

            payment = Payment.objects.create(
                user=user,
                booking=booking,
                amount=payment_info.get("transaction_amount", booking.total_amount),
                status=payment_info.get("status", "pending"),
                payment_id=payment_info.get("id"),
                method=payment_info.get("payment_method_id"),
                description=payment_info.get("description"),
            )

            # Actualizar estado de reserva si el pago fue aprobado
            if payment_info.get("status") == "approved":
                booking.status = "PAID"
                booking.save()

            return success_response(
                {
                    "payment": PaymentSerializer(payment).data,
                    "mercadopago_response": payment_info,
                },
                "Pago procesado correctamente",
                status.HTTP_201_CREATED,
            )

        except Exception as e:
            return error_response("Error al procesar el pago", str(e))
        

@api_view(["POST"])
@csrf_exempt
def mercadopago_webhook(request):
    """
    Recibe notificaciones automáticas desde Mercado Pago.
    """
    try:
        data = json.loads(request.body)
        topic = data.get("type") or data.get("topic")
        payment_id = None

        # Mercado Pago puede enviar distintos tipos de eventos (payment, merchant_order, etc.)
        if topic == "payment":
            payment_id = data.get("data", {}).get("id")
        elif topic == "merchant_order":
            payment_id = data.get("resource", "").split("/")[-1]

        if not payment_id:
            return error_response("No se encontró el ID del pago en la notificación")

        sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
        payment_info = sdk.payment().get(payment_id)["response"]

        status_payment = payment_info.get("status")
        payment_method = payment_info.get("payment_method_id")

        # Buscar el pago registrado en nuestra BD
        try:
            payment = Payment.objects.get(payment_id=payment_id)
        except Payment.DoesNotExist:
            return error_response("Pago no encontrado en la base de datos", status_code=404)

        # Actualizar el estado del pago
        payment.status = status_payment
        payment.method = payment_method
        payment.save()

        # Si el pago fue aprobado, marcar la reserva como pagada
        if status_payment == "approved" and payment.booking:
            payment.booking.status = "PAID"
            payment.booking.save()

        return success_response(
            {"payment_id": payment_id, "status": status_payment},
            "Webhook procesado correctamente",
            status.HTTP_200_OK
        )

    except Exception as e:
        return error_response("Error procesando el webhook", str(e))
