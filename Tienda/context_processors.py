from .models import Categoria  # Ajusta el import según la ubicación del modelo

# Esto es para que las categorias del dropdaown del navbar esten disponibles en todas las paginas que hereden de la plantilla base
def categorias_disponibles(request):
    categorias = Categoria.objects.all()
    return {'categorias': categorias}
