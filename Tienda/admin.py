from django.contrib import admin
from .models import Categoria, Producto, Marca, Pregunta, Carrito, CarritoItem, Venta, VentaItem, Entrada 
from django.utils.html import format_html



# Admin de Categoría
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'slug', 'imagen_preview']
    prepopulated_fields = {'slug': ('nombre',)}
    search_fields = ['nombre']
    ordering = ['nombre']

    def imagen_preview(self, obj):
        if obj.imagen_url:
            return format_html('<img src="{}" style="width: 50px; height:50px; object-fit: cover;" />', obj.imagen_url)
        return "(sin imagen)"
    imagen_preview.short_description = 'Imagen'
    
    

# Admin de Marca
@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ['nombre']
    search_fields = ['nombre']
    ordering = ['nombre']


# Este es el admin de Producto
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    # Campos que se mostrarán en la lista de productos en el panel de administración
    list_display = [
        'nombre', 'slug', 'codigo', 'fecha_vencimiento',
        'categoria', 'marca', 'precio', 'precio_efectivo',  # Se agregó precio_efectivo
        'cantidad', 'disponibilidad', 'peso',
        'venta_de_garaje', 'fecha_creado', 'imagen_preview'
    ]

    # Filtros en la barra lateral del admin
    list_filter = [
        'disponibilidad', 'categoria', 'marca',
        'fecha_creado', 'fecha_vencimiento', 'venta_de_garaje'
    ]

    # Campos sobre los que se puede buscar
    search_fields = ['nombre', 'descripcion', 'codigo', 'marca__nombre']

    # Slug autocompletado desde el nombre
    prepopulated_fields = {'slug': ('nombre',)}

    # Barra de navegación por fechas
    date_hierarchy = 'fecha_creado'

    # Orden predeterminado de los resultados
    ordering = ['nombre']

    # Campos que se pueden editar directamente desde la lista
    list_editable = ['precio', 'precio_efectivo', 'cantidad', 'disponibilidad', 'peso', 'venta_de_garaje']

    # Campos de relaciones con autocompletado
    autocomplete_fields = ['categoria', 'marca']

    # Mostrar botones de guardar también en la parte superior del formulario
    save_on_top = True

    # Método para mostrar una miniatura de la imagen en la vista de lista
    def imagen_preview(self, obj):
        if obj.imagen_url:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover;" />',
                obj.imagen_url
            )
        return "(No Image)"
    imagen_preview.short_description = 'Imagen'

    
    
    

# Admin de Entrada de productos (reabastecimiento)
@admin.register(Entrada)
class EntradaAdmin(admin.ModelAdmin):
    list_display = [
        'producto',
        'nuevo_codigo',
        'nueva_fecha_vencimiento',  # Fecha de vencimiento
        'precio_costo',
        'precio_venta',
        'precio_venta_efectivo',     # ✅ Campo nuevo añadido
        'nueva_cantidad',
        'fecha_entrada'
    ]
    list_filter = ['producto', 'fecha_entrada', 'nueva_fecha_vencimiento']
    search_fields = ['producto__nombre', 'nuevo_codigo']
    autocomplete_fields = ['producto']
    date_hierarchy = 'fecha_entrada'
    ordering = ['-fecha_entrada']
    save_on_top = True




    
# Admin de Pregunta
@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ['pregunta', 'respuesta', 'fecha_creado']  # Muestra las preguntas, respuestas y fecha de creación
    search_fields = ['pregunta', 'respuesta']  # Habilita búsqueda por pregunta y respuesta
    list_filter = ['fecha_creado']  # Permite filtrar por fecha de creación
    ordering = ['fecha_creado']  # Ordena por fecha de creación, de más nuevo a más antiguo
    save_on_top = True  # Añadir botón de guardar arriba para facilitar la edición


# Admin de Carrito
@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ['usuario']
    search_fields = ['usuario__username']
    filter_horizontal = ['productos']  # Mejora la experiencia visual para elegir productos
    ordering = ['usuario']
    save_on_top = True


# Admin de CarritoItem (opcional, si lo usas directamente)
@admin.register(CarritoItem)
class CarritoItemAdmin(admin.ModelAdmin):
    list_display = ['carrito', 'producto', 'cantidad']
    search_fields = ['carrito__usuario__username', 'producto__nombre']
    list_filter = ['producto']
    ordering = ['carrito', 'producto']
    autocomplete_fields = ['carrito', 'producto']
    save_on_top = True


# Admin de Venta
@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'dependienta', 'fecha', 'forma_pago', 'codigo_transferencia', 'total_a_pagar']  # ✅ se añadió total_a_pagar
    list_filter = ['forma_pago', 'fecha']
    search_fields = ['dependienta__username', 'codigo_transferencia']
    date_hierarchy = 'fecha'
    autocomplete_fields = ['dependienta']
    save_on_top = True
    ordering = ['-fecha']



# Admin de VentaItem (productos en cada venta)
@admin.register(VentaItem)
class VentaItemAdmin(admin.ModelAdmin):
    list_display = ['venta', 'producto', 'cantidad']
    search_fields = ['venta__id', 'producto__nombre']
    list_filter = ['producto']
    autocomplete_fields = ['venta', 'producto']
    save_on_top = True
