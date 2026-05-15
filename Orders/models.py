from django.db import models
from products.models import Product
from category.models import Category
from django.contrib.auth.models import User
class Order(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    category=models.ForeignKey(Category,on_delete=models.CASCADE)
    class OrderStatus(models.TextChoices):
        DELIVERED='DR'
        NOTDELIVERED='ND'
        DELAYED='DE'
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    order_status=models.CharField(max_length=2,choices=OrderStatus)
    
