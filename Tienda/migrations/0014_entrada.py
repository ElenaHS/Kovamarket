# Generated by Django 5.1.4 on 2025-06-10 18:44

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Tienda', '0013_producto_codigo_alter_producto_precio'),
    ]

    operations = [
        migrations.CreateModel(
            name='Entrada',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('precio_costo', models.DecimalField(decimal_places=2, max_digits=10)),
                ('precio_venta', models.DecimalField(decimal_places=2, max_digits=10)),
                ('nueva_cantidad', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('nuevo_codigo', models.CharField(max_length=100)),
                ('fecha_entrada', models.DateTimeField(auto_now_add=True)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entradas', to='Tienda.producto')),
            ],
            options={
                'ordering': ['-fecha_entrada'],
            },
        ),
    ]
