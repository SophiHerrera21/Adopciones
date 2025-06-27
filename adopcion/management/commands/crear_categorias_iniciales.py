from django.core.management.base import BaseCommand
from adopcion.models import CategoriaDonacion

class Command(BaseCommand):
    help = 'Crea categorías iniciales para donaciones'

    def handle(self, *args, **options):
        categorias = [
            {
                'nombre': 'Alimentos',
                'descripcion': 'Comida para perros y gatos, concentrado, comida húmeda, etc.'
            },
            {
                'nombre': 'Medicamentos',
                'descripcion': 'Medicamentos veterinarios, vitaminas, suplementos'
            },
            {
                'nombre': 'Juguetes',
                'descripcion': 'Juguetes para mascotas, pelotas, mordedores, etc.'
            },
            {
                'nombre': 'Accesorios',
                'descripcion': 'Collares, correas, camas, transportadoras, etc.'
            },
            {
                'nombre': 'Limpieza',
                'descripcion': 'Shampoo, jabón, productos de limpieza para mascotas'
            },
            {
                'nombre': 'Equipos Médicos',
                'descripcion': 'Equipos veterinarios, jeringas, vendas, etc.'
            },
            {
                'nombre': 'Materiales de Construcción',
                'descripcion': 'Materiales para mejorar las instalaciones del refugio'
            },
            {
                'nombre': 'Otros',
                'descripcion': 'Otros insumos no categorizados'
            }
        ]

        for categoria_data in categorias:
            categoria, created = CategoriaDonacion.objects.get_or_create(
                nombre=categoria_data['nombre'],
                defaults={'descripcion': categoria_data['descripcion']}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Categoría "{categoria.nombre}" creada exitosamente')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Categoría "{categoria.nombre}" ya existe')
                )

        self.stdout.write(
            self.style.SUCCESS('Proceso de creación de categorías completado')
        ) 