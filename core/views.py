from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from rest_framework import viewsets
from .models import Product, Category
from .serializers import ProductSerializer
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
import json
from decimal import Decimal, InvalidOperation
from django.db.models import Q

import uuid
from django.shortcuts import redirect
from .transbank_client import webpay
from django.shortcuts import render
from .pdf_utils import generate_payment_receipt

# Create your views here.

def home(request):
    return render(request, 'core/home.html', {
        'title': 'Welcome to Django Web App'
    })

def product_list(request):
    products = Product.objects.all().prefetch_related('prices')
    return render(request, 'core/products.html', {
        'products': products,
        'title': 'Todos los Productos'
    })

def category_products(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    # Get all descendant categories (including the current one)
    categories = Category.objects.filter(id=category.id) | Category.objects.filter(parent=category)
    products = Product.objects.filter(category__in=categories).prefetch_related('prices')
    
    return render(request, 'core/category_products.html', {
        'category': category,
        'products': products,
        'title': category.name
    })

@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    
    # Convert the product_id to string since session serializes it that way
    product_id = str(product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    # Get current quantity or 0 if product not in cart
    current_quantity = cart.get(product_id, 0)
    # Update quantity
    cart[product_id] = current_quantity + quantity
    
    # Save cart back to session
    request.session['cart'] = cart
    
    # Calculate total items in cart
    cart_total = sum(cart.values())
    
    return JsonResponse({
        'status': 'success',
        'cart_total': cart_total
    })

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

def login_page(request):
    return render(request, 'core/login.html', {
        'title': 'Pantalla de Inicio de Sesión'
    })

def b2b_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username == 'manolo' and password == 'duoc1234':
            request.session['b2b_user'] = username
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('b2b_dashboard')
                })
            return redirect('b2b_dashboard')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Usuario o contraseña incorrectos'
                })
            return render(request, 'core/login.html', {'error': 'Usuario o contraseña incorrectos'})
    
    return render(request, 'core/login.html')

def b2b_dashboard(request):
    if 'b2b_user' not in request.session:
        return redirect('b2b_login')
    
    return render(request, 'core/b2b.html', {
        'is_b2b_view': True
    })

def b2b_logout(request):
    if 'b2b_user' in request.session:
        del request.session['b2b_user']
    return redirect('b2b_login')

def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    cart_total = 0
    total_items = 0
    
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            # Obtener el precio más reciente del producto
            price = product.prices.first()
            if price:
                total_price = price.value * quantity
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'total_price': total_price
                })
                cart_total += total_price
                total_items += quantity
        except Product.DoesNotExist:
            continue
    
    return render(request, 'core/cart.html', {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'total_items': total_items
    })

@require_POST
def update_cart(request, product_id):
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        if quantity < 1:
            return JsonResponse({'success': False, 'error': 'La cantidad debe ser mayor a 0'})
        
        cart = request.session.get('cart', {})
        cart[str(product_id)] = quantity
        request.session['cart'] = cart
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
    return JsonResponse({'success': True})

@require_POST
def process_payment(request):
    # Aquí iría la lógica de procesamiento de pago
    # Por ahora solo limpiaremos el carrito
    request.session['cart'] = {}
    messages.success(request, '¡Gracias por tu compra!')
    return redirect('home')

@require_POST
def start_payment(request):
    raw_amount = request.POST.get('amount')
    try:
        # Quitamos posible formato: comas, símbolos de moneda…
        normalized = raw_amount.replace(',', '').replace('$', '')
        amount = Decimal(normalized)
    except (TypeError, InvalidOperation):
        return render(request, 'payment/error.html', {
            'message': 'Monto inválido para iniciar el pago.'
        })

    buy_order  = uuid.uuid4().hex[:26]
    session_id = uuid.uuid4().hex[:61]
    return_url = request.build_absolute_uri('/payment/return/')

    resp = webpay.create(buy_order, session_id, float(amount), return_url)
    return render(request, 'payment/init_transaction.html', {
        'action_url': resp['url'],
        'token':      resp['token']
    })

def download_receipt(request, buy_order):
    # Get the payment data from the session
    payment_data = request.session.get('last_payment', {})
    
    if not payment_data or payment_data.get('buy_order') != buy_order:
        messages.error(request, 'No se encontró la información del pago')
        return redirect('home')
    
    # Generate PDF
    buffer = generate_payment_receipt(payment_data)
    
    # Create the HttpResponse object with the PDF
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="comprobante_pago_{buy_order}.pdf"'
    
    return response

def payment_return(request):
    token = request.GET.get('token_ws')
    if not token:
        messages.error(request, 'No se recibió el token de la transacción')
        return redirect('cart')
    
    try:
        result = webpay.commit(token)
        
        # Store payment data in session for PDF generation
        payment_data = {
            'status': result['status'],
            'amount': result['amount'],
            'buy_order': result['buy_order'],
            'card_last4': result['card_detail']['card_number'],
            'card_type': result['card_detail'].get('card_type', 'No especificado'),
            'transaction_date': result.get('transaction_date', 'No especificada'),
            'authorization_code': result.get('authorization_code', 'No especificado'),
        }
        request.session['last_payment'] = payment_data
        
        # Si el pago fue exitoso, limpiar el carrito
        if result['status'] == 'AUTHORIZED':
            request.session['cart'] = {}
            messages.success(request, '¡Pago realizado con éxito!')
        
        # Renderiza la plantilla con los datos
        return render(request, 'payment/result.html', payment_data)
    except Exception as e:
        messages.error(request, f'Error al procesar el pago: {str(e)}')
        return redirect('cart')

def search_products(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return redirect('product_list')
    
    # Search in product name and brand
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(brand__icontains=query) |
        Q(code__icontains=query) |
        Q(product_code__icontains=query)
    ).prefetch_related('prices')
    
    return render(request, 'core/search_results.html', {
        'products': products,
        'query': query,
        'title': f'Resultados de búsqueda: {query}'
    })