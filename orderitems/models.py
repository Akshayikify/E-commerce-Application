from django.db import models
from order.models import Order
from product.models import Product
class OrderItems(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    quantity=models.PositiveIntegerField()
    sub_total=models.DecimalField(max_digits=10,decimal_places=2)
    
    
