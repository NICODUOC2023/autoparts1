from rest_framework import serializers
from .models import Product, Price

class PriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Price
        fields = ['date', 'value']

class ProductSerializer(serializers.ModelSerializer):
    prices = PriceSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['product_code', 'brand', 'code', 'name', 'prices']