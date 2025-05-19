from django.core.management.base import BaseCommand
from django.utils.text import slugify
from core.models import Category

class Command(BaseCommand):
    help = 'Creates sample categories'

    def handle(self, *args, **kwargs):
        # Main categories
        main_categories = [
            {
                'name': 'Motores y Componentes',
                'subcategories': [
                    'Filtros de Aceite',
                    'Filtros de Aire',
                    'Bujías',
                    'Correas de Distribución'
                ]
            },
            {
                'name': 'Frenos y Suspensión',
                'subcategories': [
                    'Pastillas de Freno',
                    'Discos de Freno',
                    'Amortiguadores',
                    'Rótulas'
                ]
            },
            {
                'name': 'Electricidad y Baterías',
                'subcategories': [
                    'Alternadores',
                    'Baterías',
                    'Luces y Faros',
                    'Sensores y Fusibles'
                ]
            },
            {
                'name': 'Accesorios y Seguridad',
                'subcategories': [
                    'Alarmas',
                    'Cinturones de Seguridad',
                    'Cubre Asientos',
                    'Kits de Emergencia'
                ]
            }
        ]

        for main_cat in main_categories:
            # Create main category
            parent_category = Category.objects.create(
                name=main_cat['name'],
                slug=slugify(main_cat['name'])
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created main category: {parent_category.name}')
            )

            # Create subcategories
            for sub_name in main_cat['subcategories']:
                subcategory = Category.objects.create(
                    name=sub_name,
                    slug=slugify(sub_name),
                    parent=parent_category
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Created subcategory: {subcategory.name}')
                ) 