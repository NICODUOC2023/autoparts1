from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('category/<slug:category_slug>/', views.category_products, name='category_products'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/process/', views.process_payment, name='process_payment'),
    path('payment/start/', views.start_payment, name='start_payment'),
    path('payment/return/', views.payment_return, name='payment_return'),
    path('payment/receipt/<str:buy_order>/', views.download_receipt, name='download_receipt'),
    path('search/', views.search_products, name='search_products'),
    path('get-comunas/', views.get_comunas, name='get_comunas'),
    path('get-comunas/<str:region_code>/', views.get_comunas_view, name='get_comunas_by_region'),
    path('calculate-shipping/', views.calculate_shipping, name='calculate_shipping'),
    path('b2b/login/', views.b2b_login, name='b2b_login'),
    path('b2b/dashboard/', views.b2b_dashboard, name='b2b_dashboard'),
    path('b2b/logout/', views.b2b_logout, name='b2b_logout'),
] + router.urls