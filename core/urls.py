from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'products', views.ProductViewSet)

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.category_products, name='category_products'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('api/', include(router.urls)),
    path('login/', views.login_page, name='login'),
] 