from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework import viewsets
from .models import Product, Category
from .serializers import ProductSerializer
from django.views.decorators.http import require_POST

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
        'message': 'Producto agregado al carrito',
        'cart_total': cart_total
    })

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

def login_page(request):
    return render(request, 'core/login.html', {
        'title': 'Pantalla de Inicio de Sesión'
    })