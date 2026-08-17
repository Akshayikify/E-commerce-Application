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
import requests
from django.conf import settings
import json
from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal
from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
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

    customer = get_object_or_404(
        Customer,
        user=request.user
    )

    cart = Cart.objects.filter(
        customer=customer
    ).first()

    # Customer does not have a cart
    if not cart:
        messages.warning(
            request,
            "Your cart is empty."
        )
        return redirect('cart')

    # Get ONLY this customer's cart items
    cart_items = cart.items.select_related(
        'product'
    ).all()

    # Empty cart
    if not cart_items.exists():
        messages.warning(
            request,
            "Your cart is empty."
        )
        return redirect('cart')

    # Calculate cart total
    total_price = sum(
        item.total_price
        for item in cart_items
    )

    if request.method == 'POST':

        shipping_address = request.POST.get(
            'address'
        )

        phone = request.POST.get(
            'phone'
        )

        with transaction.atomic():

            # Create Order
            order = Order.objects.create(
                customer=customer,
                shipping_address=shipping_address,
                phone=phone,
                status=Order.Order_Status.PENDING
            )

            # Create OrderItems from THIS customer's cart
            for item in cart_items:

                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

        return redirect(
            'payment',
            order_id=order.id
        )

    return render(
        request,
        'checkout.html',
        {
            'cart_items': cart_items,
            'total_price': total_price,
        }
    )


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
    total=sum(item.total_price for item in order.items.all())
    amount = float(total)

    cashfree_order_id = f"order_{order.id}"
    headers = {
        "Content-Type": "application/json",
        "x-api-version": settings.CASHFREE_API_VERSION,
        "x-client-id": settings.CASHFREE_APP_ID,
        "x-client-secret": settings.CASHFREE_SECRET_KEY,
    }
    payload = {
        "order_id": cashfree_order_id,
        "order_amount": amount,
        "order_currency": "INR",

        "customer_details": {
            "customer_id": str(customer.id),
            "customer_name": customer.user.username,
            "customer_email": customer.email,
            "customer_phone": str(customer.phone),
        },

        "order_meta": {
            "return_url": (
                request.build_absolute_uri(
                    f"/payment/return/?order_id={cashfree_order_id}"
                )
            )
        },

        "order_note": f"Payment for Django Order #{order.id}",
    }
    
    try:

        response = requests.post(
            f"{settings.CASHFREE_BASE_URL}/orders",
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        cashfree_order = response.json()

    except requests.RequestException as e:

        print("Cashfree order creation error:", e)

        return render(
            request,
            "payment.html",
            {
                "order": order,
                "amount_rupees": total,
                "error": "Unable to create payment order."
            }
        )
    
    payment, created = Payment.objects.update_or_create(
        order=order,
        defaults={
            "cashfree_order_id": cashfree_order["order_id"],
            "amount": total,
            "status": Payment.PaymentStatus.PENDING,
        }
    )
    return render(
        request,
        "payment.html",
        {
            "payment": payment,
            "order": order,
            "amount_rupees": total,
            "payment_session_id": cashfree_order[
                "payment_session_id"
            ],
            "customer": customer,
        }
    )
 
@login_required
def order_success(request,order_id):
    customer=get_object_or_404(
        Customer,
        user=request.user
    )
    order=get_object_or_404(
        Order,
        id=order_id,
        customer=customer
    )
    
    return render(
        request,
        "order_success.html",
        {
            "order": order
        }
    )

@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product'),
        id=order_id,
        customer__user=request.user,
    )

    # Generate a PDF invoice for the customer.  ``order.items`` is a related
    # manager, so an order can contain multiple OrderItem objects.
    buf=io.BytesIO()
    c=canvas.Canvas(buf,pagesize=letter,bottomup=0)
    text_ob=c.beginText()
    text_ob.setTextOrigin(inch,inch)
    text_ob.setFont('Helvetica',14)
    lines = [
        "E-Commerce Bengaluru",
        f"Invoice for Order #{order.id}",
        "",
    ]

    for item in order.items.all():
        lines.extend([
            f"Product Name: {item.product.title}",
            f"Product Quantity: {item.quantity}",
            f"Price: {item.price}",
            f"Item Total: {item.total_price}",
            "",
        ])

    lines.append(f"Order Total: {order.total_price}")
        
    for line in lines:
        text_ob.textLines(line)
            
    c.drawText(text_ob)
    c.showPage()
    c.save()
    buf.seek(0)
    return FileResponse(buf,as_attachment=True,filename=f'invoice-order-{order.id}.pdf')
@login_required
def payment_return(request):

    cashfree_order_id = request.GET.get("order_id")

    if not cashfree_order_id:
        return render(
            request,
            "payment_failed.html",
            {
                "message": "Payment order ID is missing."
            }
        )

    customer = get_object_or_404(
        Customer,
        user=request.user
    )

    payment = get_object_or_404(
        Payment,
        cashfree_order_id=cashfree_order_id,
        order__customer=customer
    )

    headers = {
        "x-api-version": settings.CASHFREE_API_VERSION,
        "x-client-id": settings.CASHFREE_APP_ID,
        "x-client-secret": settings.CASHFREE_SECRET_KEY,
    }

    try:

        response = requests.get(
            f"{settings.CASHFREE_BASE_URL}/orders/"
            f"{cashfree_order_id}",

            headers=headers,

            timeout=30
        )

        response.raise_for_status()

        cashfree_order = response.json()

    except requests.RequestException as e:

        print("Cashfree status error:", e)

        return render(
            request,
            "payment_failed.html",
            {
                "message":
                    "Unable to verify payment status."
            }
        )

    order_status = cashfree_order.get(
        "order_status"
    )

    print(
        "Cashfree order status:",
        order_status
    )

    if order_status == "PAID":

        payment.status = (
            Payment.PaymentStatus.SUCCESS
        )

        payment.save()

        order = payment.order

        order.status = (
            Order.Order_Status.PAID
        )

        order.save()

        # Clear cart only after successful payment
        cart = Cart.objects.filter(
            customer=order.customer
        ).first()

        if cart:
            cart.items.all().delete()

        return redirect(
            "order_success",
            order_id=order.id
        )

    elif order_status in ["FAILED", "CANCELLED"]:

        payment.status = (
            Payment.PaymentStatus.FAILED
        )

        payment.save()

        return render(
            request,
            "payment_failed.html",
            {
                "order": payment.order,
                "message":
                    "Payment was unsuccessful."
            }
        )

    else:

        return render(
            request,
            "payment_failed.html",
            {
                "order": payment.order,
                "message":
                    "Payment is still being processed."
            }
        )
