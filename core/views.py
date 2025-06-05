import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from decimal import Decimal, InvalidOperation
import uuid
from .models import Product, Category, Compra, DetalleCompra, Price, Empresa, Cotizacion, DetalleCotizacion
from .forms import EmpresaForm

@require_POST
def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    product = get_object_or_404(Product, id=product_id)
    
    # Convertir el ID a string ya que JSON solo acepta strings como keys
    product_id = str(product_id)
    
    # Get quantity from form data, default to 1 if not provided
    quantity = int(request.POST.get('quantity', 1))
    
    # Verificar stock
    if product.stock > 0:
        if product_id in cart:
            cart[product_id] = cart[product_id] + quantity
        else:
            cart[product_id] = quantity
        
        request.session['cart'] = cart
        messages.success(request, 'Producto agregado al carrito.')
        return JsonResponse({'status': 'success', 'cart_total': sum(cart.values())})
    else:
        messages.error(request, 'Producto sin stock disponible.')
        return JsonResponse({'status': 'error', 'message': 'Sin stock'})
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'})

@require_POST
def update_cart(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        product_id = str(product_id)
        
        # Try to get quantity from JSON data first, then form data
        try:
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))
        except (json.JSONDecodeError, ValueError):
            quantity = int(request.POST.get('quantity', 1))
        
        # Verificar stock
        product = get_object_or_404(Product, id=product_id)
        if quantity > product.stock:
            return JsonResponse({
                'status': 'error',
                'message': f'Solo hay {product.stock} unidades disponibles'
            })
        
        if quantity > 0:
            cart[product_id] = quantity
        else:
            cart.pop(product_id, None)
        
        request.session['cart'] = cart
        cart_total = sum(cart.values())
        return JsonResponse({
            'status': 'success',
            'cart_total': cart_total,
            'message': 'Carrito actualizado correctamente'
        })
        
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}) 