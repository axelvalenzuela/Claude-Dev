from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuario de la app. username = email; se agrega el departamento del empleado."""

    department = models.CharField("Departamento", max_length=100, blank=True)

    def __str__(self):
        return self.get_full_name() or self.email or self.username
