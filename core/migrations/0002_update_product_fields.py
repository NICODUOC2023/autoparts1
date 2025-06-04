from django.db import migrations, models
import random

def update_product_fields(apps, schema_editor):
    Product = apps.get_model('core', 'Product')
    for product in Product.objects.all():
        # Generar una descripción detallada
        description = f"""
{product.name} - {product.brand}

Características:
- Código de producto: {product.product_code}
- Código de referencia: {product.code}
- Marca: {product.brand}
- Disponibilidad: Inmediata

Descripción:
Este repuesto {product.name} de la marca {product.brand} es un componente de alta calidad 
diseñado específicamente para garantizar un rendimiento óptimo y duradero. Fabricado bajo 
estrictos estándares de calidad, este producto ofrece la mejor relación calidad-precio 
del mercado.

Especificaciones:
- Material de primera calidad
- Diseño preciso para un ajuste perfecto
- Durabilidad garantizada
- Cumple con estándares internacionales

Recomendaciones:
- Instalación por personal calificado
- Seguir las especificaciones del fabricante
- Mantener el producto en su empaque original hasta su instalación
"""
        
        # Actualizar descripción y stock
        product.description = description.strip()
        product.stock = random.randint(30, 50)
        product.save()

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='description',
            field=models.TextField(blank=True, default='', verbose_name='Descripción'),
            preserve_default=False,
        ),
        migrations.RunPython(update_product_fields),
    ] 