from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Categoria, Producto, Pregunta, Carrito, CarritoItem, Venta, VentaItem, VentaTemporal, VentaTemporalItem, Cuadre, CuadreDetalle, Entrada
from .forms import VentaForm, VentaItemForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login as auth_login
from .forms import RegistroForm,  LoginForm, EntradaForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import modelformset_factory
from django.utils import timezone
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.template.loader import get_template
from decimal import Decimal
from datetime import datetime
from django.db.models import Sum
from functools import wraps
from django.db.models import F
from django.db import transaction, IntegrityError
from collections import defaultdict
from django.utils.timezone import localtime



 
def permiso_dependiente_o_superusuario(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.is_superuser or request.user.groups.filter(name='Dependiente').exists()):
            return view_func(request, *args, **kwargs)
        return redirect('error_permisos')
    return _wrapped_view




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
        categoria = None
        productos = Producto.objects.filter(venta_de_garaje=True, deshabilitado=False)
    elif categoria_slug and categoria_slug != 'todo':
        categoria = get_object_or_404(Categoria, slug=categoria_slug)
        productos = Producto.objects.filter(categoria=categoria, deshabilitado=False)
    else:
        categoria = None
        productos = Producto.objects.filter(deshabilitado=False)

    # Actualizar la disponibilidad de cada producto según su stock
    for producto in productos:
        if producto.cantidad == 0 and producto.disponibilidad:
            producto.disponibilidad = False
            producto.save()
        elif producto.cantidad > 0 and not producto.disponibilidad:
            producto.disponibilidad = True
            producto.save()

    # Ordenamiento opcional
    ordenar = request.GET.get('ordenar', None)
    if ordenar == 'precio_asc':
        productos = productos.order_by('precio')
    elif ordenar == 'precio_desc':
        productos = productos.order_by('-precio')
    elif ordenar == 'nuevo':
        productos = productos.order_by('-fecha_creado')

    # Paginación
    paginator = Paginator(productos, 18)
    page_number = request.GET.get('page')
    productos_page = paginator.get_page(page_number)

    return render(request, 'listar_productos.html', {
        'categoria': categoria,
        'categoria_slug': categoria_slug,
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

    # Filtrar productos activos cuyo nombre contenga el término buscado
    resultados = Producto.objects.filter(
        nombre__icontains=query,
        deshabilitado=False
    )

    # Renderizar los resultados en la plantilla correspondiente
    return render(request, 'buscar_resultados.html', {
        'query': query,
        'resultados': resultados
    })

    
   


# Error de permisos
def error_permisos(request):
    return render(request, 'error_permisos.html')



# Vista para gestionar las ventas
@permiso_dependiente_o_superusuario
@login_required
def gestionar_venta(request):
    if request.user.is_superuser:
        ventas_lista = Venta.objects.all().order_by('-fecha')
    else:
        ventas_lista = Venta.objects.filter(dependienta=request.user).order_by('-fecha')

    paginator = Paginator(ventas_lista, 20)  # Puedes ajustar la cantidad por página
    page_number = request.GET.get("page")
    ventas = paginator.get_page(page_number)

    return render(request, 'gestionar_venta.html', {'ventas': ventas})


# Vista para detalle de venta
@permiso_dependiente_o_superusuario
@login_required
def detalle_venta(request, venta_id):
    if request.user.is_superuser:
        venta = get_object_or_404(Venta, id=venta_id)
    else:
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


# Vista para exportar a pdf
@permiso_dependiente_o_superusuario
def generar_reporte_pdf(request):
    filtro = request.GET.get('filtro')
    valor = request.GET.get('valor')

    # Filtrar ventas según el filtro y valor
    ventas_filtradas = filtrar_ventas_por_filtro(filtro, valor)

    # Calcular totales según forma de pago
    total_efectivo = 0
    total_transferencia = 0
    total_gasto = 0

    for venta in ventas_filtradas:
        if venta.forma_pago == 'efectivo':
            total_efectivo += float(venta.total_a_pagar)
        elif venta.forma_pago == 'transferencia':
            total_transferencia += float(venta.total_a_pagar)
        elif venta.forma_pago == 'gasto':
            total_gasto += float(venta.total_a_pagar)

    total_general = total_efectivo + total_transferencia
    # Contexto para la plantilla
    context = {
        'ventas': ventas_filtradas,
        'filtro': filtro,
        'valor': valor,
        'total_efectivo': total_efectivo,
        'total_transferencia': total_transferencia,
        'total_gasto': total_gasto,
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


@login_required
@permiso_dependiente_o_superusuario

def filtrar_ventas_por_filtro(filtro, valor, user):
    """
    Filtra las ventas por tipo de filtro y usuario.
    - Superusuarios ven todas las ventas.
    - Usuarios del grupo 'Dependiente' solo ven sus propias ventas.
    """
    if not filtro or not valor:
        return Venta.objects.none()  # Si falta información, no devuelve nada

    ventas = Venta.objects.all()

    # Filtrar por usuario si no es superusuario
    if not user.is_superuser:
        ventas = ventas.filter(dependienta=user)

    try:
        if filtro == 'dia':
            fecha = datetime.strptime(valor, '%Y-%m-%d').date()
            ventas = ventas.filter(fecha__date=fecha)

        elif filtro == 'mes':
            año, mes = map(int, valor.split('-'))
            ventas = ventas.filter(fecha__year=año, fecha__month=mes)

        elif filtro == 'año':
            año = int(valor)
            ventas = ventas.filter(fecha__year=año)

    except Exception as e:
        print(f"Error en filtrado: {e}")
        return Venta.objects.none()

    return ventas.order_by('-fecha')
    

# Vista para la nueva venta
@login_required
@permiso_dependiente_o_superusuario
def nueva_venta(request):
    # Obtener o crear una venta temporal por usuario
    venta_temp, _ = VentaTemporal.objects.get_or_create(dependienta=request.user)
    items_actuales = venta_temp.items.select_related("producto")

    # Total con precio normal y efectivo
    precio_total = sum(item.producto.precio * item.cantidad for item in items_actuales)
    precio_total_efectivo = sum(item.producto.precio_efectivo * item.cantidad for item in items_actuales)

    # Subtotal por ítem en efectivo
    for item in items_actuales:
        item.subtotal_efectivo = item.producto.precio_efectivo * item.cantidad

    # Buscar productos
    consulta = request.GET.get('buscar', '')
    productos_disponibles = Producto.objects.filter(disponibilidad=True, deshabilitado=False)
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
            codigo_transferencia = venta_form.cleaned_data.get("codigo_transferencia")
            motivo_gasto = venta_form.cleaned_data.get("motivo_gasto")

            # Total a pagar según forma de pago
            if forma_pago == "efectivo":
                total_a_pagar = precio_total_efectivo
            else:
                total_a_pagar = precio_total

            try:
                with transaction.atomic():
                    # Crear la venta
                    venta = Venta.objects.create(
                        dependienta=request.user,
                        fecha=timezone.localtime(),
                        forma_pago=forma_pago,
                        codigo_transferencia=codigo_transferencia,
                        total_a_pagar=total_a_pagar,
                        motivo_gasto=motivo_gasto if forma_pago == "gasto" else None
                    )

                    # Crear los ítems y descontar stock con F()
                    for item in items_actuales:
                        VentaItem.objects.create(
                            venta=venta,
                            producto=item.producto,
                            cantidad=item.cantidad,
                            precio_unitario=item.producto.precio,
                            precio_unitario_efectivo=item.producto.precio_efectivo
                        )
                        Producto.objects.filter(id=item.producto.id).update(
                            cantidad=F('cantidad') - item.cantidad
                        )

                    # Limpiar venta temporal
                    venta_temp.delete()

                    messages.success(request, "✅ Venta registrada correctamente.")
                    return redirect("gestionar_venta")

            except IntegrityError as e:
                messages.error(request, "❌ Error de integridad al registrar la venta. Intente nuevamente.")
                # En producción podrías loguear el error con logging o Sentry si deseas.
                return redirect("nueva_venta")
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




# def nueva_venta(request):
#     # Obtener o crear una venta temporal por usuario
#     venta_temp, _ = VentaTemporal.objects.get_or_create(dependienta=request.user)
#     items_actuales = venta_temp.items.select_related("producto")

#     # Total con precio normal y efectivo
#     precio_total = sum(item.producto.precio * item.cantidad for item in items_actuales)
#     precio_total_efectivo = sum(item.producto.precio_efectivo * item.cantidad for item in items_actuales)

#     # Subtotal por ítem en efectivo
#     for item in items_actuales:
#         item.subtotal_efectivo = item.producto.precio_efectivo * item.cantidad

#     # Buscar productos
#     consulta = request.GET.get('buscar', '')
#     productos_disponibles = Producto.objects.filter(disponibilidad=True, deshabilitado=False)
#     if consulta:
#         productos_disponibles = productos_disponibles.filter(nombre__icontains=consulta)

#     # Paginación
#     paginator = Paginator(productos_disponibles, 20)
#     page_number = request.GET.get("page")
#     page_obj = paginator.get_page(page_number)

#     if request.method == "POST":
#         venta_form = VentaForm(request.POST)
#         if venta_form.is_valid():
#             forma_pago = venta_form.cleaned_data["forma_pago"]
#             codigo_transferencia = venta_form.cleaned_data.get("codigo_transferencia")
#             motivo_gasto = venta_form.cleaned_data.get("motivo_gasto")

#             # Total a pagar según forma de pago (gasto se trata como transferencia)
#             if forma_pago == "efectivo":
#                 total_a_pagar = precio_total_efectivo
#             else:
#                 total_a_pagar = precio_total  # incluye gasto y transferencia

#             # Crear la venta
#             venta = Venta.objects.create(
#                 dependienta=request.user,
#                 fecha=timezone.now(),
#                 forma_pago=forma_pago,
#                 codigo_transferencia=codigo_transferencia,
#                 total_a_pagar=total_a_pagar,
#                 motivo_gasto=motivo_gasto if forma_pago == "gasto" else None
#             )

#             # Crear los ítems y descontar del stock
#             for item in items_actuales:
#                 VentaItem.objects.create(
#                     venta=venta,
#                     producto=item.producto,
#                     cantidad=item.cantidad,
#                     precio_unitario=item.producto.precio,
#                     precio_unitario_efectivo=item.producto.precio_efectivo
#                 )
#                 item.producto.cantidad -= item.cantidad
#                 item.producto.save()

#             # Limpiar venta temporal
#             venta_temp.delete()
#             messages.success(request, "✅ Venta registrada correctamente.")
#             return redirect("gestionar_venta")
#     else:
#         venta_form = VentaForm()

#     context = {
#         "usuario": request.user,
#         "productos": page_obj,
#         "items": items_actuales,
#         "precio_total": precio_total,
#         "precio_total_efectivo": precio_total_efectivo,
#         "venta_form": venta_form,
#         "buscar": consulta
#     }
#     return render(request, "nueva_venta.html", context)



# # Vista para agregar producto AJAX
# @login_required
# @permiso_dependiente_o_superusuario
# def agregar_producto_ajax(request, producto_id):
#     if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
#         cantidad = int(request.POST.get("cantidad", 1))
#         producto = get_object_or_404(Producto, id=producto_id)
#         venta_temp, _ = VentaTemporal.objects.get_or_create(dependienta=request.user)

#         if cantidad > producto.cantidad:
#             return JsonResponse({"success": False, "mensaje": "No hay suficiente stock."})

#         item, created = VentaTemporalItem.objects.get_or_create(
#             venta_temporal=venta_temp,
#             producto=producto
#         )
#         item.cantidad += cantidad
#         item.save()

#         return JsonResponse({
#             "success": True,
#             "mensaje": f"{cantidad} unidades de '{producto.nombre}' añadidas.",
#             "nueva_cantidad": item.cantidad
#         })
#     return JsonResponse({"success": False, "mensaje": "Solicitud inválida."})



# Vista para agregar un producto (evita doble procesamiento)
@login_required
@permiso_dependiente_o_superusuario
def agregar_producto_venta(request, producto_id):
    if request.method == "POST":
        cantidad_deseada = int(request.POST.get("cantidad", 1))

        if cantidad_deseada < 1:
            messages.warning(request, "La cantidad debe ser al menos 1.")
            return redirect("nueva_venta")

        venta_temp, _ = VentaTemporal.objects.get_or_create(dependienta=request.user)
        producto = get_object_or_404(Producto, id=producto_id)

        if cantidad_deseada > producto.cantidad:
            messages.warning(request, f"No hay suficiente stock para '{producto.nombre}'.")
            return redirect("nueva_venta")

        item, created = VentaTemporalItem.objects.get_or_create(
            venta_temporal=venta_temp,
            producto=producto
        )

        nueva_cantidad = item.cantidad + cantidad_deseada
        if nueva_cantidad > producto.cantidad:
            messages.warning(request, f"Solo quedan {producto.cantidad - item.cantidad} unidades disponibles de '{producto.nombre}'.")
        else:
            item.cantidad = nueva_cantidad
            item.save()
            messages.success(request, f"Se añadieron {cantidad_deseada} unidad(es) de '{producto.nombre}' a la venta.")

    return redirect("nueva_venta")

# def agregar_producto_venta(request, producto_id):
#     if request.method == "POST":
#         venta_temp, _ = VentaTemporal.objects.get_or_create(dependienta=request.user)
#         producto = get_object_or_404(Producto, id=producto_id)

#         item, created = VentaTemporalItem.objects.get_or_create(
#             venta_temporal=venta_temp,
#             producto=producto
#         )

#         if item.cantidad + 1 > producto.cantidad:
#             messages.warning(request, f"No hay más stock disponible para '{producto.nombre}'.")
#         else:
#             item.cantidad += 1
#             item.save()
#             messages.success(request, f"Producto '{producto.nombre}' añadido a la venta.")

#     return redirect("nueva_venta")



# Aumentar cantidad de un producto en la venta temporal
@login_required
@permiso_dependiente_o_superusuario
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
@permiso_dependiente_o_superusuario
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
@permiso_dependiente_o_superusuario

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




# Vista para realizar una nueva entrada de un producto
@login_required
@permiso_dependiente_o_superusuario
def nueva_entrada(request):
    productos = Producto.objects.filter(deshabilitado=False)
    producto_id = request.GET.get('producto')
    producto_seleccionado = None
    form = None

    if producto_id:
        producto_seleccionado = get_object_or_404(Producto, id=producto_id)
        ultima_entrada = Entrada.objects.filter(producto=producto_seleccionado).order_by('-fecha_entrada').first()

        if request.method == 'POST':
            form = EntradaForm(request.POST)
            if form.is_valid():
                entrada = form.save(commit=False)
                # Forzamos asignar el producto seleccionado
                entrada.producto = producto_seleccionado
                entrada.save()
                messages.success(request, "Entrada registrada correctamente.")
                return redirect('nueva_entrada')
        else:
            # Preparamos datos iniciales con la última entrada (excepto cantidad)
            if ultima_entrada:
                initial_data = {
                    "precio_costo": ultima_entrada.precio_costo,
                    "precio_venta": ultima_entrada.precio_venta,
                    "precio_venta_efectivo": ultima_entrada.precio_venta_efectivo,
                    "nuevo_codigo": ultima_entrada.nuevo_codigo,
                    "nueva_fecha_vencimiento": ultima_entrada.nueva_fecha_vencimiento,
                    "nueva_cantidad": None,  # vacía para que ingreses cantidad nueva
                }
                form = EntradaForm(initial=initial_data)
            else:
                form = EntradaForm()

    else:
        # Si no hay producto seleccionado, formulario vacío
        form = EntradaForm()
    
    context = {
        "productos": productos,
        "form": form,
        "producto_seleccionado": producto_seleccionado,
    }
    return render(request, "nueva_entrada.html", context)



# Vista para listar las entradas
@login_required
@permiso_dependiente_o_superusuario
def listar_entrada(request):
    entradas_lista = Entrada.objects.select_related('producto').order_by('-fecha_entrada')
    
    paginator = Paginator(entradas_lista, 20)  # 20 entradas por página
    page_number = request.GET.get('page')
    entradas = paginator.get_page(page_number)

    context = {
        "entradas": entradas,
    }
    return render(request, "listar_entrada.html", context)



# Vista para realizar cuadre del d'ia 
@login_required
@permiso_dependiente_o_superusuario
def generar_cuadre(request):
    hoy = localtime().date()  # Cambio aquí ✅
    try:
        with transaction.atomic():
            productos = Producto.objects.all()
            cuadre = Cuadre.objects.create(fecha=hoy, usuario=request.user)

            entradas = Entrada.objects.filter(fecha_entrada__date=hoy).values('producto_id').annotate(total=Sum('nueva_cantidad'))
            ventas_dia = Venta.objects.filter(fecha__date=hoy)
            items_dia = VentaItem.objects.filter(venta__in=ventas_dia).select_related('producto', 'venta')

            entradas_map = {e['producto_id']: e['total'] for e in entradas}

            resumen = defaultdict(lambda: {
                'gasto': 0,
                'transferencia': 0,
                'efectivo': 0
            })

            for item in items_dia:
                resumen[item.producto_id][item.venta.forma_pago] += item.cantidad

            for producto in productos:
                pid = producto.id
                cantidad_gasto = resumen[pid]['gasto']
                cantidad_transferencia = resumen[pid]['transferencia']
                cantidad_efectivo = resumen[pid]['efectivo']

                precio_gasto = producto.precio
                precio_transferencia = producto.precio
                precio_efectivo = producto.precio_efectivo

                importe_gasto = cantidad_gasto * precio_gasto
                importe_transferencia = cantidad_transferencia * precio_transferencia
                importe_efectivo = cantidad_efectivo * precio_efectivo

                importe_total_producto = importe_transferencia + importe_efectivo
                total_vendido = cantidad_gasto + cantidad_transferencia + cantidad_efectivo
                total_entradas = entradas_map.get(pid, 0)
                cantidad_inicial = max(producto.cantidad + total_vendido - total_entradas, 0)
                cantidad_final = producto.cantidad

                CuadreDetalle.objects.create(
                    cuadre=cuadre,
                    producto=producto,
                    cantidad_inicial=cantidad_inicial,
                    entradas=total_entradas,
                    cantidad_gasto=cantidad_gasto,
                    precio_unitario_gasto=precio_gasto,
                    importe_gasto=importe_gasto,
                    cantidad_transferencia=cantidad_transferencia,
                    precio_unitario_transferencia=precio_transferencia,
                    importe_transferencia=importe_transferencia,
                    cantidad_efectivo=cantidad_efectivo,
                    precio_unitario_efectivo=precio_efectivo,
                    importe_efectivo=importe_efectivo,
                    importe_total_producto=importe_total_producto,
                    cantidad_final=cantidad_final,
                )

        messages.success(request, f"✅ Cuadre generado exitosamente para el día {hoy}.")
        return redirect("detalle_cuadre", cuadre.id)

    except Exception as e:
        messages.error(request, f"❌ Error al generar el cuadre: {str(e)}")
        return redirect("listar_cuadres")




# Vista para el detalle del cuadre
@login_required
@permiso_dependiente_o_superusuario
def detalle_cuadre(request, cuadre_id):
    cuadre = get_object_or_404(Cuadre, id=cuadre_id)
    detalles = cuadre.detalles.select_related('producto').all()

    context = {
        'cuadre': cuadre,
        'detalles': detalles,
    }
    return render(request, 'detalle_cuadre.html', context)



@login_required
@permiso_dependiente_o_superusuario
def listar_cuadre(request):
    cuadres_lista = Cuadre.objects.select_related('usuario').order_by('-fecha', '-creado_en')
    paginator = Paginator(cuadres_lista, 10)  # 10 cuadres por página

    page_number = request.GET.get('page')
    cuadres = paginator.get_page(page_number)

    context = {
        'cuadres': cuadres,
    }
    return render(request, 'listar_cuadre.html', context)



# Vista para generar el reporte del cuadre en pdf
@login_required
@permiso_dependiente_o_superusuario
def generar_pdf_reporte_cuadre(request, cuadre_id):
    cuadre = get_object_or_404(Cuadre, id=cuadre_id)
    detalles = cuadre.detalles.select_related('producto').all()

    total_efectivo = detalles.aggregate(suma=Sum('importe_efectivo'))['suma'] or 0
    total_transferencia = detalles.aggregate(suma=Sum('importe_transferencia'))['suma'] or 0
    total_gasto = detalles.aggregate(suma=Sum('importe_gasto'))['suma'] or 0
    total_general = total_efectivo + total_transferencia

    context = {
        'cuadre': cuadre,
        'detalles': detalles,
        'ahora': timezone.now(),
        'request': request,
        'total_efectivo': total_efectivo,
        'total_transferencia': total_transferencia,
        'total_gasto': total_gasto,
        'total_general': total_general,
    }

    template = get_template('reporte_cuadre_pdf.html')
    html = template.render(context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="reporte_cuadre_{cuadre.fecha}_{cuadre.id}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Ocurrió un error al generar el PDF', status=500)
    return response


# # Vista para registrar un nuevo gasto
# @login_required
# def nuevo_gasto(request):
#     # Filtrar productos disponibles y no deshabilitados
#     productos_disponibles = Producto.objects.filter(disponibilidad=True, deshabilitado=False)

#     # Búsqueda
#     consulta = request.GET.get('buscar', '')
#     if consulta:
#         productos_disponibles = productos_disponibles.filter(nombre__icontains=consulta)

#     # Paginación
#     paginator = Paginator(productos_disponibles, 20)
#     page_number = request.GET.get("page")
#     page_obj = paginator.get_page(page_number)

#     # Procesamiento del formulario POST
#     if request.method == 'POST':
#         gasto_form = GastoForm(request.POST)
#         if gasto_form.is_valid():
#             gasto = gasto_form.save(commit=False)
#             gasto.responsable = request.user  # ✅ Campo obligatorio
#             gasto.fecha = timezone.now()
#             gasto.save()

#             # Obtener productos seleccionados y sus cantidades
#             productos = request.POST.getlist('producto_id')
#             cantidades = request.POST.getlist('cantidad')

#             for pid, cant in zip(productos, cantidades):
#                 try:
#                     producto = Producto.objects.get(id=pid, deshabilitado=False)
#                     cantidad = int(cant)
#                     if cantidad > 0 and producto.cantidad >= cantidad:
#                         # Crear el gasto del producto
#                         GastoItem.objects.create(
#                             gasto=gasto,
#                             producto=producto,
#                             cantidad=cantidad
#                         )
#                         # Descontar del stock
#                         producto.cantidad -= cantidad
#                         producto.save()
#                 except Exception:
#                     continue  # Silenciar errores puntuales por seguridad

#             messages.success(request, "✅ Gasto registrado correctamente.")
#             return redirect('gestionar_venta')
#     else:
#         gasto_form = GastoForm()

#     # Renderizar el formulario con los productos paginados
#     return render(request, 'nuevo_gasto.html', {
#         'form': gasto_form,
#         'productos': page_obj,
#         'buscar': consulta
#     })