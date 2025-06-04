from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from rest_framework import viewsets
from .models import Product, Category, Pedido, DetallePedido
from .serializers import ProductSerializer
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET
from django.contrib import messages
from django.urls import reverse
import json
from decimal import Decimal, InvalidOperation
from django.db.models import Q
import requests



from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from .chilexpress_client import ChilexpressClient

import uuid
from django.shortcuts import redirect
from .transbank_client import webpay
from django.shortcuts import render
from .pdf_utils import generate_payment_receipt
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .regions import get_regions, get_comunas
from .chilexpress_client import ChilexpressClient

# Create your views here.

def home(request):
    # Get 4 newest products (Cyber 2025)
    cyber_products = Product.objects.all().prefetch_related('prices').order_by('-created_at')[:4]
    
    # Get 4 oldest products (Recién Llegados)
    new_products = Product.objects.all().prefetch_related('prices').order_by('created_at')[:4]
    
    return render(request, 'core/home.html', {
        'title': 'Autopartes - Tu tienda de repuestos',
        'cyber_products': cyber_products,
        'new_products': new_products
    })

def product_list(request):
    products = Product.objects.all().prefetch_related('prices')
    return render(request, 'core/products.html', {
        'products': products,
        'title': 'Todos los Productos'
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product.objects.prefetch_related('prices'), id=product_id)
    latest_price = product.get_latest_price()
    
    # Get related products from the same category
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    
    return render(request, 'core/product_detail.html', {
        'product': product,
        'latest_price': latest_price,
        'related_products': related_products,
        'title': product.name
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
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        product = get_object_or_404(Product, id=product_id)
        
        # Convertir el ID a string ya que JSON solo acepta strings como keys
        product_id = str(product_id)
        
        # Verificar stock
        if product.stock > 0:
            if product_id in cart:
                cart[product_id] += 1
            else:
                cart[product_id] = 1
            
            request.session['cart'] = cart
            messages.success(request, 'Producto agregado al carrito.')
            return JsonResponse({'status': 'success'})
        else:
            messages.error(request, 'Producto sin stock disponible.')
            return JsonResponse({'status': 'error', 'message': 'Sin stock'})
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'})

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

@require_POST
def update_cart(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        product_id = str(product_id)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            cart[product_id] = quantity
        else:
            cart.pop(product_id, None)
        
        request.session['cart'] = cart
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'})

@require_POST
def remove_from_cart(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        product_id = str(product_id)
        
        if product_id in cart:
            del cart[product_id]
            request.session['cart'] = cart
            return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Producto no encontrado'})

@require_POST
def process_payment(request):
    # Get form data
    nombre = request.POST.get('nombre')
    apellido = request.POST.get('apellido')
    correo = request.POST.get('correo')
    direccion = request.POST.get('direccion')
    comuna = request.POST.get('comuna')
    shipping_cost = Decimal(request.POST.get('shipping_cost', '0'))
    
    # Get cart data
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'El carrito está vacío')
        return redirect('cart')
    
    # Calculate total
    cart_total = Decimal('0')
    cart_items = []
    
    try:
        for product_id, quantity in cart.items():
            product = Product.objects.get(id=product_id)
            latest_price = product.get_latest_price()
            if not latest_price:
                messages.error(request, f'Error: Precio no disponible para {product.name}')
                return redirect('cart')
            
            item_total = latest_price.total * Decimal(str(quantity))
            cart_total += item_total
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'price': latest_price,
                'total': item_total
            })
        
        # Add shipping cost
        cart_total += shipping_cost
        
        # Create Pedido
        buy_order = str(uuid.uuid4())[:20]  # Transbank requires max 26 chars
        session_id = str(uuid.uuid4())
        return_url = request.build_absolute_uri(reverse('payment_return'))
        
        # Create order in database
        pedido = Pedido.objects.create(
            numero_pedido=buy_order,
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            direccion=direccion,
            comuna=comuna,
            subtotal=cart_total - shipping_cost,
            iva=Decimal('0.19') * (cart_total - shipping_cost),
            costo_envio=shipping_cost,
            valor_total=cart_total,
            estado='pendiente',
            metodo_pago='webpay'
        )
        
        # Create order details
        for item in cart_items:
            DetallePedido.objects.create(
                pedido=pedido,
                producto=item['product'],
                cantidad=item['quantity'],
                precio_unitario=item['price'].value,
                subtotal=item['price'].value * item['quantity'],
                iva=item['price'].iva * item['quantity'],
                total=item['price'].total * item['quantity']
            )
        
        # Initialize Transbank payment
        response = webpay.create(
            buy_order=buy_order,
            session_id=session_id,
            amount=int(cart_total),  # Transbank requires integer
            return_url=return_url
        )
        
        # Store order info in session for later
        request.session['payment_info'] = {
            'buy_order': buy_order,
            'cart_items': [{
                'product_id': item['product'].id,
                'quantity': item['quantity'],
                'price': float(item['price'].total),
                'total': float(item['total'])
            } for item in cart_items],
            'shipping_cost': float(shipping_cost),
            'total': float(cart_total)
        }
        
        # Clear cart
        request.session['cart'] = {}
        
        # Redirect to Transbank
        return redirect(response.url + '?token_ws=' + response.token)
        
    except Product.DoesNotExist:
        messages.error(request, 'Uno o más productos no existen')
        return redirect('cart')
    except InvalidOperation as e:
        messages.error(request, f'Error en el cálculo: {str(e)}')
        return redirect('cart')
    except Exception as e:
        messages.error(request, f'Error al procesar el pago: {str(e)}')
        return redirect('cart')

@require_GET
def start_payment(request):
    # Get pending order from session
    pending_order = request.session.get('pending_order')
    if not pending_order:
        messages.error(request, 'No hay un pedido pendiente de pago')
        return redirect('cart')
    
    try:
        amount = Decimal(pending_order['amount'])  # Convertir de string a Decimal
        order_id = pending_order['order_id']
        
        # Generate unique identifiers
        buy_order = f"OC{order_id:06d}"  # Format: OC000123
        session_id = str(uuid.uuid4())
        return_url = request.build_absolute_uri('/payment/return/')

        # Create Webpay transaction
        resp = webpay.create(buy_order, session_id, float(amount), return_url)  # Webpay requiere float
        
        # Store transaction data in session
        request.session['transaction_data'] = {
            'order_id': order_id,
            'buy_order': buy_order,
            'amount': str(amount)  # Guardar como string en la sesión
        }
        
        return render(request, 'payment/init_transaction.html', {
            'action_url': resp['url'],
            'token': resp['token']
        })
        
    except Exception as e:
        messages.error(request, f'Error al iniciar el pago: {str(e)}')
        return redirect('cart')

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

def format_clp(value):
    """Formatea un número como moneda CLP"""
    try:
        value = str(int(float(value)))
        if len(value) <= 3:
            return value
        else:
            s = value[-3:]
            value = value[:-3]
            while value:
                s = value[-3:] + '.' + s if value[-3:] else value + '.' + s
                value = value[:-3]
            return s
    except (ValueError, TypeError):
        return value

def products(request):
    products = Product.objects.all().prefetch_related('prices')
    categories = Category.objects.all()
    
    # Filtrar por categoría si se especifica
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    context = {
        'products': products,
        'categories': categories
    }
    return render(request, 'core/products.html', context)

def cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    cart_subtotal = Decimal('0')
    shipping_cost = Decimal('0')
    
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        price = product.get_latest_price()
        if price:
            quantity = Decimal(str(quantity))  # Convertir quantity a Decimal
            subtotal = price.value * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'unit_price': price.value,
                'subtotal': subtotal
            })
            cart_subtotal += subtotal
    
    # Calcular IVA y total
    cart_iva = cart_subtotal * Decimal('0.19')
    
    # Calcular costo de envío si hay items
    if cart_items:
        shipping_cost = Decimal('11487')  # Costo fijo de envío
    
    cart_total = cart_subtotal + cart_iva + shipping_cost
    
    context = {
        'cart_items': cart_items,
        'cart_subtotal': cart_subtotal,
        'cart_iva': cart_iva,
        'shipping_cost': shipping_cost,
        'cart_total': cart_total
    }
    
    return render(request, 'core/cart.html', context)

def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Tu carrito está vacío')
        return redirect('cart')
    
    cart_items = []
    cart_subtotal = Decimal('0')
    
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, id=product_id)
        price = product.get_latest_price()
        if price:
            subtotal = price.value * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'unit_price': price.value,
                'subtotal': subtotal
            })
            cart_subtotal += subtotal
    
    cart_iva = cart_subtotal * Decimal('0.19')
    shipping_cost = Decimal('11487') if cart_items else Decimal('0')
    cart_total = cart_subtotal + cart_iva + shipping_cost
    
    context = {
        'cart_items': cart_items,
        'cart_subtotal': cart_subtotal,
        'cart_iva': cart_iva,
        'shipping_cost': shipping_cost,
        'cart_total': cart_total
    }
    
    return render(request, 'core/checkout.html', context)

@require_GET
def get_comunas_view(request, region_code):
    """
    Vista que atiende GET /api/comunas/<region_code>/
    Devuelve en JSON la lista de comunas definidas en regions.py para esa región.
    """
    try:
        comunas = get_comunas(region_code)
        return JsonResponse(comunas, safe=False, status=200)
    except Exception as e:
        return JsonResponse(
            {"error": f"Error inesperado al obtener comunas: {str(e)}"},
            status=500
        )
API_KEY = "06244c53b5864b05877581700ea03308"

@require_POST
def calculate_shipping(request):
    try:
        data = json.loads(request.body)
        destination_code = data.get('destination_code')
        
        if not destination_code:
            return JsonResponse({'error': 'Código de destino es requerido'}, status=400)

        # Fixed weight of 5kg
        package_weight = 5
            
        # Get cart total for declared worth
        cart = request.session.get('cart', {})
        cart_total = 0
        for product_id, quantity in cart.items():
            product = Product.objects.get(id=product_id)
            price = product.get_latest_price()
            if price:
                cart_total += price.total * quantity

        # Initialize Chilexpress client and calculate shipping
        client = ChilexpressClient(api_key=API_KEY)
        try:
            result = client.calculate_shipping(
                origin_county_code=ORIGIN_COMUNA,
                destination_county_code=destination_code,
                package_weight=package_weight,
                declared_worth=cart_total
            )
            
            # Add more details to the response
            return JsonResponse({
                'success': True,
                'cost': result['cost'],
                'service_type': result['service_type'],
                'service_description': result.get('service_description', ''),
                'delivery_time': result.get('delivery_time', '')
            })
            
        except ValueError as e:
            return JsonResponse({
                'error': f'Error al calcular el envío: {str(e)}',
                'details': 'Por favor, verifica que la comuna seleccionada sea válida.'
            }, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido en la solicitud.'}, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Error inesperado: {str(e)}',
            'details': 'Por favor, intenta nuevamente más tarde.'
        }, status=500)

# Add these constants at the top of the file
COMUNAS = [
    {"code": "STGO", "name": "Santiago"},
    {"code": "PROV", "name": "Providencia"},
    {"code": "LCON", "name": "Las Condes"},
    {"code": "NUNO", "name": "Ñuñoa"},
    {"code": "VALP", "name": "Valparaíso"},
    {"code": "VINA", "name": "Viña del Mar"},
    {"code": "CONC", "name": "Concepción"},
]

ORIGIN_COMUNA = "STGO"  # Santiago como origen por defecto

@require_GET
def get_comunas(request):
    """Return list of available communes"""
    return JsonResponse(COMUNAS, safe=False)