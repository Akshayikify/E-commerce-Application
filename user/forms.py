from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegistrationForm(UserCreationForm):
    username=forms.CharField(max_length=35,required="True")
    first_name=forms.CharField(max_length=15,required="True")
    email=forms.EmailField()
    last_name=forms.CharField(max_length=15,required="True")
    class Meta:
        model=User
        fields=['username','email','first_name','last_name','password1','password2']
    
