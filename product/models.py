from django.db import models
from category.models import Category
class Product(models.Model):
    name=models.CharField(max_length=40)
    description=models.TextField()
    image=models.ImageField(upload_to='products/',null=True,blank=True)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    is_availabel=models.BooleanField(default=True)
    category=models.ForeignKey(Category,on_delete=models.CASCADE)
