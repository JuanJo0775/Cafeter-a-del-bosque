# apps/core/commands/commands/init_data.py

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.menu.models import Category, Product
from apps.kitchen.models import KitchenStation

User = get_user_model()


class Command(BaseCommand):
    help = "Inicializa datos de prueba (idempotente). Uso: python manage.py init_data [--force] [--dry-run] [--seed-users]"

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Forzar recreación (override).')
        parser.add_argument('--dry-run', action='store_true', help='Simular sin aplicar cambios.')
        parser.add_argument('--seed-users', action='store_true', help='Crear usuarios de prueba (admin, meseros, cocineros).')

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        seed_users = options['seed_users']

        self.stdout.write("=" * 60)
        self.stdout.write(" Iniciando init_data (commands command) ")
        self.stdout.write("=" * 60)

        if dry_run:
            self.stdout.write(self.style.WARNING("MODO DRY-RUN: no se aplicarán cambios."))

        try:
            with transaction.atomic():

                # === USUARIOS (ADMIN, MESEROS, COCINEROS) ===
                if seed_users:
                    # ------------------------
                    # SUPERUSUARIO / ADMIN
                    # ------------------------
                    admin_defaults = {
                        "email": "admin@cafedelbosque.com",
                        "is_staff": True,
                        "is_superuser": True,
                    }
                    admin, created = User.objects.get_or_create(
                        username='admin',
                        defaults=admin_defaults
                    )
                    if created:
                        admin.set_password("admin123")
                        admin.role = "ADMIN"
                        admin.save()
                        self.stdout.write(self.style.SUCCESS("✓ Superusuario creado"))
                    else:
                        self.stdout.write("✓ Superusuario ya existe")

                    # ------------------------
                    # MESEROS
                    # ------------------------
                    meseros = [
                        ("maria_mesera", "María", "González", "maria@cafedelbosque.com"),
                        ("juan_mesero", "Juan", "Pérez", "juan@cafedelbosque.com"),
                    ]
                    for username, fname, lname, email in meseros:
                        u, created = User.objects.get_or_create(
                            username=username,
                            defaults={
                                "first_name": fname,
                                "last_name": lname,
                                "email": email,
                                "role": "MESERO"
                            }
                        )
                        u.set_password("mesero123")
                        u.role = "MESERO"
                        u.save()

                    self.stdout.write("✓ Meseros verificados/creados")

                    # ------------------------
                    # COCINEROS
                    # ------------------------
                    cocineros = [
                        ("carlos_chef", "Carlos", "Rodríguez", "carlos@cafedelbosque.com"),
                        ("laura_chef", "Laura", "Ramírez", "laura@cafedelbosque.com"),
                    ]
                    for username, fname, lname, email in cocineros:
                        u, created = User.objects.get_or_create(
                            username=username,
                            defaults={
                                "first_name": fname,
                                "last_name": lname,
                                "email": email,
                                "role": "COCINERO"
                            }
                        )
                        u.set_password("chef123")
                        u.role = "COCINERO"
                        u.save()

                    self.stdout.write("✓ Cocineros verificados/creados")

                    # ------------------------
                    # IMPORTANTE:
                    # No se crean usuarios CLIENTE porque ahora el cliente es anónimo
                    # y solo usa un nombre (campo: customer_name).
                    # ------------------------
                    self.stdout.write(self.style.WARNING(
                        "Clientes NO se crean porque ahora los clientes no usan login."
                    ))

                # === CATEGORÍAS Y PRODUCTOS BASE ===
                self.stdout.write("\nVerificando categorías y productos base...")

                cat_bebidas, _ = Category.objects.get_or_create(
                    name="Bebidas",
                    defaults={"category_type": "BEBIDAS", "description": "Bebidas calientes y frías"}
                )
                cat_comidas, _ = Category.objects.get_or_create(
                    name="Comidas",
                    defaults={"category_type": "COMIDAS", "description": "Platos principales"}
                )

                # Productos
                Product.objects.update_or_create(
                    name="Café Americano",
                    defaults={
                        "category": cat_bebidas,
                        "description": "Café filtrado clásico",
                        "base_price": 2.5,
                        "preparation_time": 4,
                        "is_available": True
                    }
                )
                Product.objects.update_or_create(
                    name="Sandwich Club",
                    defaults={
                        "category": cat_comidas,
                        "description": "Sandwich con vegetales y proteínas",
                        "base_price": 6.5,
                        "preparation_time": 8,
                        "is_available": True
                    }
                )

                self.stdout.write(self.style.SUCCESS("✓ Categorías y productos verificados/creados"))

                # === ESTACIONES DE COCINA ===
                KitchenStation.objects.update_or_create(
                    name="Estación Bebidas Calientes",
                    defaults={"station_type": "BEBIDAS_CALIENTES", "is_active": True}
                )
                KitchenStation.objects.update_or_create(
                    name="Estación Platos Fuertes",
                    defaults={"station_type": "PLATOS_FUERTES", "is_active": True}
                )
                KitchenStation.objects.update_or_create(
                    name="Estación Postres",
                    defaults={"station_type": "POSTRES", "is_active": True}
                )

                self.stdout.write(self.style.SUCCESS("✓ Estaciones de cocina verificadas/creadas"))

                # Si dry-run, forzamos rollback
                if dry_run:
                    raise RuntimeError("DRY-RUN: forzando rollback (no se aplicaron cambios)")

            self.stdout.write(self.style.SUCCESS("init_data completado correctamente"))

        except Exception as e:
            if dry_run and "DRY-RUN" in str(e):
                self.stdout.write(self.style.WARNING("DRY-RUN finalizado. No se aplicaron cambios."))
            else:
                self.stdout.write(self.style.ERROR(f"init_data falló: {e}"))
                raise
