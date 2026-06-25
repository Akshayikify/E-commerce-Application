from django.contrib.auth.models import User
from store.models import Customer
def run():
    user=User.objects.all().values()
    print(user)
    