import sys
from django.apps import AppConfig

class TiendaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Tienda'

    def ready(self):
        # ✅ Solo ejecuta si estamos en ejecución del servidor, no durante migraciones ni en entornos donde la BD no está lista
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv:
            from django.contrib.auth.models import Group
            from django.db.utils import OperationalError, ProgrammingError

            try:
                for nombre_grupo in ['Cliente', 'Dependiente', 'Administrador']:
                    Group.objects.get_or_create(name=nombre_grupo)
            except (OperationalError, ProgrammingError):
                # ⚠️ Se atrapan errores si la base de datos aún no está lista
                pass
<<<<<<< HEAD

            # Importa señales solo si es seguro
            try:
                import Tienda.signals
            except ImportError:
                pass

=======

            # Importa señales solo si es seguro
            try:
                import Tienda.signals
            except ImportError:
                pass
>>>>>>> 77a41cf44a5a04bf9de21528f2e6642f7c2755bd

