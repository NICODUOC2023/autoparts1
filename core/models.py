from django.db import models
from django.utils import timezone
from decimal import Decimal

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Slug")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                             related_name='children', verbose_name="Categoría padre")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['name']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    brand = models.CharField(max_length=100, verbose_name="Marca")
    code = models.CharField(max_length=50, verbose_name="Código")
    product_code = models.CharField(max_length=50, verbose_name="Código del producto")
    description = models.TextField(verbose_name="Descripción", blank=True)
    stock = models.IntegerField(verbose_name="Stock", default=0)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, 
                               related_name='products', verbose_name="Categoría")
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name="Imagen")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.brand}"

    def get_latest_price(self):
        return self.prices.first()

class Price(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='prices')
    value = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Valor Neto")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def iva(self):
        return self.value * Decimal('0.19')

    @property
    def total(self):
        return self.value + self.iva

    def __str__(self):
        return f"{self.product.name} - ${self.total:,.0f}"

    def save(self, *args, **kwargs):
        if isinstance(self.value, float):
            self.value = Decimal(str(self.value))
        super().save(*args, **kwargs)

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]

    METODO_PAGO_CHOICES = [
        ('transferencia', 'Transferencia Bancaria'),
        ('webpay', 'WebPay'),
        ('efectivo', 'Efectivo'),
    ]

    # Datos del cliente
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    apellido = models.CharField(max_length=200, verbose_name="Apellido")
    correo = models.EmailField(verbose_name="Correo electrónico")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    rut = models.CharField(max_length=12, verbose_name="RUT")

    # Datos de envío
    direccion = models.TextField(verbose_name="Dirección")
    comuna = models.CharField(max_length=100, verbose_name="Comuna")
    ciudad = models.CharField(max_length=100, verbose_name="Ciudad")
    codigo_postal = models.CharField(max_length=20, verbose_name="Código Postal", blank=True, null=True)
    
    # Datos del pedido
    numero_pedido = models.CharField(max_length=20, unique=True, verbose_name="Número de Pedido")
    fecha_pedido = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del Pedido")
    productos = models.ManyToManyField(Product, through='DetallePedido', related_name='pedidos')
    
    # Valores
    subtotal = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Subtotal")
    iva = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="IVA")
    costo_envio = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Costo de Envío", default=0)
    valor_total = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Valor Total")
    
    # Estado y método de pago
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name="Estado")
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, verbose_name="Método de Pago")
    
    # Datos de seguimiento
    codigo_seguimiento = models.CharField(max_length=100, verbose_name="Código de Seguimiento", blank=True, null=True)
    notas = models.TextField(verbose_name="Notas", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_pedido']

    def __str__(self):
        return f"Pedido #{self.numero_pedido} - {self.nombre} {self.apellido}"

    def save(self, *args, **kwargs):
        if not self.numero_pedido:
            # Generar número de pedido único: PED + YYYYMMDD + 4 dígitos aleatorios
            import random
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            random_digits = ''.join([str(random.randint(0, 9)) for _ in range(4)])
            self.numero_pedido = f"PED{date_str}{random_digits}"
        
        # Calcular totales si no están establecidos
        if not self.iva:
            self.iva = int(self.subtotal * 0.19)
        if not self.valor_total:
            self.valor_total = self.subtotal + self.iva + self.costo_envio
            
        super().save(*args, **kwargs)

    def get_estado_display_class(self):
        """Retorna la clase de Bootstrap según el estado"""
        estado_classes = {
            'pendiente': 'warning',
            'pagado': 'info',
            'enviado': 'primary',
            'entregado': 'success',
            'cancelado': 'danger'
        }
        return estado_classes.get(self.estado, 'secondary')

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Product, on_delete=models.CASCADE)
    cantidad = models.IntegerField(verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Precio Unitario")
    subtotal = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Subtotal")
    iva = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="IVA")
    total = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Total")

    class Meta:
        verbose_name = "Detalle de Pedido"
        verbose_name_plural = "Detalles de Pedidos"

    def __str__(self):
        return f"{self.producto.name} x{self.cantidad} - Pedido #{self.pedido.numero_pedido}"

    def save(self, *args, **kwargs):
        if not self.subtotal:
            self.subtotal = self.cantidad * self.precio_unitario
        if not self.iva:
            self.iva = int(self.subtotal * 0.19)
        if not self.total:
            self.total = self.subtotal + self.iva
        super().save(*args, **kwargs)

