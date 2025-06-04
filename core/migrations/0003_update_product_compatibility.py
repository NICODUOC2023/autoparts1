from django.db import migrations
import random

def update_product_compatibility(apps, schema_editor):
    Product = apps.get_model('core', 'Product')
    
    # Lista de marcas y modelos comunes
    vehicle_models = {
        'Chevrolet': ['Spark', 'Sail', 'Captiva', 'Cruze', 'Orlando', 'Sonic', 'Tracker'],
        'Nissan': ['Qashqai', 'X-Trail', 'Versa', 'Sentra', 'Kicks', 'March'],
        'Mazda': ['3', '6', 'CX-3', 'CX-5', 'CX-30', 'BT-50'],
        'Suzuki': ['Swift', 'Vitara', 'Baleno', 'S-Cross', 'Jimny'],
        'Toyota': ['Corolla', 'RAV4', 'Yaris', 'Hilux', 'Land Cruiser'],
        'Hyundai': ['Accent', 'Tucson', 'Santa Fe', 'Elantra', 'i10', 'i20'],
        'Kia': ['Rio', 'Sportage', 'Cerato', 'Morning', 'Sorento']
    }

    for product in Product.objects.all():
        # Obtener el contenido actual de la descripción
        current_description = product.description
        
        # Si ya tiene una línea de compatibilidad, no la agregamos de nuevo
        if "Compatible con los modelos" not in current_description:
            # Seleccionar una marca aleatoria y 1-3 modelos aleatorios de esa marca
            brand = random.choice(list(vehicle_models.keys()))
            models = random.sample(vehicle_models[brand], k=random.randint(1, 3))
            
            # Generar años aleatorios entre 2000 y 2024
            years = sorted(random.sample(range(2000, 2025), k=random.randint(1, 3)))
            years_str = ", ".join(str(year) for year in years)
            
            # Crear la línea de compatibilidad
            compatibility_line = f"\nCompatible con los modelos {brand} {', '.join(models)} ({years_str})"
            
            # Agregar la línea de compatibilidad antes de las recomendaciones
            parts = current_description.split("Recomendaciones:")
            if len(parts) == 2:
                new_description = parts[0] + compatibility_line + "\n\nRecomendaciones:" + parts[1]
                product.description = new_description
                product.save()

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_update_product_fields'),
    ]

    operations = [
        migrations.RunPython(update_product_compatibility),
    ] 