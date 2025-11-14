"""
Script para inicializar datos de prueba
Ejecutar: python manage.py shell < scripts/init_data.py
"""
from apps.users.models import User
from apps.menu.models import Category, Product
from apps.kitchen.models import KitchenStation

print("Inicializando datos de prueba...")

# 1. Crear usuarios
print("\n1. Creando usuarios...")

# Admin
admin, _ = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@cafedelbosque.com',
        'role': 'ADMIN',
        'is_staff': True,
        'is_superuser': True
    }
)
admin.set_password('admin123')
admin.save()
print("✓ Admin creado")

# Meseros
mesero1, _ = User.objects.get_or_create(
    username='maria_mesera',
    defaults={
        'email': 'maria@cafedelbosque.com',
        'role': 'MESERO',
        'first_name': 'María',
        'last_name': 'González'
    }
)
mesero1.set_password('mesero123')
mesero1.save()

mesero2, _ = User.objects.get_or_create(
    username='juan_mesero',
    defaults={
        'email': 'juan@cafedelbosque.com',
        'role': 'MESERO',
        'first_name': 'Juan',
        'last_name': 'Pérez'
    }
)
mesero2.set_password('mesero123')
mesero2.save()
print("✓ 2 Meseros creados")

# Cocineros
cocinero, _ = User.objects.get_or_create(
    username='carlos_chef',
    defaults={
        'email': 'carlos@cafedelbosque.com',
        'role': 'COCINERO',
        'first_name': 'Carlos',
        'last_name': 'Rodríguez'
    }
)
cocinero.set_password('chef123')
cocinero.save()
print("✓ Cocinero creado")

# Clientes
cliente1, _ = User.objects.get_or_create(
    username='ana_cliente',
    defaults={
        'email': 'ana@email.com',
        'role': 'CLIENTE',
        'first_name': 'Ana',
        'last_name': 'Martínez'
    }
)
cliente1.set_password('cliente123')
cliente1.save()

cliente2, _ = User.objects.get_or_create(
    username='pedro_cliente',
    defaults={
        'email': 'pedro@email.com',
        'role': 'CLIENTE',
        'first_name': 'Pedro',
        'last_name': 'López'
    }
)
cliente2.set_password('cliente123')
cliente2.save()
print("✓ 2 Clientes creados")

# 2. Crear categorías
print("\n2. Creando categorías...")

cat_bebidas, _ = Category.objects.get_or_create(
    name='Bebidas Calientes',
    defaults={'category_type': 'BEBIDAS', 'description': 'Café, té y chocolate'}
)

cat_bebidas_frias, _ = Category.objects.get_or_create(
    name='Bebidas Frías',
    defaults={'category_type': 'BEBIDAS', 'description': 'Jugos y batidos'}
)

cat_entradas, _ = Category.objects.get_or_create(
    name='Entradas',
    defaults={'category_type': 'ENTRADAS', 'description': 'Panes y acompañamientos'}
)

cat_comidas, _ = Category.objects.get_or_create(
    name='Comidas',
    defaults={'category_type': 'COMIDAS', 'description': 'Platos principales'}
)

cat_postres, _ = Category.objects.get_or_create(
    name='Postres',
    defaults={'category_type': 'POSTRES', 'description': 'Dulces y postres'}
)
print("✓ 5 Categorías creadas")

# 3. Crear productos
print("\n3. Creando productos...")

# Bebidas calientes
Product.objects.get_or_create(
    name='Café Americano',
    category=cat_bebidas,
    defaults={
        'description': 'Café negro tradicional',
        'base_price': 3.50,
        'preparation_time': 3,
        'available_extras': {'leche': 0.5, 'azucar': 0.0, 'extra_shot': 1.0}
    }
)

Product.objects.get_or_create(
    name='Cappuccino',
    category=cat_bebidas,
    defaults={
        'description': 'Café con leche espumosa',
        'base_price': 4.50,
        'preparation_time': 5,
        'available_extras': {'leche_vegetal': 0.5, 'jarabe_vainilla': 0.3}
    }
)

Product.objects.get_or_create(
    name='Chocolate Caliente',
    category=cat_bebidas,
    defaults={
        'description': 'Chocolate artesanal',
        'base_price': 4.00,
        'preparation_time': 4,
        'available_extras': {'crema': 0.5, 'marshmallows': 0.3}
    }
)

# Bebidas frías
Product.objects.get_or_create(
    name='Jugo de Naranja Natural',
    category=cat_bebidas_frias,
    defaults={
        'description': 'Jugo recién exprimido',
        'base_price': 3.00,
        'preparation_time': 2,
        'available_extras': {}
    }
)

Product.objects.get_or_create(
    name='Batido de Fresa',
    category=cat_bebidas_frias,
    defaults={
        'description': 'Batido cremoso de fresas',
        'base_price': 5.00,
        'preparation_time': 4,
        'available_extras': {'proteina': 1.0, 'extra_fruta': 0.5}
    }
)

# Entradas
Product.objects.get_or_create(
    name='Croissant',
    category=cat_entradas,
    defaults={
        'description': 'Croissant de mantequilla',
        'base_price': 2.50,
        'preparation_time': 2,
        'available_extras': {}
    }
)

Product.objects.get_or_create(
    name='Pan con Mantequilla',
    category=cat_entradas,
    defaults={
        'description': 'Pan artesanal tostado',
        'base_price': 1.50,
        'preparation_time': 3,
        'available_extras': {}
    }
)

# Comidas
Product.objects.get_or_create(
    name='Sandwich de Pollo',
    category=cat_comidas,
    defaults={
        'description': 'Sandwich con pollo a la plancha',
        'base_price': 8.00,
        'preparation_time': 10,
        'available_extras': {'queso': 0.5, 'aguacate': 1.0}
    }
)

Product.objects.get_or_create(
    name='Ensalada César',
    category=cat_comidas,
    defaults={
        'description': 'Ensalada fresca con aderezo César',
        'base_price': 7.50,
        'preparation_time': 8,
        'available_extras': {'pollo': 2.0}
    }
)

# Postres
Product.objects.get_or_create(
    name='Cheesecake',
    category=cat_postres,
    defaults={
        'description': 'Tarta de queso con frutos rojos',
        'base_price': 5.50,
        'preparation_time': 2,
        'available_extras': {}
    }
)

Product.objects.get_or_create(
    name='Brownie con Helado',
    category=cat_postres,
    defaults={
        'description': 'Brownie caliente con helado de vainilla',
        'base_price': 6.00,
        'preparation_time': 5,
        'available_extras': {'extra_helado': 1.0}
    }
)

print("✓ 11 Productos creados")

# 4. Crear estaciones de cocina
print("\n4. Creando estaciones de cocina...")

KitchenStation.objects.get_or_create(
    name='Estación Bebidas Calientes',
    defaults={
        'station_type': 'BEBIDAS_CALIENTES',
        'can_handle_categories': ['BEBIDAS']
    }
)

KitchenStation.objects.get_or_create(
    name='Estación Bebidas Frías',
    defaults={
        'station_type': 'BEBIDAS_FRIAS',
        'can_handle_categories': ['BEBIDAS']
    }
)

KitchenStation.objects.get_or_create(
    name='Panadería',
    defaults={
        'station_type': 'PANADERIA',
        'can_handle_categories': ['ENTRADAS']
    }
)

KitchenStation.objects.get_or_create(
    name='Cocina Principal',
    defaults={
        'station_type': 'COCINA',
        'can_handle_categories': ['COMIDAS']
    }
)

KitchenStation.objects.get_or_create(
    name='Repostería',
    defaults={
        'station_type': 'POSTRES',
        'can_handle_categories': ['POSTRES']
    }
)

print("✓ 5 Estaciones de cocina creadas")

print("\n" + "="*50)
print("✓ Datos inicializados correctamente!")
print("="*50)
print("\nCredenciales de acceso:")
print("- Admin: admin / admin123")
print("- Mesero: maria_mesera / mesero123")
print("- Chef: carlos_chef / chef123")
print("- Cliente: ana_cliente / cliente123")
print("\nAccede al admin en: http://localhost:8000/admin/")