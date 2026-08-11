from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator,MaxValueValidator
from datetime import datetime
from translate import Translator
class Category(models.Model):
    """
    This class stores the all the categories of product like Home appliances , Electronics ,.etc. 
    """
    name=models.CharField(max_length=200)
    
    class Meta:
        verbose_name_plural='Categories'
    
    def __str__(self):
        return self.name
class Product(models.Model):
    """ This model class creates the table named products in sqllite database storing the meta data about the product."""
    title=models.CharField(max_length=120)
    product_image=models.ImageField(upload_to='products/',null=True)
    description=models.TextField()
    price=models.DecimalField(decimal_places=2,max_digits=7,default=45.78)
    category=models.ForeignKey(Category,on_delete=models.CASCADE,related_name='categories')
    title_kn=models.CharField(max_length=255,blank=True,null=True)
    def save(self,*args,**kwargs):
        if not self.title_kn and self.title:
            try:
                language='kn'
                translator=Translator(to_lang=language)
                self.title_kn=translator.translate(self.title)
            except:
                self.title_kn=self.title
        super().save(*args, **kwargs)
         
    def __str__(self):
        return self.title
class Customer(models.Model):
    """ Here User model is extended to create a Customer profile."""
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    email=models.EmailField()
    phone=PhoneNumberField(unique=True,region='IN')
    address=models.TextField()
    
    def __str__(self):
        return self.user.username
class Order(models.Model):
    """ It creates Orders table , which stores the shipping data of the customer orders.Each order bound to a authenticated customer"""
    class Order_Status(models.TextChoices):
        PENDING='PEN','pending'
        PAID='PD','paid'
        SHIPPED='SH','shipped'
        DELIVERED='DL','delivered'
        CANCELED='CL','canceled'
    customer=models.ForeignKey(Customer,on_delete=models.CASCADE,related_name='orders')
    shipping_address=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    phone=PhoneNumberField(region='IN')
    status=models.CharField(max_length=3,choices=Order_Status.choices,default=Order_Status.PENDING)
    
    def __str__(self):
        return f"Order #id {self.id}- {self.customer.user.username}"

class OrderItem(models.Model):
    """ It stores the ordered items,thier quantities and prices extending the order model . There is one to Many relationship with product."""
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    price=models.DecimalField(max_digits=7,decimal_places=2)
    quantity=models.PositiveBigIntegerField(default=1)
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items')
    
    @property
    def total_price(self):
        return self.quantity*self.price
    
    def __str__(self):
        return f"{self.quantity} x {self.product.title}"
class Rating(models.Model):
    """Rating is bound to authenticated customer and product selected for checkout."""
    customer=models.ForeignKey(Customer,on_delete=models.CASCADE,related_name='ratings')
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    rating=models.PositiveSmallIntegerField(validators=[MinValueValidator(1),MaxValueValidator(5)])
    class Meta:
        unique_together=('customer','product')
class Cart(models.Model):
    """ Cart is bound to authenticated customer and stores datetime of creation. """
    customer=models.OneToOneField(Customer,on_delete=models.CASCADE,related_name='cart')
    created_at=models.DateTimeField(auto_now_add=True)
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())
    def __str__(self):
        return f"{self.customer.user.username} is connected to cart"

class CartItem(models.Model):
    """ There is a one many to relationship with cart and product and gets the quantity through POST request stores in 'quantity' attribure. """
    product=models.OneToOneField(Product,on_delete=models.CASCADE)
    cart=models.ForeignKey(Cart,on_delete=models.CASCADE,related_name='items')
    quantity=models.PositiveIntegerField(default=1)
    class Meta:
        unique_together=('cart','product')
    @property
    def total_price(self):
        return self.product.price*self.quantity
    
