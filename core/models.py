from django.db import models

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre")
    slug = models.SlugField(unique=True, verbose_name="Slug")
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
    product_code = models.CharField(max_length=20, verbose_name="Código del producto")
    brand = models.CharField(max_length=100, verbose_name="Marca")
    code = models.CharField(max_length=20, verbose_name="Código")
    name = models.CharField(max_length=200, verbose_name="Nombre")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, 
                               related_name='products', verbose_name="Categoría")
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name="Imagen")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.brand} - {self.name}"

class Price(models.Model):
    product = models.ForeignKey(Product, related_name='prices', on_delete=models.CASCADE)
    date = models.DateTimeField(verbose_name="Fecha")
    value = models.IntegerField(verbose_name="Valor")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Precio"
        verbose_name_plural = "Precios"
        ordering = ['-date']

    def __str__(self):
        return f"{self.product.name} - ${self.value} ({self.date.strftime('%d/%m/%Y')})"

