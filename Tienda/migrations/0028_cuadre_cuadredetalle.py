# Generated by Django 5.1.4 on 2025-07-09 20:19

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Tienda', '0027_venta_motivo_gasto_alter_venta_forma_pago'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Cuadre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(unique=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CuadreDetalle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad_inicial', models.PositiveIntegerField()),
                ('entradas', models.PositiveIntegerField(default=0)),
                ('cantidad_gasto', models.PositiveIntegerField(default=0)),
                ('precio_unitario_gasto', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('importe_gasto', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('cantidad_transferencia', models.PositiveIntegerField(default=0)),
                ('precio_unitario_transferencia', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('importe_transferencia', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('cantidad_efectivo', models.PositiveIntegerField(default=0)),
                ('precio_unitario_efectivo', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('importe_efectivo', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('importe_total_producto', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('cantidad_final', models.PositiveIntegerField()),
                ('cuadre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='Tienda.cuadre')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Tienda.producto')),
            ],
        ),
    ]
