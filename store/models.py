from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User

class Category(models.Model):
    name=models.CharField(max_length=200)
    def __str__(self):
        return self.name
class Product(models.Model):
    title=models.CharField(max_length=120)
    product_image=models.ImageField(upload_to='products/',null=True)
    description=models.TextField()
    category=models.ForeignKey(Category,on_delete=models.CASCADE)
    
    def __str__(self):
        return self.title
class Customer(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    email=models.EmailField()
    phone=PhoneNumberField(unique=True,region='IN')
    address=models.TextField()
    
    def __str__(self):
        return self.user.username
class Order(models.Model):
    products=models.ForeignKey(Product,on_delete=models.CASCADE)
    customer=models.ForeignKey(Customer,on_delete=models.CASCADE)
    quantity=models.IntegerField(default=1)
    price=models.IntegerField()
    address=models.TextField()
    datetime=models.DateTimeField()
    phone=PhoneNumberField(region='IN')
    status=models.BooleanField(default=False)
    @property
    def get_total_price(self):
        return self.price*self.quantity
class Rating(models.Model):
    customer=models.ForeignKey(Customer,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    rating=models.PositiveSmallIntegerField()
        
    
    
    
