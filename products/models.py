from django.db import models
from category.models import Category
class Product(models.Model):
    name=models.CharField(max_length=50)
    price=models.FloatField(decimal_places=2,max_digits=6)
    category=models.ForeignKey(Category,on_delete=models.CASCADE)
    description=models.TextField()
    image=models.ImageField(upload_to='/products')
    
    def __str__(self):
        return self.name
    
