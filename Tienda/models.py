from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils.timezone import now

# Modelo de Categoría
class Categoria(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    imagen_url = models.URLField(blank=True, null=True, help_text="Pega aquí el enlace directo de la imagen")
    

    class Meta:
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['nombre']),
        ]
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return f"/categoria/{self.slug}/"
    
    
# Modelo de Marca
class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre



# Modelo de producto
class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, related_name='productos', on_delete=models.CASCADE)
    marca = models.ForeignKey(Marca, related_name='productos', on_delete=models.SET_NULL, null=True, blank=True)
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    imagen_url = models.URLField(blank=True, null=True, help_text="Pega aquí el enlace directo de la imagen")
    descripcion = models.TextField(blank=True)

    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    codigo = models.CharField(max_length=100, blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)

    disponibilidad = models.BooleanField(default=True)
    peso = models.CharField(max_length=50, blank=True, null=True)
    opcion_mensajeria = models.BooleanField(default=False)
    rebajado = models.BooleanField(default=False)
    envio_gratis = models.BooleanField(default=False)

    cantidad = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    venta_de_garaje = models.BooleanField(default=False)

    # 🆕 Campo para ocultar productos que ya no se usarán
    deshabilitado = models.BooleanField(default=False, help_text="Marca este producto como deshabilitado si ya no se vende ni repone.")

    fecha_creado = models.DateTimeField(auto_now_add=True)
    fecha_modificado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['nombre']),
            models.Index(fields=['-fecha_creado']),
        ]

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return f"/producto/{self.slug}/"

    @property
    def imagen_url_final(self):
        if self.imagen_url:
            return self.imagen_url
        return "/media/default.png"

    def save(self, *args, **kwargs):
        # Actualizar disponibilidad según la cantidad
        self.disponibilidad = self.cantidad > 0
        super().save(*args, **kwargs)



        
        
# Modelo de Entrada de productos
class Entrada(models.Model):
    producto = models.ForeignKey(Producto, related_name='entradas', on_delete=models.CASCADE)
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    nueva_cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    nuevo_codigo = models.CharField(max_length=100)
    nueva_fecha_vencimiento = models.DateField(blank=True, null=True)
    fecha_entrada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_entrada']

    def save(self, *args, **kwargs):
        """
        Al guardar una entrada, se ajusta el stock y, si corresponde, se actualizan los datos del producto.
        - Si se edita una entrada antigua, solo se ajusta el stock.
        - Si la entrada es la más reciente para ese producto, se actualizan precio, código, vencimiento.
        """
        es_actualizacion = self.pk is not None

        # Guardar valores previos antes de actualizar
        if es_actualizacion:
            entrada_anterior = Entrada.objects.get(pk=self.pk)
            cantidad_anterior = entrada_anterior.nueva_cantidad
        else:
            cantidad_anterior = 0

        super().save(*args, **kwargs)  # Guardar entrada primero

        producto = self.producto

        # Ajustar cantidad del producto (resta lo anterior y suma lo nuevo)
        producto.cantidad -= cantidad_anterior
        producto.cantidad += self.nueva_cantidad

        # Verificar si esta entrada es la más reciente
        ultima_entrada = Entrada.objects.filter(producto=producto).order_by('-fecha_entrada').first()

        if ultima_entrada and ultima_entrada.pk == self.pk:
            # Solo si esta entrada es la más reciente se actualizan estos campos
            producto.precio = self.precio_venta
            producto.precio_efectivo = self.precio_venta_efectivo
            producto.codigo = self.nuevo_codigo
            if self.nueva_fecha_vencimiento:
                producto.fecha_vencimiento = self.nueva_fecha_vencimiento

        producto.save()

    def __str__(self):
        return f"Entrada de {self.nueva_cantidad} x {self.producto.nombre} ({self.fecha_entrada.date()})"

# Modelo de pregunta
class Pregunta(models.Model):
    pregunta = models.CharField(max_length=500)  # Limitar a un máximo de 500 caracteres
    respuesta = models.TextField()  # Para poder escribir una respuesta más extensa

    fecha_creado = models.DateTimeField(auto_now_add=True)  # Fecha de creación para ordenarlas si es necesario
    fecha_modificado = models.DateTimeField(auto_now=True)  # Fecha de modificación (opcional)

    def __str__(self):
        return self.pregunta  # Se muestra la pregunta en lugar del objeto completo en el admin

    class Meta:
        ordering = ['fecha_creado']  # Ordenar las preguntas por fecha de creación
    
    
# Modelos de carrito de compra
class Carrito(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    productos = models.ManyToManyField(Producto, related_name='carritos', blank=True)
    
    def __str__(self):
        return f"Carrito de {self.usuario.username}"

class CarritoItem(models.Model):
    carrito = models.ForeignKey(Carrito, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.cantidad * self.producto.precio

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'
    
    
    


# Modelo de Venta
class Venta(models.Model):
    dependienta = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ventas')
    fecha = models.DateTimeField(auto_now_add=True)

    FORMA_PAGO_OPCIONES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('gasto', 'Agregar a gastos'),  # 🆕 Nueva opción
    ]
    forma_pago = models.CharField(max_length=30, choices=FORMA_PAGO_OPCIONES)
    codigo_transferencia = models.CharField(max_length=100, blank=True, null=True)

    total_a_pagar = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # 🆕 Campo para guardar el motivo del gasto si la venta fue registrada como "gasto"
    motivo_gasto = models.TextField(
        blank=True,
        null=True,
        help_text="Describe el motivo si esta venta fue registrada como gasto"
    )

    def __str__(self):
        return f"Venta #{self.id} - {self.dependienta.username} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-fecha']


        


# Modelo intermedio para registrar los productos y su cantidad en cada venta
class VentaItem(models.Model):
    venta = models.ForeignKey(Venta, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Precio normal
    precio_unitario_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Precio en efectivo

    def subtotal(self):
        return self.precio_unitario * self.cantidad

    def subtotal_efectivo(self):
        return self.precio_unitario_efectivo * self.cantidad

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'



# Modelos para gestionar ventas en construcción (temporalmente)
class VentaTemporal(models.Model):
    dependienta = models.OneToOneField(User, on_delete=models.CASCADE, related_name='venta_temporal')
    creada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Venta temporal de {self.dependienta.username}"

    def total(self):
        return sum(item.subtotal() for item in self.items.all())


class VentaTemporalItem(models.Model):
    venta_temporal = models.ForeignKey(VentaTemporal, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=0)

    def subtotal(self):
        return self.cantidad * self.producto.precio

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'
    
    
# Modelo para hacer el cuadre
class Cuadre(models.Model):
    fecha = models.DateField(unique=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cuadre {self.fecha} - {self.usuario.username}"

class CuadreDetalle(models.Model):
    cuadre = models.ForeignKey(Cuadre, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad_inicial = models.PositiveIntegerField()
    entradas = models.PositiveIntegerField(default=0)

    cantidad_gasto = models.PositiveIntegerField(default=0)
    precio_unitario_gasto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    importe_gasto = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    cantidad_transferencia = models.PositiveIntegerField(default=0)
    precio_unitario_transferencia = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    importe_transferencia = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    cantidad_efectivo = models.PositiveIntegerField(default=0)
    precio_unitario_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    importe_efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    importe_total_producto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cantidad_final = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.producto.nombre} - Cuadre {self.cuadre.fecha}"






# # Modelo de Gasto (productos usados internamente)
# class Gasto(models.Model):
#     responsable = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gastos')
#     fecha = models.DateTimeField(auto_now_add=True)
#     descripcion = models.TextField(blank=True, help_text="Describe brevemente el motivo del gasto")

#     def __str__(self):
#         return f"Gasto #{self.id} - {self.responsable.username} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"

#     class Meta:
#         ordering = ['-fecha']



# # Detalle de productos utilizados en el gasto
# class GastoItem(models.Model):
#     gasto = models.ForeignKey(Gasto, related_name='items', on_delete=models.CASCADE)
#     producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
#     cantidad = models.PositiveIntegerField(default=1)

#     def __str__(self):
#         return f'{self.cantidad} x {self.producto.nombre} (Gasto #{self.gasto.id})'
