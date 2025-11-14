"""
Tests para todos los patrones de diseño implementados
"""
from django.test import TestCase
from apps.users.models import User
from apps.menu.models import Category, Product
from apps.orders.models import Order, OrderItem
from apps.kitchen.models import KitchenStation
from apps.orders.services import OrderService
from apps.orders.patterns.builder import OrderBuilder
from apps.orders.patterns.factory import get_order_factory
from apps.orders.patterns.state import OrderStateManager
from apps.orders.patterns.command import CreateOrderCommand, CommandInvoker
from apps.orders.patterns.memento import get_caretaker, OrderOriginator
from apps.kitchen.handlers import KitchenRouter
from apps.core.config import get_config
from apps.core.cache_proxy import MenuProxy
from apps.core.facade import CafeteriaFacade
from apps.notifications.services import NotificationService
from apps.notifications.strategies import NotificationManager
from apps.menu.services import get_menu_factory


class FactoryPatternTest(TestCase):
    """Tests para Factory Method"""

    def setUp(self):
        self.customer = User.objects.create(username='test_customer', role='CLIENTE')
        self.category = Category.objects.create(name='Bebidas', category_type='BEBIDAS')
        self.product = Product.objects.create(
            name='Café',
            category=self.category,
            base_price=3.50,
            preparation_time=5
        )

    def test_dine_in_factory(self):
        """Test Factory para orden en mesa"""
        factory = get_order_factory('dine_in')
        order = factory.create_order(
            customer=self.customer,
            table_number=5
        )

        self.assertEqual(order.table_number, 5)
        self.assertEqual(order.customer, self.customer)

    def test_takeaway_factory(self):
        """Test Factory para orden para llevar"""
        factory = get_order_factory('take_away')
        order = factory.create_order(customer=self.customer)

        self.assertEqual(order.table_number, 0)
        self.assertIn('PARA LLEVAR', order.special_instructions)


class BuilderPatternTest(TestCase):
    """Tests para Builder Pattern"""

    def setUp(self):
        self.customer = User.objects.create(username='builder_test', role='CLIENTE')
        self.mesero = User.objects.create(username='mesero_test', role='MESERO')
        self.category = Category.objects.create(name='Bebidas', category_type='BEBIDAS')
        self.product = Product.objects.create(
            name='Café',
            category=self.category,
            base_price=3.50,
            preparation_time=5,
            available_extras={'leche': 0.5}
        )

    def test_builder_creates_order(self):
        """Test construcción de orden con Builder"""
        builder = OrderBuilder()
        order = (builder
                 .set_customer(self.customer)
                 .set_table(5)
                 .set_mesero(self.mesero)
                 .add_product(self.product.id, quantity=2, extras={'leche': True})
                 .add_special_instructions("Sin azúcar")
                 .build())

        self.assertEqual(order.table_number, 5)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.special_instructions, "Sin azúcar")


class SingletonPatternTest(TestCase):
    """Tests para Singleton Pattern"""

    def test_config_singleton(self):
        """Test que Config es singleton"""
        config1 = get_config()
        config2 = get_config()

        self.assertIs(config1, config2)

        config1.set('max_tables', 30)
        self.assertEqual(config2.get('max_tables'), 30)


class StatePatternTest(TestCase):
    """Tests para State Pattern"""

    def setUp(self):
        self.customer = User.objects.create(username='state_test', role='CLIENTE')
        self.category = Category.objects.create(name='Bebidas', category_type='BEBIDAS')
        self.product = Product.objects.create(
            name='Café',
            category=self.category,
            base_price=3.50,
            preparation_time=5
        )
        self.order = Order.objects.create(
            customer=self.customer,
            table_number=5
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1
        )

    def test_state_transitions(self):
        """Test transiciones de estados"""
        self.assertEqual(self.order.status, 'PENDIENTE')

        # PENDIENTE -> EN_PREPARACION
        OrderStateManager.advance_order(self.order)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'EN_PREPARACION')

        # EN_PREPARACION -> LISTO
        OrderStateManager.advance_order(self.order)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'LISTO')

        # LISTO -> ENTREGADO
        OrderStateManager.advance_order(self.order)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'ENTREGADO')


class CommandPatternTest(TestCase):
    """Tests para Command Pattern"""

    def setUp(self):
        self.customer = User.objects.create(username='command_test', role='CLIENTE')
        self.category = Category.objects.create(name='Bebidas', category_type='BEBIDAS')
        self.product = Product.objects.create(
            name='Café',
            category=self.category,
            base_price=3.50,
            preparation_time=5
        )

    def test_create_order_command(self):
        """Test comando de crear orden"""
        command = CreateOrderCommand(
            customer=self.customer,
            table_number=5,
            items=[{'product_id': self.product.id, 'quantity': 1, 'extras': {}}]
        )

        invoker = CommandInvoker()
        order = invoker.execute_command(command)

        self.assertIsNotNone(order)
        self.assertEqual(order.items.count(), 1)

    def test_command_undo(self):
        """Test deshacer comando"""
        command = CreateOrderCommand(
            customer=self.customer,
            table_number=5,
            items=[{'product_id': self.product.id, 'quantity': 1, 'extras': {}}]
        )

        invoker = CommandInvoker()
        order = invoker.execute_command(command)
        order_id = order.id

        # Deshacer
        invoker.undo()

        self.assertFalse(Order.objects.filter(id=order_id).exists())


class MementoPatternTest(TestCase):
    """Tests para Memento Pattern"""

    def setUp(self):
        self.customer = User.objects.create(username='memento_test', role='CLIENTE')
        self.category = Category.objects.create(name='Bebidas', category_type='BEBIDAS')
        self.product = Product.objects.create(
            name='Café',
            category=self.category,
            base_price=3.50,
            preparation_time=5
        )
        self.order = Order.objects.create(
            customer=self.customer,
            table_number=5,
            status='PENDIENTE'
        )

    def test_save_and_restore_memento(self):
        """Test guardar y restaurar estado"""
        caretaker = get_caretaker()

        # Guardar estado inicial
        caretaker.save(self.order, tag="initial")

        # Cambiar estado
        self.order.status = 'EN_PREPARACION'
        self.order.save()

        # Restaurar
        caretaker.restore(self.order, tag="initial")
        self.order.refresh_from_db()

        self.assertEqual(self.order.status, 'PENDIENTE')


class ChainOfResponsibilityTest(TestCase):
    """Tests para Chain of Responsibility"""

    def setUp(self):
        self.customer = User.objects.create(username='chain_test', role='CLIENTE')

        # Crear categorías
        self.cat_bebidas = Category.objects.create(name='Bebidas', category_type='BEBIDAS')
        self.cat_comidas = Category.objects.create(name='Comidas', category_type='COMIDAS')

        # Crear productos
        self.cafe = Product.objects.create(
            name='Café Caliente',
            category=self.cat_bebidas,
            base_price=3.50,
            preparation_time=5
        )
        self.sandwich = Product.objects.create(
            name='Sandwich',
            category=self.cat_comidas,
            base_price=8.00,
            preparation_time=10
        )

        # Crear estaciones
        KitchenStation.objects.create(
            name='Bebidas Calientes',
            station_type='BEBIDAS_CALIENTES',
            can_handle_categories=['BEBIDAS']
        )
        KitchenStation.objects.create(
            name='Cocina Principal',
            station_type='COCINA',
            can_handle_categories=['COMIDAS']
        )

        # Crear orden
        self.order = Order.objects.create(customer=self.customer, table_number=5)
        OrderItem.objects.create(order=self.order, product=self.cafe, quantity=1)
        OrderItem.objects.create(order=self.order, product=self.sandwich, quantity=1)

    def test_route_to_stations(self):
        """Test enrutamiento a estaciones"""
        router = KitchenRouter()
        assignments = router.route_order(self.order)

        self.assertGreater(len(assignments), 0)


class ObserverPatternTest(TestCase):
    """Tests para Observer Pattern"""

    def setUp(self):
        self.mesero = User.objects.create(username='observer_mesero', role='MESERO')
        self.customer = User.objects.create(username='observer_customer', role='CLIENTE')
        self.category = Category.objects.create(name='Bebidas', category_type='BEBIDAS')
        self.product = Product.objects.create(
            name='Café',
            category=self.category,
            base_price=3.50,
            preparation_time=5
        )
        self.order = Order.objects.create(customer=self.customer, table_number=5)

    def test_register_waiter_observer(self):
        """Test registro de mesero como observer"""
        NotificationService.register_waiter(self.mesero)

        # Notificar
        NotificationService.notify_kitchen(self.order)

        notifications = NotificationService.get_kitchen_notifications()
        self.assertGreater(len(notifications), 0)


class ProxyPatternTest(TestCase):
    """Tests para Proxy Pattern"""

    def setUp(self):
        self.category = Category.objects.create(name='Bebidas', category_type='BEBIDAS')
        self.product = Product.objects.create(
            name='Café',
            category=self.category,
            base_price=3.50,
            preparation_time=5
        )

    def test_menu_proxy_cache(self):
        """Test cache del menú"""
        proxy = MenuProxy()

        # Primera llamada (carga desde BD)
        menu1 = proxy.get_menu()

        # Segunda llamada (usa cache)
        menu2 = proxy.get_menu()

        self.assertEqual(len(menu1), len(menu2))

        # Verificar info de cache
        cache_info = proxy.get_cache_info()
        self.assertTrue(cache_info['cached'])


class FacadePatternTest(TestCase):
    """Tests para Facade Pattern"""

    def setUp(self):
        self.customer = User.objects.create(username='facade_customer', role='CLIENTE')
        self.mesero = User.objects.create(username='facade_mesero', role='MESERO')
        self.category = Category.objects.create(name='Bebidas', category_type='BEBIDAS')
        self.product = Product.objects.create(
            name='Café',
            category=self.category,
            base_price=3.50,
            preparation_time=5
        )

        KitchenStation.objects.create(
            name='Bebidas Calientes',
            station_type='BEBIDAS_CALIENTES',
            can_handle_categories=['BEBIDAS']
        )

    def test_facade_complete_order(self):
        """Test orden completa usando Facade"""
        facade = CafeteriaFacade()

        result = facade.realizar_pedido_completo(
            customer_id=self.customer.id,
            table_number=5,
            items=[{'product_id': self.product.id, 'quantity': 1, 'extras': {}}],
            mesero_id=self.mesero.id
        )

        self.assertTrue(result['success'])
        self.assertIn('order', result)


class StrategyPatternTest(TestCase):
    """Tests para Strategy Pattern"""

    def test_notification_strategies(self):
        """Test estrategias de notificación"""
        result = NotificationManager.send_notification(
            'console',
            'test@example.com',
            'Mensaje de prueba'
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['type'], 'console')


class CompositePatternTest(TestCase):
    """Tests para Composite Pattern"""

    def setUp(self):
        self.parent_category = Category.objects.create(
            name='Bebidas',
            category_type='BEBIDAS'
        )
        self.child_category = Category.objects.create(
            name='Bebidas Calientes',
            category_type='BEBIDAS',
            parent=self.parent_category
        )
        self.product = Product.objects.create(
            name='Café',
            category=self.child_category,
            base_price=3.50,
            preparation_time=5
        )

    def test_get_all_products_recursive(self):
        """Test obtener productos recursivamente"""
        products = self.parent_category.get_all_products()
        self.assertIn(self.product, products)