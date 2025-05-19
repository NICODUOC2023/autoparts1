def cart_processor(request):
    cart = request.session.get('cart', {})
    cart_total = sum(cart.values())
    return {
        'cart_total': cart_total
    } 