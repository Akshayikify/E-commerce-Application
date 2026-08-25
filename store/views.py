from django.shortcuts import render,redirect,get_object_or_404
from .forms import RegistrationForm,RatingForm,CustomerUpdateForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login,logout
from django.views.decorators.http import require_POST
from .models import Customer,Product,Cart,CartItem,Category,Order,OrderItem,Payment,Rating
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q,Case,Value,When,IntegerField
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
import requests
from django.conf import settings
import json
import io
import datetime
from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal
from reportlab.lib import colors
from django.http import FileResponse
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums  import TA_CENTER,TA_RIGHT
from reportlab.platypus import SimpleDocTemplate,Table,Paragraph,Spacer
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from django.db.models import Avg
from .tasks import send_confirmation_mail
from django.http import HttpResponse
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
    products=Product.objects.annotate(avg_rating=Avg('ratings__rating')).order_by('id')
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
        ).annotate(priority=Case(
            When(title__iexact=query,then=Value(3)),
            When(description__iexact=query,then=Value(2)),
            When(category__name__iexact=query,then=Value(1)),
            default=Value(0),
            output_field=IntegerField()
        )).order_by('-priority').distinct()
        if products.exists():
            messages.success(request,"Product found successfully")
        else:
            messages.warning(request,'No product found')
    paginator=Paginator(products,8)
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
def customer_profile(request):

    customer = get_object_or_404(Customer, user=request.user)

    show_modal = False

    if request.method == 'POST':

        form = CustomerUpdateForm(request.POST, instance=customer)

        if form.is_valid():
            form.save()

            messages.success(request, 'Your profile has been updated!')

            return redirect('profile')

        else:
            messages.error(request, 'Please correct the errors below.')
            show_modal = True

    else:
        form = CustomerUpdateForm(instance=customer)

    return render(
        request,
        'customer.html',
        {
            'customer': customer,
            'form': form,
            'show_modal': show_modal
        }
    )

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

    # Stock Management
    available = all(
        item.product.stock >= item.quantity
        for item in cart_items
    )

    # Calculate cart total
    total_price = sum(
        item.total_price
        for item in cart_items
    )

    if request.method == 'POST':

        if not available:
            messages.warning(request, "One or more items are no longer in stock.")
            return redirect('checkout')

        shipping_address = request.POST.get(
            'address'
        )

        phone = request.POST.get(
            'phone'
        )

        with transaction.atomic():

            # Lock and re-check the products immediately before creating the
            # order.  This prevents two simultaneous checkouts from selling
            # more units than are in stock.
            locked_products = {
                item.product_id: Product.objects.select_for_update().get(
                    pk=item.product_id
                )
                for item in cart_items
            }

            if any(
                locked_products[item.product_id].stock < item.quantity
                for item in cart_items
            ):
                messages.warning(
                    request,
                    "One or more items are no longer in stock."
                )
                return redirect('checkout')

            # Create Order
            order = Order.objects.create(
                customer=customer,
                shipping_address=shipping_address,
                phone=phone,
                status=Order.Order_Status.PENDING
            )

            # Create OrderItems from THIS customer's cart
            for item in cart_items:
                product = locked_products[item.product_id]

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    price=product.price
                )

                product.stock -= item.quantity
                product.save(update_fields=['stock'])

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
            'available': available,
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
    buf=io.BytesIO()
    lines=[]
    title=ParagraphStyle(
        name='TitleStyle',
        fontName='Helvetica-Bold',
        fontSize=24,
        alignment=TA_CENTER
    )
    lines.append(Paragraph('E-Commerce Application', title))
    lines.append(Spacer(1,20))
    doc=SimpleDocTemplate(buf,pagesize=letter,rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40) 
    table_data=[
        ["Product Title","Product Quantity","Product Price","Total Price"]
    ]
    for item in order.items.all():
        table_data.extend(
            [[item.product.title,item.quantity,item.product.price,item.total_price]]
        )
    table = Table(table_data,colWidths=[180, 90, 90, 90],style=[('ALIGN',(0,0),(-1,-1),'CENTER'),('LINEBELOW',(0,0),(-1,-1),1,colors.black)])
    lines.append(table)
    lines.append(Spacer(1,20))
    order_total=ParagraphStyle(
        name='Normal',
        fontName='Helvetica',
        fontSize=12,
        alignment=TA_RIGHT
    )
    lines.append(Paragraph(f'Order Total: Rs. {order.total_price}', order_total))
    doc.build(lines)      
    buf.seek(0)
    return FileResponse(buf,as_attachment=True,filename=f'invoice_order{order.id}.pdf')
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

@login_required
# Order Management
def Order_mngt(request):
    customer=get_object_or_404(Customer,user=request.user)
    orders=Order.objects.filter(customer=customer).prefetch_related('items__product').order_by('-created_at')
    return render(request,'order_history.html',{'orders': orders})
def order_items(request,order_id):
    
    order=Order.objects.get(pk=order_id)
    return render(request,'order_items.html',{'order': order})
    
@login_required
def order_detail(request,order_item_id):
    order_item=OrderItem.objects.get(pk=order_item_id)
    
    customer=get_object_or_404(Customer,user=request.user)
    if request.method=='POST':
        form=RatingForm(request.POST)
        if form.is_valid():
            rating=form.cleaned_data['rating']
            Rating.objects.create(rating=rating,customer=customer,product=order_item.product)
            messages.success(request,f"Rating has been successfully submitted for {order_item.product.title}")
            return redirect('orders')
    else:
        form=RatingForm()
    time=datetime.datetime.now()
    formatted_time=time.strftime('%I:%M %p')
    return render(request,'order_detail.html',{'order_item': order_item,'time': formatted_time,'form': form})


@login_required
def order_confirmation_mail(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if order.status == Order.Order_Status.PAID:
        if order.customer.email:
            send_confirmation_mail.delay(order_id, order.customer.email)
            return HttpResponse(f"Confirmation mail triggered for Order #{order.id} to {order.customer.email}.")
        return HttpResponse(f"No email address found for customer of Order #{order.id}.", status=400)
    return HttpResponse(f"Order #{order.id} is not in a paid status (Current status: {order.status}).", status=400)


    