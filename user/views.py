from django.shortcuts import render,redirect
from .forms import UserRegistrationForm
from django.contrib import messages
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import authenticate,login as auth_login
from django.contrib.auth.forms import AuthenticationForm 
import os
from dotenv import load_dotenv
load_dotenv()
def home(request):
    return render(request,'index.html',{'title':'home'})
def Login(request):
    if request.method=='POST':
        form=AuthenticationForm(data=request.POST)
        if form.is_valid():
            username=form.cleaned_data.get('username')
            password=form.cleaned_data.get('password')
            user=authenticate(request,username=username,password=password)
            if user is not None:
                auth_login(request,user)
                messages.success(request,f'welcome {username}')
                return redirect('home')
            else:
                messages.error(request,f'Account does not exist please Signup')
    else:
        form=AuthenticationForm()
    return render(request,'login.html',{'form':form,'title':'login'})
            
        
def register(request):
    if request.method=='POST':
        form=UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username=form.cleaned_data.get('username')
            email=form.cleaned_data.get('email')
            html_temp=get_template('email.html')
            d={'username':username}
            subject,from_email,to='welcome',os.getenv('EMAIL_HOST_USER'),email
            html_content=html_temp.render(d)
            msg=EmailMultiAlternatives(subject,'Please view this email in an HTML-supported client.',from_email,[to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            messages.success(request,f'Your account has been successfully created! You can login now!')
            return redirect('login')
    else:
        form=UserRegistrationForm()
    return render(request,'register.html',{'form':form,'title':'register'})
            
