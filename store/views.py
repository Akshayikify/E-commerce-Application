from django.shortcuts import render,redirect,get_object_or_404
from .forms import RegistrationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login,logout
from translate import Translator
from django.views.decorators.http import require_POST
from .models import Customer,Product,Cart,CartItem,Category,Order,OrderItem,Payment
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
import razorpay
from django.conf import settings

def register(request):
    if request.method=='POST':
        form=RegistrationForm(request.POST)
        if form.is_valid():
            user=User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                # first_name=form.cleaned_data['first_name'],
                # last_name=form.cleaned_data['last_name']
            )
            Customer.objects.create(
                user=user,
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address'],
                email=form.cleaned_data['email']
            )
            return redirect("login")
    else:
        form=RegistrationForm()
    return render(request,'register.html',{'form':form})
        
def login_view(request):
    if request.method=='POST':
        form=AuthenticationForm(request,data=request.POST)
        if form.is_valid():
            user=form.get_user()
            login(request,user)
            return redirect('home')
    else:
        form=AuthenticationForm()
    return render(request,'login.html',{'form':form})

def logout_view(request):
    logout(request)
    return redirect('home')

def home(request):
    query=request.GET.get('q',"").strip()
    category_id=request.GET.get('category','').strip()
    products=Product.objects.only('id','product_image','title','price').order_by('id')
    categories=Category.objects.all()
    if category_id:
        products=Product.objects.filter(category_id=category_id)
    cart_item_count=0
    if request.user.is_authenticated:
        try:
            profile=request.user.customer
            cart_item_count=CartItem.objects.filter(cart__customer=profile).count()
        except Exception:
            profile=None
    if query:
        products=Product.objects.filter(
            Q(title__icontains=query)|
            Q(description__icontains=query)|
            Q(category__name__icontains=query)
        ).distinct()
        if products.exists():
            messages.success(request,"Product found successfully")
        else:
            messages.warning(request,'No product found')
    paginator=Paginator(products,4)
    page_no=request.GET.get('page')
    page_obj=paginator.get_page(page_no)
    context={
        'products':page_obj,
        'query': query,
        'cart_item_count':cart_item_count,
        'page_obj': page_obj,
        'categories':categories,
        'selected_category': category_id
        }
    return render(request,"home.html",context)

def product_detail(request,pk):
    product=get_object_or_404(Product,id=pk)
    translation=product.title_kn or product.title
    return render(request,'product.html',{'product':product,'translation':translation})
    
@login_required
@require_POST
def add_to_cart(request,pk):
    product=get_object_or_404(Product,pk=pk)
    profile=request.user.customer
    cart,_=Cart.objects.get_or_create(customer=profile)
    
    try:
        quantity=int(request.POST.get('quantity',1))
        if quantity<1:
            quantity=1
    except ValueError:
        quantity=1
    
    cart_item,created=CartItem.objects.get_or_create(
        product=product,
        cart=cart,
        defaults={
            'quantity': quantity
        }
    )
    
    if not created:
        cart_item.quantity+=quantity
        cart_item.save()
        messages.success(request,f"Updated quantity for {product.title}")
    else:
        messages.success(request,f"{product.title} is added to your cart.")
    
    return redirect('cart')

@login_required
def cart_detail(request):
    cart=Cart.objects.filter(customer=request.user.customer).prefetch_related('items__product').first()
    return render(request,'cart.html',{'cart': cart})
@login_required
def update_quantity(request,pk):
    cart_item=CartItem.objects.get(pk=pk)
    try:
        quantity=int(request.POST.get('quantity',1))
    except ValueError:
        quantity=1
    
    if quantity<=0:
        cart_item.delete()
        messages.success(request,f"{cart_item.product.title} was removed successfully!")
    else:
        cart_item.quantity=quantity
        cart_item.save()
        messages.success(request,"Cart quantity updated")
    return redirect('cart')
@login_required
def remove_cart_item(request,pk):
    cart_item=get_object_or_404(CartItem,id=pk,cart__customer__user=request.user)
    cart_item.delete()
    messages.success(request,f"{cart_item.product.title} is removed from cart")
    return redirect('cart')
@login_required
def customer_profile(request,customer_id):
    customer=Customer.objects.get(pk=customer_id)
    return render(request,'customer.html',{'customer': customer})

@login_required(login_url='login')
def checkout(request): 
    customer=get_object_or_404(
        Customer,
        user=request.user
    )
    cart=Cart.objects.filter(customer=customer).prefetch_related('items__product').first()
    cart_items=CartItem.objects.select_related('product')
    total_price=sum(item.total_price for item in cart_items)
    if request.method=='POST':
        shipping_address=request.POST.get('address')
        phone=request.POST.get('phone')
        order=Order.objects.create(
            customer=customer,
            shipping_address=shipping_address,
            phone=phone,
            status=Order.Order_Status.PENDING
        )
        
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            
        return redirect('payment',order_id=order.id)
    
    return render(request,'checkout.html',
                  {'cart_items': cart_items,
                   'total_price': total_price,
                   })    


@login_required
def payment(request,order_id):
    customer=get_object_or_404(
        Customer,
        user=request.user,
    )
    order=get_object_or_404(
        Order,
        id=order_id,
        customer=customer
    )
    if order.status!=Order.Order_Status.PENDING:
        return redirect(
            'order_success',
            order_id=order.id
        )
    client = razorpay.Client(auth=
    (settings.RAZORPAY_KEY_ID, 
    settings.RAZORPAY_KEY_SECRET
    ))
    total=sum(item.total_price for item in order.items.all())
    amount=int(total*100)

    razorpay_order=client.order.create({
    "amount": amount,
    "currency": "INR",
    "receipt": f"order_{order.id}",
    })
    
    payment=Payment.objects.create(
        order=order,
        razorpay_order_id=razorpay_order['id'],
        amount=total 
    )
    return render(
        request,
        'payment.html',
        {
            'payment': payment,
            'order': order,
            'amount': amount,
            'amount_rupees': total,
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'customer': customer
        })