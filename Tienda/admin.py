from django.contrib import admin
from .models import Categoria, Producto, Marca, Pregunta, Carrito, CarritoItem, Venta, VentaItem, Entrada, Cuadre, CuadreDetalle
from django.utils.html import format_html
from django.utils.safestring import mark_safe



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
    list_display = [
        'nombre', 'slug', 'codigo', 'fecha_vencimiento',
        'categoria', 'marca', 'precio', 'precio_efectivo',
        'cantidad', 'disponibilidad', 'peso',
        'venta_de_garaje', 'deshabilitado',  # ✅ Se añade aquí
        'fecha_creado', 'imagen_preview'
    ]

    list_filter = [
        'disponibilidad', 'categoria', 'marca',
        'fecha_creado', 'fecha_vencimiento',
        'venta_de_garaje', 'deshabilitado'  # ✅ También como filtro
    ]

    search_fields = ['nombre', 'descripcion', 'codigo', 'marca__nombre']
    prepopulated_fields = {'slug': ('nombre',)}
    date_hierarchy = 'fecha_creado'
    ordering = ['nombre']

    list_editable = ['disponibilidad', 'peso', 'venta_de_garaje', 'deshabilitado']  # ✅ Se puede editar desde la lista
    autocomplete_fields = ['categoria', 'marca']
    save_on_top = True

    readonly_fields = ['fecha_creado', 'fecha_modificado']

    def get_readonly_fields(self, request, obj=None):
        campos_base = ['fecha_creado', 'fecha_modificado']
        if obj:
            campos_extra = [
                'precio',
                'precio_efectivo',
                'cantidad',
                'codigo',
                'fecha_vencimiento',
            ]
            return campos_base + campos_extra
        return campos_base

    def has_delete_permission(self, request, obj=None):
        # ❌ No permitir eliminación de productos
        return False

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
        'nueva_fecha_vencimiento',
        'precio_costo',
        'precio_venta',
        'precio_venta_efectivo',
        'nueva_cantidad',
        'fecha_entrada',
    ]
    list_filter = ['producto', 'fecha_entrada', 'nueva_fecha_vencimiento']
    search_fields = ['producto__nombre', 'nuevo_codigo']
    autocomplete_fields = ['producto']
    date_hierarchy = 'fecha_entrada'
    ordering = ['-fecha_entrada']
    save_on_top = True
    readonly_fields = ['fecha_entrada']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'producto' in form.base_fields:
            form.base_fields['producto'].queryset = Producto.objects.filter(deshabilitado=False)
        return form

    def has_delete_permission(self, request, obj=None):
        return False

    def render_change_form(self, request, context, *args, **kwargs):
        if 'adminform' in context and 'producto' in context['adminform'].form.fields:
            context['adminform'].form.fields['producto'].help_text = mark_safe(
                "<div style='color: #b94a48; font-weight: bold; padding: 6px;'>"
                "⚠️ <strong>Importante:</strong> No elimines entradas. "
                "Si cometiste un error, registra una entrada correctiva (positiva o negativa) para ajustar el stock. "
                "Solo edita si estás completamente seguro."
                "</div>"
            )
        return super().render_change_form(request, context, *args, **kwargs)


    
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
    list_display = [
        'id',
        'dependienta',
        'fecha',
        'forma_pago_coloreada',  # ✅ Mostramos forma de pago con etiquetas
        'codigo_transferencia',
        'total_a_pagar',
    ]
    list_filter = ['forma_pago', 'fecha']
    search_fields = ['dependienta__username', 'codigo_transferencia']
    date_hierarchy = 'fecha'
    autocomplete_fields = ['dependienta']
    save_on_top = True
    ordering = ['-fecha']

    def forma_pago_coloreada(self, obj):
        """
        Devuelve la forma de pago con una etiqueta de color según el tipo.
        """
        colores = {
            'efectivo': 'success',
            'transferencia': 'info',
            'gasto': 'danger',
        }
        color = colores.get(obj.forma_pago, 'secondary')
        label = dict(obj.FORMA_PAGO_OPCIONES).get(obj.forma_pago, obj.forma_pago)
        return format_html(f'<span class="badge bg-{color}">{label}</span>')

    forma_pago_coloreada.short_description = 'Forma de pago'



# Admin de VentaItem (productos en cada venta)
@admin.register(VentaItem)
class VentaItemAdmin(admin.ModelAdmin):
    list_display = ['venta', 'producto', 'cantidad']
    search_fields = ['venta__id', 'producto__nombre']
    list_filter = ['producto']
    autocomplete_fields = ['venta', 'producto']
    save_on_top = True







class CuadreDetalleInline(admin.TabularInline):
    model = CuadreDetalle
    extra = 0
    readonly_fields = [
        'producto',
        'cantidad_inicial',
        'entradas',
        'cantidad_gasto',
        'precio_unitario_gasto',
        'importe_gasto',
        'cantidad_transferencia',
        'precio_unitario_transferencia',
        'importe_transferencia',
        'cantidad_efectivo',
        'precio_unitario_efectivo',
        'importe_efectivo',
        'importe_total_producto',
        'cantidad_final',
    ]
    can_delete = False
    show_change_link = False
    
    
    
    

@admin.register(Cuadre)
class CuadreAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'usuario', 'creado_en']
    search_fields = ['usuario__username']
    list_filter = ['fecha', 'usuario']
    ordering = ['-fecha']
    inlines = [CuadreDetalleInline]
    readonly_fields = ['fecha', 'usuario', 'creado_en']

    def has_add_permission(self, request):
        return False  # Para evitar que se creen desde el admin

    def has_change_permission(self, request, obj=None):
        return False  # Para que no se editen desde el admin

    def has_delete_permission(self, request, obj=None):
        return False  # Opcional: evitar eliminación desde admin



# # Admin para Gasto
# @admin.register(Gasto)
# class GastoAdmin(admin.ModelAdmin):
#     list_display = ['id', 'responsable', 'fecha', 'descripcion_corta', 'total_productos']
#     list_filter = ['responsable', 'fecha']
#     search_fields = ['descripcion', 'responsable__username']
#     date_hierarchy = 'fecha'
#     ordering = ['-fecha']
#     readonly_fields = ['fecha']

#     def descripcion_corta(self, obj):
#         return obj.descripcion[:50] + "..." if obj.descripcion and len(obj.descripcion) > 50 else obj.descripcion
#     descripcion_corta.short_description = 'Descripción'

#     def total_productos(self, obj):
#         return sum(item.cantidad for item in obj.items.all())
#     total_productos.short_description = 'Total de productos usados'

#     def has_delete_permission(self, request, obj=None):
#         return False
    
    
    
# # Admin para gasto item
# @admin.register(GastoItem)
# class GastoItemAdmin(admin.ModelAdmin):
#     list_display = ['gasto', 'producto', 'cantidad']
#     list_filter = ['producto']
#     search_fields = ['producto__nombre', 'gasto__id']
#     autocomplete_fields = ['gasto', 'producto']
#     ordering = ['-gasto__fecha']

#     def has_delete_permission(self, request, obj=None):
#         return False