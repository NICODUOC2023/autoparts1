from django.core.management.base import BaseCommand
from core.models import Product
import random

class Command(BaseCommand):
    help = 'Updates product descriptions with compatibility information'

    def handle(self, *args, **kwargs):
        # Car brands and their models with years
        car_compatibility = {
            'Suzuki': [
                ('Swift', '2018-2023'),
                ('Vitara', '2015-2023'),
                ('Baleno', '2016-2023'),
                ('S-Cross', '2017-2023'),
            ],
            'Mazda': [
                ('3', '2019-2023'),
                ('CX-5', '2017-2023'),
                ('6', '2018-2023'),
                ('CX-30', '2020-2023'),
            ],
            'Chevrolet': [
                ('Onix', '2019-2023'),
                ('Cruze', '2016-2023'),
                ('Tracker', '2020-2023'),
                ('Captiva', '2018-2023'),
            ],
            'Nissan': [
                ('Versa', '2020-2023'),
                ('Sentra', '2020-2023'),
                ('X-Trail', '2017-2023'),
                ('Kicks', '2021-2023'),
            ],
            'Audi': [
                ('A3', '2017-2023'),
                ('Q3', '2019-2023'),
                ('A4', '2016-2023'),
                ('Q5', '2018-2023'),
            ],
        }

        products = Product.objects.all()
        
        for product in products:
            # Randomly select 2-3 car brands
            selected_brands = random.sample(list(car_compatibility.keys()), random.randint(2, 3))
            compatibility_text = []
            
            for brand in selected_brands:
                # For each brand, randomly select 1-2 models
                selected_models = random.sample(car_compatibility[brand], random.randint(1, 2))
                for model, years in selected_models:
                    compatibility_text.append(f"{brand} {model} ({years})")
            
            # Create the description
            base_description = product.description or ""
            compatibility_info = "\n\nCompatible con los modelos:\n- " + "\n- ".join(compatibility_text)
            
            # Update the product
            product.description = base_description + compatibility_info
            product.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Updated description for product: {product.name}')
            ) 