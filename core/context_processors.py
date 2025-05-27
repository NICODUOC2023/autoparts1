from .models import Product

def cart_processor(request):
    cart = request.session.get('cart', {})
    cart_total = sum(cart.values())
    return {
        'cart_total': cart_total
    }

def cart_items_count(request):
    cart = request.session.get('cart', {})
    total_items = sum(cart.values())
    return {'cart_items_count': total_items} 