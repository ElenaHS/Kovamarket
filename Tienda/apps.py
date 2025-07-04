from django.apps import AppConfig

class TiendaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Tienda'

    def ready(self):
        # Importar solo dentro del método ready, cuando Django esté completamente cargado
        from django.contrib.auth.models import Group

        # Crear los grupos si no existen
        for nombre_grupo in ['Cliente', 'Dependiente', 'Administrador']:
            Group.objects.get_or_create(name=nombre_grupo)

        # Si usas señales, importa el archivo aquí también
        import Tienda.signals

