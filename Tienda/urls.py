from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    inicio,
    listar_producto,
    listar_categoria,
    producto_detalle,
    listar_pregunta,
    register,
    iniciar_sesion,
    cerrar_sesion,
    ver_carrito,
    agregar_al_carrito,
    aumentar_cantidad,
    disminuir_cantidad,
    buscar_productos,
    gestionar_venta,
    nueva_venta,
    aumentar_cantidad_venta,
    disminuir_cantidad_venta,
    agregar_producto_venta,
    cancelar_venta,
    detalle_venta,
    generar_reporte_pdf,
    error_permisos,
    detalle_cuadre,
    generar_cuadre,
    listar_cuadre,
    generar_pdf_reporte_cuadre,
    nueva_entrada,
    listar_entrada,
   
    
)

urlpatterns = [

    # Página principal
    path('', inicio, name='inicio'),

    # Productos y categorías
    path('productos/', listar_producto, name='listar_todos_productos'),
    path('productos/<slug:categoria_slug>/', listar_producto, name='listar_producto'),
    path('productos/', listar_producto, name='listar_producto'),
    path('productos/categoria/<slug:categoria_slug>/', listar_producto, name='listar_producto_categoria'),
    path('productos/categoria/<slug:categoria_slug>/', listar_producto, name='producto_por_categoria'),
    path('categorias/', listar_categoria, name='listar_categoria'),
    path('producto/<int:id>/', producto_detalle, name='producto_detalle'),

    # Preguntas frecuentes
    path('preguntas-frecuentes/', listar_pregunta, name='preguntas_frecuentes'),

    # Carrito
    path('carrito/', ver_carrito, name='ver_carrito'),
    path('carrito/agregar/<int:producto_id>/', agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/aumentar/<int:item_id>/', aumentar_cantidad, name='aumentar_cantidad'),
    path('carrito/disminuir/<int:item_id>/', disminuir_cantidad, name='disminuir_cantidad'),

    # Búsqueda
    path('buscar/', buscar_productos, name='buscar_productos'),

    # Gestión de ventas
    path('ventas/', gestionar_venta, name='gestionar_venta'),
    path('ventas/nueva/', nueva_venta, name='nueva_venta'),
    path('ventas/<int:venta_id>/detalle/', detalle_venta, name='detalle_venta'),
    path('ventas/reporte_pdf/', generar_reporte_pdf, name='generar_reporte_pdf'),
    path('cuadre/<int:cuadre_id>/', detalle_cuadre, name='detalle_cuadre'),
    path('cuadre/generar/', generar_cuadre, name='generar_cuadre'),
    path('cuadre/', listar_cuadre, name='listar_cuadre'),
    path('cuadre/<int:cuadre_id>/reporte/', generar_pdf_reporte_cuadre, name='reporte_cuadre_pdf'),
    # path("venta/agregar-ajax/<int:producto_id>/", agregar_producto_ajax, name="agregar_producto_ajax"),
     path('entrada/nueva/', nueva_entrada, name='nueva_entrada'),
      path('entradas/', listar_entrada, name='listar_entrada'),

   
    # path('gastos/nuevo/', nuevo_gasto, name='nuevo_gasto'),
    
    # Manejo de errores
    path('error-permisos/', error_permisos, name='error_permisos'),

    # path('ventas/listado-productos/', listado_productos_venta, name='listado_productos_venta'),
    path('ventas/aumentar/<int:item_id>/', aumentar_cantidad_venta, name='aumentar_cantidad_venta'),
    path('ventas/disminuir/<int:item_id>/', disminuir_cantidad_venta, name='disminuir_cantidad_venta'),
    path('ventas/agregar/<int:producto_id>/', agregar_producto_venta, name='agregar_producto_venta'),
    path("cancelar-venta/", cancelar_venta, name="cancelar_venta"),



    # Autenticación y sesiones
    path('login/', iniciar_sesion, name='iniciar_sesion'),
    path('accounts/login/', lambda request: redirect('iniciar_sesion')),
    path('logout/', cerrar_sesion, name='cerrar_sesion'),
    path('register/', register, name='register'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
]

# Archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)






# from django.urls import path
# from django.contrib.auth import views as auth_views
# from django.contrib.auth import authenticate, login as auth_login
# from .views import inicio, listar_producto, listar_categoria, producto_detalle, listar_pregunta, register, iniciar_sesion, cerrar_sesion, ver_carrito, agregar_al_carrito, aumentar_cantidad, disminuir_cantidad, buscar_productos, gestionar_venta, nueva_venta, aumentar_cantidad_venta, disminuir_cantidad_venta
# from django.conf import settings
# from django.conf.urls.static import static
# from django.contrib.auth.views import LoginView
# from django.contrib.auth.views import LogoutView
# from django.shortcuts import redirect

# urlpatterns = [
#     path('', inicio, name='inicio'),
#     path('productos/', listar_producto, name='listar_todos_productos'),
#     path('productos/<slug:categoria_slug>/', listar_producto, name='listar_producto'),

#     path('productos/', listar_producto, name='listar_producto'),
#     path('productos/categoria/<slug:categoria_slug>/', listar_producto, name='listar_producto_categoria'),
#     path('productos/categoria/<slug:categoria_slug>/', listar_producto, name='producto_por_categoria'),
#     path('categorias/', listar_categoria, name='listar_categoria'),
#     path('producto/<int:id>/', producto_detalle, name='producto_detalle'),
#     path('preguntas-frecuentes/', listar_pregunta, name='preguntas_frecuentes'),
#     path('carrito/', ver_carrito, name='ver_carrito'),
#     path('carrito/agregar/<int:producto_id>/', agregar_al_carrito, name='agregar_al_carrito'),
#     path('carrito/aumentar/<int:item_id>/', aumentar_cantidad, name='aumentar_cantidad'),
#     path('carrito/disminuir/<int:item_id>/', disminuir_cantidad, name='disminuir_cantidad'),
#     path('buscar/', buscar_productos, name='buscar_productos'),
#     path('ventas/', gestionar_venta, name='gestionar_venta'),
#     path('ventas/nueva/', nueva_venta, name='nueva_venta'),
#     # path('ventas/listado-productos/', listado_productos_venta, name='listado_productos_venta'),
#     # Esta es la URL para ajustar la cantidad de un producto en una venta temporal
#     path('ventas/aumentar/<int:item_id>/', aumentar_cantidad_venta, name='aumentar_cantidad_venta'),
#     path('ventas/disminuir/<int:item_id>/', disminuir_cantidad_venta, name='disminuir_cantidad_venta'),


    
#     # Sistema de autenticacion y manejo de sesiones
#     path('login/', iniciar_sesion, name='iniciar_sesion'),
#     path('accounts/login/', lambda request: redirect('iniciar_sesion')),
    
#     path('logout/', cerrar_sesion, name='cerrar_sesion'),  # Logout
#     path('register/', register, name='register'),  # URL para el registro
    
    
#     path('login/', LoginView.as_view(template_name='login.html'), name='login'),
# ]

# if settings.DEBUG:  # Solo en desarrollo
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)