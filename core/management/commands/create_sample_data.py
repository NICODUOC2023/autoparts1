from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Product, Price, Category

class Command(BaseCommand):
    help = 'Creates sample automotive products and prices'

    def handle(self, *args, **kwargs):
        # Create sample products
        products = [
            {
                'product_code': 'MOT001',
                'brand': 'Toyota',
                'code': 'TOY-M001',
                'name': 'Motor 2.0L 4 Cilindros',
                'price': 2500000
            },
            {
                'product_code': 'FRE001',
                'brand': 'Brembo',
                'code': 'BRE-F001',
                'name': 'Kit de Frenos Delanteros',
                'price': 450000
            },
            {
                'product_code': 'BAT001',
                'brand': 'Bosch',
                'code': 'BOS-B001',
                'name': 'Batería 12V 60Ah',
                'price': 180000
            }
        ]

        for product_data in products:
            price_value = product_data.pop('price')  # Remove price from product data
            
            # Try to get existing product or create new one
            product, created = Product.objects.get_or_create(
                product_code=product_data['product_code'],
                defaults=product_data
            )
            
            # Create a new price for the product
            Price.objects.create(
                product=product,
                date=timezone.now(),
                value=price_value
            )
            
            action = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(f'{action} product {product.name} with price ${price_value:,}')
            ) 