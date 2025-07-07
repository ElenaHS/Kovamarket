from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Categoria, Producto, Pregunta, Carrito, CarritoItem, Venta, VentaItem, VentaTemporal, VentaTemporalItem
from .forms import VentaForm, VentaItemForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login as auth_login
from .forms import RegistroForm,  LoginForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import modelformset_factory
from django.utils import timezone
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.template.loader import get_template
from decimal import Decimal
from datetime import datetime




# Vista para iniciar sesion
def iniciar_sesion(request):
    form = LoginForm(request, data=request.POST or None)
    
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f'¡Bienvenido/a {user.username}!')
            return redirect('inicio')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')  # opcional

    return render(request, 'iniciar_sesion.html', {'form': form})

# Vista para cerrar sesion
def cerrar_sesion(request):
    auth_logout(request)  # Cierra la sesión del usuario
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect('inicio')  # Redirige a la página de inicio o cualquier otra vista




# Vista para registrar usuario
def register(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Obtener o crear el grupo "Cliente"
            grupo, creado = Group.objects.get_or_create(name='Cliente')
            user.groups.add(grupo)  # Asignar el usuario al grupo

            auth_login(request, user)
            messages.success(request, '¡Bienvenido! Tu cuenta ha sido creada y ya has iniciado sesión.')
            return redirect('inicio')
    else:
        form = RegistroForm()

    return render(request, 'registrar.html', {'form': form})




# Vista de inicio
def inicio(request):
    categorias = Categoria.objects.all()  # Obtener todas las categorías
    return render(request, 'inicio.html', {'categorias': categorias})

# Listar categorías
def listar_categoria(request):
    categorias = Categoria.objects.all()
    return render(request, 'listar_categoria.html', {'categorias': categorias})



# Vista para listar productos, con filtrado por categoría y ordenamiento
def listar_producto(request, categoria_slug=None):
    # Verificar si el slug corresponde a una categoría específica
    if categoria_slug == 'venta-de-garaje':
        # Si es una categoría fija, filtrar por productos marcados como venta_de_garaje
        categoria = None  # No hay categoría real en este caso
        productos = Producto.objects.filter(venta_de_garaje=True)
    elif categoria_slug and categoria_slug != 'todo':
        # Buscar la categoría según el slug proporcionado
        categoria = get_object_or_404(Categoria, slug=categoria_slug)
        # Filtrar productos por la categoría encontrada
        productos = Producto.objects.filter(categoria=categoria)
    else:
        # Si el slug es "todo" o no se proporciona ninguno, mostrar todos los productos
        categoria = None
        productos = Producto.objects.all()

    # Actualizar la disponibilidad de cada producto según su stock
    for producto in productos:
        if producto.cantidad == 0 and producto.disponibilidad:
            producto.disponibilidad = False
            producto.save()
        elif producto.cantidad > 0 and not producto.disponibilidad:
            producto.disponibilidad = True
            producto.save()

    # Obtener el parámetro de ordenación desde la URL
    ordenar = request.GET.get('ordenar', None)
    if ordenar == 'precio_asc':
        productos = productos.order_by('precio')  # Ordenar de menor a mayor precio
    elif ordenar == 'precio_desc':
        productos = productos.order_by('-precio')  # Ordenar de mayor a menor precio
    elif ordenar == 'nuevo':
        productos = productos.order_by('-fecha_creado')  # Ordenar por productos más recientes

    # Configurar paginación (18 productos por página)
    paginator = Paginator(productos, 18)
    page_number = request.GET.get('page')  # Obtener número de página desde la URL
    productos_page = paginator.get_page(page_number)  # Obtener la página actual de productos

    # Renderizar la plantilla y pasar el slug de categoría seleccionada
    return render(request, 'listar_productos.html', {
        'categoria': categoria,
        'categoria_slug': categoria_slug,  # Se pasa a la plantilla para marcar categoría activa
        'productos': productos_page,
        'ordenar': ordenar
    })

# Detalle de los productos
def producto_detalle(request, id):
    producto = get_object_or_404(Producto, id=id)
    return render(request, 'producto_detalle.html', {'producto': producto})


# Listar las preguntas frecuentas
def listar_pregunta(request):
    preguntas = Pregunta.objects.all()
    return render(request, 'preguntas_frecuentes.html', {'preguntas': preguntas})

# Ver carrito
@login_required
def ver_carrito(request):
    carrito, creado = Carrito.objects.get_or_create(usuario=request.user)
    items = carrito.items.select_related('producto')

    cantidad_total = sum(item.cantidad for item in items)

    # Calcular el precio total del carrito
    precio_total = sum(item.cantidad * item.producto.precio for item in items)

    return render(request, 'carrito.html', {
        'items': items,
        'cantidad_total': cantidad_total,
        'precio_total': precio_total
    })




# Agregar al carrito
@login_required(login_url='iniciar_sesion')  # usa el nombre de tu URL para iniciar sesión
def agregar_al_carrito(request, producto_id):
    # Obtener el producto según el ID; si no existe, retorna error 404
    producto = get_object_or_404(Producto, id=producto_id)

    # Verificar si el producto tiene stock disponible
    if producto.cantidad <= 0:
        messages.warning(request, "Este producto está agotado.")
        return redirect('listar_producto')

    # Obtener o crear el carrito asociado al usuario actual
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)

    # Obtener o crear el ítem del carrito correspondiente al producto
    item, creado = CarritoItem.objects.get_or_create(carrito=carrito, producto=producto)

    if not creado:
        # Si el ítem ya existe, verificar si aún se puede aumentar la cantidad
        if item.cantidad < producto.cantidad:
            item.cantidad += 1
            item.save()
            messages.success(request, f"Se ha añadido otra unidad de {producto.nombre} al carrito.")
        else:
            messages.warning(request, "No puedes agregar más unidades de las disponibles en stock.")
    else:
        # Si es la primera vez que se agrega al carrito, establecer cantidad = 1
        item.cantidad = 1
        item.save()
        messages.success(request, f"{producto.nombre} se ha añadido al carrito.")

    # Importante: No se descuenta del stock aquí. Se hará al confirmar la compra.
    return redirect('ver_carrito')




# Eliminar item
@login_required
def eliminar_item(request, item_id):
    item = get_object_or_404(CarritoItem, id=item_id, carrito__usuario=request.user)
    item.delete()
    return redirect('ver_carrito')



# Aumentar cantidad de un producto en el carrito
@login_required
def aumentar_cantidad(request, item_id):
    item = get_object_or_404(CarritoItem, id=item_id, carrito__usuario=request.user)
    if item.cantidad < item.producto.cantidad:
        item.cantidad += 1
        
        item.producto.save()
        item.save()
    else:
        messages.warning(request, "No hay más stock disponible para este producto.")
    return redirect('ver_carrito')


# Disminuir cantidad de un producto en el carrito
@login_required
def disminuir_cantidad(request, item_id):
    item = get_object_or_404(CarritoItem, id=item_id, carrito__usuario=request.user)
    if item.cantidad > 1:
        item.cantidad -= 1
        
        item.producto.save()
        item.save()
    else:
        # Eliminar el ítem si la cantidad es 1 y se desea disminuir
       
        item.producto.save()
        item.delete()
    return redirect('ver_carrito')



# Vista para buscar productos
def buscar_productos(request):
    # Obtener el término de búsqueda desde el campo "q" del formulario
    query = request.GET.get('q', '')
    
    # Filtrar productos cuyo nombre contenga el término buscado (ignorando mayúsculas/minúsculas)
    resultados = Producto.objects.filter(nombre__icontains=query)

    # Renderizar los resultados en la plantilla correspondiente
    return render(request, 'buscar_resultados.html', {
        'query': query,
        'resultados': resultados
    })
    
    
    
# Solo usuarios del grupo "dependienta"
def es_dependienta(user):
    return user.groups.filter(name='dependienta').exists()


# Solo superusuarios
def solo_superusuario(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('error_permisos')
        return view_func(request, *args, **kwargs)
    return login_required(_wrapped_view)


# Error de permisos
def error_permisos(request):
    return render(request, 'error_permisos.html')



# Vista para gestionar las ventas
solo_superusuario
@login_required
def gestionar_venta(request):
    ventas_lista = Venta.objects.filter(dependienta=request.user).order_by('-fecha')
    paginator = Paginator(ventas_lista, 20)  # Cambia el 20 si deseas más o menos ventas por página
    page_number = request.GET.get("page")
    ventas = paginator.get_page(page_number)
    return render(request, 'gestionar_venta.html', {'ventas': ventas})



# Vista para detalle de venta
@solo_superusuario
@login_required
def detalle_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id, dependienta=request.user)
    items = venta.items.select_related('producto')

    # Calcular subtotal según forma de pago
    for item in items:
        if venta.forma_pago == 'efectivo':
            precio_unitario = item.producto.precio_efectivo
        else:
            precio_unitario = item.producto.precio
        item.subtotal_calculado = precio_unitario * item.cantidad

    return render(request, 'detalle_venta.html', {
        'venta': venta,
        'items': items
    })


# Vista para generar reporte en pdf de las ventas
@solo_superusuario
@login_required
def generar_reporte_pdf(request):
    filtro = request.GET.get('filtro')
    valor = request.GET.get('valor')

    # Filtrar ventas según el filtro y valor
    ventas_filtradas = filtrar_ventas_por_filtro(filtro, valor)

    # Calcular totales según forma de pago
    total_efectivo = 0
    total_transferencia = 0
    for venta in ventas_filtradas:
        if venta.forma_pago == 'efectivo':
            total_efectivo += float(venta.total_a_pagar)
        elif venta.forma_pago == 'transferencia':
            total_transferencia += float(venta.total_a_pagar)

    total_general = total_efectivo + total_transferencia

    # Contexto para la plantilla
    context = {
        'ventas': ventas_filtradas,
        'filtro': filtro,
        'valor': valor,
        'total_efectivo': total_efectivo,
        'total_transferencia': total_transferencia,
        'total_general': total_general,
        'ahora': timezone.now(),
        'request': request,  # para acceder a request.user en la plantilla
    }

    # Renderizar PDF
    template_path = 'reporte_pdf.html'
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_ventas.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error al generar PDF <pre>' + html + '</pre>')

    return response


def filtrar_ventas_por_filtro(filtro, valor):
    if not filtro or not valor:
        return Venta.objects.none()  # No se proporciona filtro o valor

    try:
        if filtro == 'dia':
            fecha = datetime.strptime(valor, '%Y-%m-%d')
            return Venta.objects.filter(fecha__date=fecha.date())

        elif filtro == 'mes':
            año, mes = map(int, valor.split('-'))
            return Venta.objects.filter(fecha__year=año, fecha__month=mes)

        elif filtro == 'año':
            año = int(valor)
            return Venta.objects.filter(fecha__year=año)

    except Exception as e:
        print(f"Error en filtrado: {e}")
        return Venta.objects.none()


# Vista para mostrar y confirmar una nueva venta
from django.db.models import Q
from django.core.paginator import Paginator

@login_required
@solo_superusuario
def nueva_venta(request):
    venta_temp, _ = VentaTemporal.objects.get_or_create(dependienta=request.user)
    items_actuales = venta_temp.items.select_related("producto")

    # Precio sin descuento
    precio_total = sum(item.producto.precio * item.cantidad for item in items_actuales)

    # Precio total en efectivo
    precio_total_efectivo = sum(item.producto.precio_efectivo * item.cantidad for item in items_actuales)

    # Subtotal efectivo para cada item
    for item in items_actuales:
        item.subtotal_efectivo = item.producto.precio_efectivo * item.cantidad

    # Búsqueda de productos
    consulta = request.GET.get('buscar', '')
    productos_disponibles = Producto.objects.filter(disponibilidad=True)

    if consulta:
        productos_disponibles = productos_disponibles.filter(nombre__icontains=consulta)

    # Paginación
    paginator = Paginator(productos_disponibles, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    if request.method == "POST":
        venta_form = VentaForm(request.POST)
        if venta_form.is_valid():
            forma_pago = venta_form.cleaned_data["forma_pago"]
            codigo_transferencia = venta_form.cleaned_data["codigo_transferencia"]

            total_a_pagar = precio_total_efectivo if forma_pago == "efectivo" else precio_total

            venta = Venta.objects.create(
                dependienta=request.user,
                fecha=timezone.now(),
                forma_pago=forma_pago,
                codigo_transferencia=codigo_transferencia,
                total_a_pagar=total_a_pagar
            )

            for item in items_actuales:
                VentaItem.objects.create(
                    venta=venta,
                    producto=item.producto,
                    cantidad=item.cantidad,
                    precio_unitario=item.producto.precio,
                    precio_unitario_efectivo=item.producto.precio_efectivo
                )
                item.producto.cantidad -= item.cantidad
                item.producto.save()

            venta_temp.delete()
            messages.success(request, "✅ Venta registrada correctamente.")
            return redirect("gestionar_venta")
    else:
        venta_form = VentaForm()

    context = {
        "usuario": request.user,
        "productos": page_obj,
        "items": items_actuales,
        "precio_total": precio_total,
        "precio_total_efectivo": precio_total_efectivo,
        "venta_form": venta_form,
        "buscar": consulta
    }
    return render(request, "nueva_venta.html", context)




# Vista para agregar un producto (evita doble procesamiento)
@login_required
@solo_superusuario
def agregar_producto_venta(request, producto_id):
    if request.method == "POST":
        venta_temp, _ = VentaTemporal.objects.get_or_create(dependienta=request.user)
        producto = get_object_or_404(Producto, id=producto_id)

        item, created = VentaTemporalItem.objects.get_or_create(
            venta_temporal=venta_temp,
            producto=producto
        )

        if item.cantidad + 1 > producto.cantidad:
            messages.warning(request, f"No hay más stock disponible para '{producto.nombre}'.")
        else:
            item.cantidad += 1
            item.save()
            messages.success(request, f"Producto '{producto.nombre}' añadido a la venta.")

    return redirect("nueva_venta")



# Aumentar cantidad de un producto en la venta temporal
@login_required
@solo_superusuario
def aumentar_cantidad_venta(request, item_id):
    item = get_object_or_404(VentaTemporalItem, id=item_id, venta_temporal__dependienta=request.user)
    
    if item.cantidad < item.producto.cantidad:
        item.cantidad += 1
        item.save()
    else:
        messages.warning(request, "No hay más stock disponible para este producto.")
        
    return redirect('nueva_venta')


# Disminuir cantidad de un producto en la venta temporal
@login_required
@solo_superusuario
def disminuir_cantidad_venta(request, item_id):
    item = get_object_or_404(VentaTemporalItem, id=item_id, venta_temporal__dependienta=request.user)
    
    if item.cantidad > 1:
        item.cantidad -= 1
        item.save()
    else:
        item.delete()
        
    return redirect('nueva_venta')


# Vista para cancelar la venta
@login_required

def cancelar_venta(request):
    if request.method == "POST":
        try:
            venta_temp = VentaTemporal.objects.get(dependienta=request.user)
            # Borra todos los items asociados a esta venta
            VentaTemporalItem.objects.filter(venta_temporal=venta_temp).delete()
            venta_temp.delete()
            messages.success(request, "La venta ha sido cancelada correctamente.")
        except VentaTemporal.DoesNotExist:
            messages.warning(request, "No hay una venta activa para cancelar.")
    return redirect("gestionar_venta")





# # Esta es la vista para registrar una nueva venta basada en el carrito de la dependienta
# @login_required
# def nueva_venta(request):
#     # Obtener el carrito de la usuaria actual
#     carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
#     items = carrito.items.select_related('producto')

#     if not items.exists():
#         messages.warning(request, "Tu carrito está vacío. Añade productos antes de registrar la venta.")
#         return redirect('ver_carrito')

#     if request.method == 'POST':
#         venta_form = VentaForm(request.POST)
#         if venta_form.is_valid():
#             venta = venta_form.save(commit=False)
#             venta.dependienta = request.user
#             venta.save()

#             # Crear los VentaItem desde los productos del carrito
#             for item in items:
#                 VentaItem.objects.create(
#                     venta=venta,
#                     producto=item.producto,
#                     cantidad=item.cantidad
#                 )
#                 # Descontar del stock
#                 item.producto.cantidad -= item.cantidad
#                 item.producto.save()

#             # Vaciar el carrito
#             carrito.items.all().delete()

#             messages.success(request, "Venta registrada exitosamente.")
#             return redirect('gestionar_venta')
#     else:
#         venta_form = VentaForm()

#     precio_total = sum(item.producto.precio * item.cantidad for item in items)

#     return render(request, 'nueva_venta.html', {
#         'venta_form': venta_form,
#         'items': items,
#         'precio_total': precio_total,
#         'usuario': request.user,  # Para mostrar el nombre en la plantilla
#     })
    
    
    
   # Vistas relacionadas con ventas

# @login_required
# def listado_productos_venta(request):
#     productos = Producto.objects.filter(disponibilidad=True)

#     return render(request, 'listado_productos_venta.html', {
#         'productos': productos
#     })



# @login_required
# # @user_passes_test(es_dependienta)  # Puedes activar esta validación si defines el test de rol
# def nueva_venta(request):
#     # Se define un formset para agregar varios productos a la venta
#     VentaItemFormSet = modelformset_factory(
#         VentaItem, form=VentaItemForm, extra=3, can_delete=True
#     )

#     if request.method == 'POST':
#         venta_form = VentaForm(request.POST)
#         formset = VentaItemFormSet(request.POST, queryset=VentaItem.objects.none())

#         if venta_form.is_valid() and formset.is_valid():
#             venta = venta_form.save(commit=False)
#             venta.dependienta = request.user  # Asigna la dependienta actual
#             venta.save()

#             for form in formset:
#                 if form.cleaned_data:
#                     item = form.save(commit=False)
#                     item.venta = venta
#                     item.save()

#             return redirect('gestionar_venta')  # Redirige al listado de ventas

#     else:
#         venta_form = VentaForm()
#         formset = VentaItemFormSet(queryset=VentaItem.objects.none())

#     return render(request, 'nueva_venta.html', {
#         'venta_form': venta_form,
#         'formset': formset,
#     })