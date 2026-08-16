from django.contrib import admin
from .models import Product,Order,Customer,Rating,Category,Cart,CartItem,Payment
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Customer)
admin.site.register(Rating)
admin.site.register(Category)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Payment)


