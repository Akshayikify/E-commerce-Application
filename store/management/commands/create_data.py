from store.models import Customer,Product,Order,Rating,Category
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help='Populate the database with mock data'
    def handle(self,*args,**kwargs):
        user=User.objects.filter(username='AkshayH')
        if not user.exists():
            User.objects.create_superuser(username='admin',password='test@123$')
        else:
            user=user
        categories=[{'name':'Accessories & Shoes'},
                    {'name':'Electronics'},
                    {'name':'Home, Garden & Tools'},
                    {'name':'Beauty, Health & Personal Care'},
                    {'name':'Sports, Fitness & Outdoors'},
                    {'name':'Toys, Children & Baby'},
                    {'name':'Media & Entertainment'},
                    {'name':'Grocery, Food & Beverage'},
                    {'name':'Automotive & Parts'},
                    {'name':'Digital Products & Services'}]
        Category.objects.all().delete()
        for category in categories:
            Category.objects.create(**category)
        Product.objects.all().delete()