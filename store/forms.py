from django import forms
from django.contrib.auth.models import User
from .models import Customer
from django.contrib.auth.forms import AuthenticationForm

class RegistrationForm(forms.Form):
    #Create first_name field 
    first_name=forms.CharField(max_length=50)
    #Create first_name field 
    last_name=forms.CharField(max_length=50)
    #Username field a character field
    username=forms.CharField(max_length=100)
    #Create a email field 
    email=forms.EmailField()
    #Phone field with maximum of 15 digits
    phone=forms.CharField(max_length=15)
    #Address with textarea widget
    address=forms.CharField(widget=forms.Textarea)
    #Create a password field with password widget
    password=forms.CharField(widget=forms.PasswordInput)
    confirm_password=forms.CharField(widget=forms.PasswordInput)
    
    def clean(self):
        cleaned=super().clean()
        if cleaned.get('password')!=cleaned.get('confirm_password'):
            raise forms.ValidationError("Password doesn't match")
        return cleaned

class LoginForm(AuthenticationForm):
    pass   