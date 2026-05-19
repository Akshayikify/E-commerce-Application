from django.db import models
from django.contrib.auth.models import User
from product.models import Product
class Order(models.Model):
    class Status_Code(models.TextChoices):
        PENDING="PD","Pending"
        SHIPPED="SH","Shipped"
        DELAYED="DL","Delayed"
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    status=models.CharField(max_length=2,choices=Status_Code.choices)
    
    
    
    
        
