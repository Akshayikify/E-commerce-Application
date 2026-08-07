from django.urls import path
from . import views
urlpatterns=[
    path('',views.home,name='home'), # URL path for 'home' page
    path('register',views.register,name='register'), # URL path for Registration page
    path('logout',views.logout_view,name='logout'), # URL path for logout page
    path('products/<int:pk>',views.product_detail,name='product_detail'), #URL path for detailed product page
    path('cart/',views.cart_detail,name='cart'),# URL path for cart page
    path('cart/add/<int:pk>/',views.add_to_cart,name='add_to_cart'), #URL path for add to cart
    path('cart/remove/<int:pk>/',views.remove_cart_item,name='remove_cart_item'), # URL path for remove items from cart
    path('customer/<int:customer_id>/',views.customer_profile,name='profile') #URL path for customer profile
]
