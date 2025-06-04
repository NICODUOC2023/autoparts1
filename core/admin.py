from django.contrib import admin
from .models import Product, Price, Category

class PriceInline(admin.TabularInline):
    model = Price
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'slug', 'created_at')
    search_fields = ('name', 'slug')
    list_filter = ('parent', 'created_at')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'category', 'product_code', 'code', 'get_latest_price')
    search_fields = ('name', 'brand', 'product_code', 'code')
    list_filter = ('brand', 'category', 'created_at')
    inlines = [PriceInline]

    def get_latest_price(self, obj):
        latest_price = obj.prices.first()
        if latest_price:
            return f"${latest_price.value:,}"
        return "Sin precio"
    get_latest_price.short_description = "Último Precio"

@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'get_formatted_neto', 'get_formatted_iva', 'get_formatted_total', 'created_at')
    list_filter = ('created_at', 'product__brand')
    search_fields = ('product__name', 'product__brand')

    def get_formatted_neto(self, obj):
        return f"${obj.value:,}"
    get_formatted_neto.short_description = "Valor Neto"

    def get_formatted_iva(self, obj):
        return f"${obj.iva:,}"
    get_formatted_iva.short_description = "IVA"

    def get_formatted_total(self, obj):
        return f"${obj.total:,}"
    get_formatted_total.short_description = "Total"
