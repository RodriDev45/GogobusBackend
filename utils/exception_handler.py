from rest_framework.views import exception_handler
from utils.responses import error_response

def custom_exception_handler(exc, context):
    # Llamar al handler por defecto de DRF
    response = exception_handler(exc, context)

    if response is not None:
        # Si es un error manejado por DRF (permisos, validación, etc.)
        return error_response(
            message=response.data.get("detail", "Error en la solicitud"),
            errors=response.data,
            status_code=response.status_code
        )

    # Si es un error no manejado (ej. 500)
    return error_response(
        message="Error interno del servidor",
        errors=str(exc),
        status_code=500
    )
