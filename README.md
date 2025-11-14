# Café del Bosque - Sistema de Gestión de Órdenes

## 🚀 Pasos para Ejecutar el Proyecto

### 1. Preparar Base de Datos PostgreSQL

```sql
-- En pgAdmin o terminal psql:
CREATE DATABASE cafeteria_db;
```

### 2. Configurar Variables de Entorno

Crea archivo `.env` en la raíz del proyecto:

```env
DB_NAME=cafeteria_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=django-insecure-dev-key
DEBUG=True
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Crear Tablas en la Base de Datos

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Cargar Datos de Prueba

```bash
#Simular:
python manage.py init_data --dry-run --seed-users

#Ejecutar real y crear usuarios/estaciones/productos de ejemplo:
python manage.py init_data --seed-users

#Forzar (en caso de que quieras actualizar defaults):
python manage.py init_data --force --seed-users
```

### 6. Ejecutar Servidor

```bash
python manage.py runserver
```

El servidor estará disponible en: **http://localhost:8000**

---

## 📋 Endpoints Principales

### **FACADE - Operaciones Completas**

#### Realizar Pedido Completo
```http
POST /api/core/pedido/realizar/
Content-Type: application/json

{
    "customer_id": 4,
    "table_number": 5,
    "mesero_id": 1,
    "items": [
        {"product_id": 1, "quantity": 2, "extras": {"leche": true}},
        {"product_id": 6, "quantity": 1}
    ]
}
```

#### Ver Estado del Sistema
```http
GET /api/core/estado/
```

#### Completar Orden (Cocina → Listo)
```http
POST /api/core/pedido/1/completar/
```

#### Entregar Orden (Mesero → Entregado)
```http
POST /api/core/pedido/1/entregar/
```

---

### **MENÚ (Proxy Cache)**

#### Obtener Menú (Cacheado)
```http
GET /api/core/menu/cached/
```

#### Refrescar Cache
```http
GET /api/core/menu/cached/?refresh=true
```

#### Buscar Productos
```http
GET /api/core/menu/buscar/?q=cafe
```

---

### **ÓRDENES (Factory, Builder, State, Command, Memento)**

#### Crear Orden
```http
POST /api/orders/create/
{
    "customer_id": 4,
    "table_number": 3,
    "items": [{"product_id": 1, "quantity": 1}]
}
```

#### Avanzar Estado de Orden
```http
POST /api/orders/1/advance/
```

#### Cancelar Orden
```http
POST /api/orders/1/cancel/
{
    "reason": "Cliente cambió de opinión",
    "user_id": 1
}
```

#### Ver Historial (Memento)
```http
GET /api/orders/1/history/
```

---

### **COCINA (Chain of Responsibility)**

#### Enrutar Orden a Estaciones
```http
POST /api/kitchen/route/1/
```

#### Ver Estado de Estaciones
```http
GET /api/kitchen/status/
```

---

## 🎯 Flujo Completo de Ejemplo

### **1. Crear un pedido completo usando Facade:**

```bash
curl -X POST http://localhost:8000/api/core/pedido/realizar/ \
-H "Content-Type: application/json" \
-d '{
  "customer_id": 4,
  "table_number": 5,
  "mesero_id": 1,
  "items": [
    {"product_id": 1, "quantity": 2, "extras": {"leche": true}},
    {"product_id": 8, "quantity": 1}
  ]
}'
```

**Esto automáticamente:**
- ✅ Crea la orden (Factory/Builder)
- ✅ La pone en estado EN_PREPARACION (State)
- ✅ Notifica a cocina (Observer)
- ✅ Enruta a estaciones (Chain of Responsibility)
- ✅ Guarda snapshot (Memento)

### **2. Ver estado del sistema:**

```bash
curl http://localhost:8000/api/core/estado/
```

### **3. Completar orden (simular cocina):**

```bash
curl -X POST http://localhost:8000/api/core/pedido/1/completar/
```

**Esto automáticamente:**
- ✅ Cambia estado a LISTO (State)
- ✅ Notifica al mesero (Observer)

### **4. Entregar orden (mesero):**

```bash
curl -X POST http://localhost:8000/api/core/pedido/1/entregar/
```

---

## 🧪 Probar Patrones Específicos

### **PROXY (Cache de Menú)**
```bash
# Primera llamada: carga desde BD
curl http://localhost:8000/api/core/menu/cached/

# Segunda llamada: usa cache (más rápido)
curl http://localhost:8000/api/core/menu/cached/

# Forzar refresh
curl http://localhost:8000/api/core/menu/cached/?refresh=true
```

### **SINGLETON (Configuración)**
```bash
# Ver configuración
curl http://localhost:8000/api/core/config/

# Actualizar
curl -X PATCH http://localhost:8000/api/core/config/ \
-H "Content-Type: application/json" \
-d '{"max_tables": 30}'
```

### **OBSERVER (Notificaciones)**
Las notificaciones se imprimen en consola cuando:
- Nueva orden → notifica cocina
- Orden lista → notifica mesero

### **CHAIN OF RESPONSIBILITY (Enrutamiento)**
```bash
curl -X POST http://localhost:8000/api/kitchen/route/1/
```

---

## 🔍 Verificar en Admin

Accede a: **http://localhost:8000/admin/**

**Credenciales:**
- Usuario: `admin`
- Password: `admin123`

Podrás ver:
- Órdenes creadas
- Historial de cambios (Memento)
- Cola de estaciones
- Usuarios y productos

---

## 📊 Patrones Implementados

| Patrón | Ubicación | Propósito |
|--------|-----------|-----------|
| **Factory Method** | `orders/patterns/factory.py` | Crear diferentes tipos de órdenes |
| **Abstract Factory** | `menu/services.py` | Menús por temporada |
| **Builder** | `orders/patterns/builder.py` | Construir órdenes paso a paso |
| **Singleton** | `core/config.py` | Configuración única |
| **Decorator** | `menu/models.py` | Extras en productos |
| **Facade** | `core/facade.py` | Interfaz simplificada |
| **Composite** | `menu/models.py` | Categorías y productos |
| **Proxy** | `core/cache_proxy.py` | Cache del menú |
| **Command** | `orders/patterns/command.py` | Operaciones con historial |
| **State** | `orders/patterns/state.py` | Estados de órdenes |
| **Observer** | `notifications/services.py` | Notificaciones automáticas |
| **Chain of Resp.** | `kitchen/handlers.py` | Enrutamiento a estaciones |
| **Strategy** | `notifications/strategies.py`, `menu/services.py` | Precios y notificaciones |
| **Memento** | `orders/patterns/memento.py` | Guardar/restaurar estados |

---

## 🐛 Troubleshooting

### Error de conexión a PostgreSQL
```bash
# Verifica que PostgreSQL esté corriendo
# Windows: Services → PostgreSQL
# Mac/Linux: sudo service postgresql status
```

### Tablas no existen
```bash
python manage.py makemigrations
python manage.py migrate
```

### Puerto 8000 ocupado
```bash
python manage.py runserver 8080
```