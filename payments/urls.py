from django.urls import path, include
from .views import PaymentViewSet, mercadopago_webhook
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('', PaymentViewSet, basename='payments')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/mercadopago/', mercadopago_webhook, name='mercadopago-webhook'),
]
