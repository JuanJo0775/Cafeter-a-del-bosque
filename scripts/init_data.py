"""
Script para inicializar datos de prueba del sistema Cafetería del Bosque
Ejecutar: python manage.py shell < scripts/init_data.py
"""

from apps.users.models import User
from apps.menu.models import Category, Product
from apps.kitchen.models import KitchenStation

print("=" * 60)
print(" Inicializando datos del sistema Cafetería del Bosque ")
print("=" * 60)

# ==========================================================
# 1. CREAR USUARIOS
# ==========================================================
print("\n1) Creando usuarios...\n")

# --- Superusuario (admin del sistema) ---
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username="admin",
        email="admin@cafedelbosque.com",
        password="admin123"
    )
    admin.role = "ADMIN"
    admin.save()
    print("✓ Superusuario creado")
else:
    print("✓ Superusuario ya existe")

# --- Meseros ---
meseros_data = [
    ("maria_mesera", "María", "González", "maria@cafedelbosque.com"),
    ("juan_mesero", "Juan", "Pérez", "juan@cafedelbosque.com"),
]

for username, fname, lname, email in meseros_data:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": fname,
            "last_name": lname,
            "email": email,
            "role": "MESERO"
        }
    )
    user.set_password("mesero123")
    user.save()

print("✓ Meseros creados")

# --- Cocineros ---
cocineros_data = [
    ("carlos_chef", "Carlos", "Rodríguez", "carlos@cafedelbosque.com"),
    ("laura_chef", "Laura", "Ramírez", "laura@cafedelbosque.com"),
]

for username, fname, lname, email in cocineros_data:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": fname,
            "last_name": lname,
            "email": email,
            "role": "COCINERO"
        }
    )
    user.set_password("chef123")
    user.save()

print("✓ Cocineros creados")

# --- Clientes ---
clientes_data = [
    ("ana_cliente", "Ana", "Martínez", "ana@email.com"),
    ("pedro_cliente", "Pedro", "López", "pedro@email.com"),
    ("sofia_cliente", "Sofía", "Ramírez", "sofia@email.com"),
]

for username, fname, lname, email in clientes_data:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": fname,
            "last_name": lname,
            "email": email,
            "role": "CLIENTE"
        }
    )
    user.set_password("cliente123")
    user.save()

print("✓ Clientes creados")


# ==========================================================
# 2. CATEGORÍAS DEL MENÚ
# ==========================================================
print("\n2) Creando categorías...\n")

cat_bebidas_c = Category.objects.get_or_create(
    name="Bebidas Calientes",
    defaults={"category_type": "BEBIDAS", "description": "Café, té y chocolate caliente"}
)[0]

cat_bebidas_f = Category.objects.get_or_create(
    name="Bebidas Frías",
    defaults={"category_type": "BEBIDAS", "description": "Jugos y bebidas refrescantes"}
)[0]

cat_entradas = Category.objects.get_or_create(
    name="Entradas",
    defaults={"category_type": "ENTRADAS", "description": "Panes, snacks y acompañamientos"}
)[0]

cat_comidas = Category.objects.get_or_create(
    name="Comidas",
    defaults={"category_type": "COMIDAS", "description": "Platos principales"}
)[0]

cat_postres = Category.objects.get_or_create(
    name="Postres",
    defaults={"category_type": "POSTRES", "description": "Dulces y postres caseros"}
)[0]

print("✓ Categorías creadas")


# ==========================================================
# 3. PRODUCTOS — MENÚ BASE
# ==========================================================
print("\n3) Creando productos...\n")

productos = [
    # Bebidas calientes
    ("Café Americano", cat_bebidas_c, "Café negro tradicional", 3.50, 3,
     {"leche": 0.5, "azucar": 0, "extra_shot": 1.0}, None),

    ("Cappuccino", cat_bebidas_c, "Café con leche espumosa", 4.50, 5,
     {"leche_vegetal": 0.5, "jarabe_vainilla": 0.3}, None),

    ("Chocolate Caliente", cat_bebidas_c, "Chocolate artesanal", 4.00, 4,
     {"crema": 0.5, "marshmallows": 0.3}, None),

    # Bebidas frías
    ("Jugo de Naranja Natural", cat_bebidas_f, "Jugo recién exprimido", 3.00, 2, {}, None),
    ("Batido de Fresa", cat_bebidas_f, "Cremoso y dulce", 5.00, 4,
     {"proteina": 1.0, "extra_fruta": 0.5}, None),

    # Entradas
    ("Croissant", cat_entradas, "Croissant clásico", 2.50, 2, {}, None),
    ("Pan con Mantequilla", cat_entradas, "Pan tostado artesanal", 1.50, 3, {}, None),

    # Comidas
    ("Sandwich de Pollo", cat_comidas, "Pollo a la plancha con vegetales", 8.00, 10,
     {"queso": 0.5, "aguacate": 1}, None),

    ("Ensalada César", cat_comidas, "Clásica con aderezo César", 7.50, 8,
     {"pollo": 2}, None),

    # Postres
    ("Cheesecake", cat_postres, "Tarta de queso", 5.50, 2, {}, None),
    ("Brownie con Helado", cat_postres, "Brownie caliente con bola de vainilla", 6.00, 5,
     {"extra_helado": 1.0}, None),
]

for name, cat, desc, price, prep, extras, season in productos:
    Product.objects.get_or_create(
        name=name,
        category=cat,
        defaults={
            "description": desc,
            "base_price": price,
            "preparation_time": prep,
            "available_extras": extras,
            "season": season
        }
    )

print("✓ Productos del menú base creados")


# ==========================================================
# 4. PRODUCTOS DE TEMPORADA (estrategia)
# ==========================================================
print("\n4) Creando productos de temporada...\n")

productos_temp = [
    ("Latte de Calabaza", cat_bebidas_c, "Bebida típica de otoño", 4.80, 5,
     {"crema": 0.3}, "OTONIO"),

    ("Chocolate Navideño", cat_bebidas_c, "Chocolate con especias", 4.50, 4,
     {"canela": 0.2}, "INVIERNO"),

    ("Helado de Vainilla Especial", cat_postres, "Helado artesanal", 4.00, 2,
     {"topping_chispas": 0.5}, "VERANO"),
]

for name, cat, desc, price, prep, extras, season in productos_temp:
    Product.objects.get_or_create(
        name=name,
        category=cat,
        defaults={
            "description": desc,
            "base_price": price,
            "preparation_time": prep,
            "available_extras": extras,
            "season": season
        }
    )

print("✓ Productos de temporada creados")


# ==========================================================
# 5. ESTACIONES DE COCINA
# ==========================================================
print("\n5) Creando estaciones de cocina...\n")

stations = [
    ("Estación Bebidas Calientes", "BEBIDAS_CALIENTES", ["BEBIDAS"]),
    ("Estación Bebidas Frías", "BEBIDAS_FRIAS", ["BEBIDAS"]),
    ("Panadería", "PANADERIA", ["ENTRADAS"]),
    ("Cocina Principal", "COCINA", ["COMIDAS"]),
    ("Repostería", "POSTRES", ["POSTRES"]),
]

for name, stype, handled in stations:
    KitchenStation.objects.get_or_create(
        name=name,
        defaults={"station_type": stype, "can_handle_categories": handled}
    )

print("✓ Estaciones creadas")

print("\n" + "=" * 60)
print("✓ Inicialización completada exitosamente")
print("=" * 60)
print("\nCredenciales de prueba:")
print("• Admin: admin / admin123")
print("• Meseros: maria_mesera | juan_mesero — clave: mesero123")
print("• Cocineros: carlos_chef | laura_chef — clave: chef123")
print("• Clientes: ana_cliente | pedro_cliente | sofia_cliente — clave: cliente123")
print("\nAdmin panel: http://localhost:8000/admin/")
