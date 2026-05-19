from django.db import models
from django.contrib.auth.models import User
from orderitems.models import OrderItems
class Cart(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    order_items=models.ForeignKey(OrderItems,on_delete=models.SET_NULL,null=True)
    confirm_order=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    
    
