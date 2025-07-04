from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


# Modelo de Categoría
class Categoria(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    imagen_url = models.URLField(blank=True, null=True, help_text="Pega aquí el enlace directo de la imagen en Drive")
    

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
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    descripcion = models.TextField(blank=True)

    # Precio de venta actual del producto (inicialmente 0)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Código y vencimiento pueden estar vacíos
    codigo = models.CharField(max_length=100, blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)

    disponibilidad = models.BooleanField(default=True)
    peso = models.CharField(max_length=50, blank=True, null=True)
    opcion_mensajeria = models.BooleanField(default=False)
    rebajado = models.BooleanField(default=False)
    envio_gratis = models.BooleanField(default=False)

    cantidad = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])

    # Nuevo campo: indica si el producto pertenece a "Venta de garaje"
    venta_de_garaje = models.BooleanField(default=False)

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
    def imagen_url(self):
        if self.imagen:
            return self.imagen.url
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
    nueva_cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    nuevo_codigo = models.CharField(max_length=100)
    nueva_fecha_vencimiento = models.DateField(blank=True, null=True)  # <--- Campo añadido
    fecha_entrada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_entrada']

    def save(self, *args, **kwargs):
        """
        Al guardar una entrada, actualizamos automáticamente el producto asociado:
        - Se suma la nueva cantidad a la cantidad existente.
        - Se actualiza el precio de venta, el código y la fecha de vencimiento.
        """
        super().save(*args, **kwargs)

        producto = self.producto
        producto.cantidad += self.nueva_cantidad
        producto.precio = self.precio_venta
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
    ]
    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO_OPCIONES)
    codigo_transferencia = models.CharField(max_length=100, blank=True, null=True)

    # ✅ Nuevo campo para guardar el total final
    total_a_pagar = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Venta #{self.id} - {self.dependienta.username} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-fecha']


# Modelo intermedio para registrar los productos y su cantidad en cada venta
class VentaItem(models.Model):
    venta = models.ForeignKey(Venta, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.cantidad * self.producto.precio

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
