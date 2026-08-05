from django.urls import path
from . import views
urlpatterns=[
    path('',views.home,name='home'),
    path('register',views.register,name='register'),
    path('login',views.login_view,name='login'),
    path('logout',views.logout_view,name='logout'),
    path('products/<int:pk>',views.product_detail,name='product_detail'),
    path('cart/',views.cart_detail,name='cart'),
    path('cart/add/<int:pk>/',views.add_to_cart,name='add_to_cart'),
    path('cart/remove/<int:pk>/',views.remove_cart_item,name='remove_cart_item'),
    
]
