from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    class Roles(models.TextChoices):
        PASSENGER = "PASSENGER", "Pasajero"
        DRIVER = "DRIVER", "Conductor"
        ADMIN = "ADMIN", "Administrador"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.PASSENGER
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    dni = models.CharField(max_length=20, blank=True, null=True)
    license_number = models.CharField(max_length=50, blank=True, null=True)

    # Campo para login social
    google_id = models.CharField(max_length=255, blank=True, null=True, unique=True)

    # Campo para URL de la imagen de perfil (supabase storage)
    profile_image_url = models.URLField(max_length=500, blank=True, null=True)

    # 👇 Definir email como identificador único
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"   # ahora se usa el email para login
    REQUIRED_FIELDS = ["username"]  # username seguirá existiendo, pero no es obligatorio para login

    def __str__(self):
        return f"{self.username} ({self.role})"