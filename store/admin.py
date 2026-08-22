from django.contrib import admin
from .models import Product,Order,Customer,Rating,Category,Cart,CartItem,Payment,OrderItem
from django.utils.html import format_html
from django.utils.http import urlencode
from django.urls import reverse
@admin.register(OrderItem)
class OrderItem(admin.ModelAdmin):
    list_display=['id','product','price','quantity','view_order']
    list_filter=['price']
    search_fields=['id']
    def view_order(self,obj):
        url=reverse('admin:store_order_change',args=[obj.order.id])
        return format_html('<a href={}>{}</a>',url,obj.order.id)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display=('title','description','price','category','stock')
    list_editable=['price','stock']
    search_fields=['title','price']
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display=['id','customer','status_badge','shipping_address','created_at']
    list_filter=['status','created_at']
    search_fields=['id','customer__user__username']
    @admin.display(description='Status')
    def status_badge(self,obj):
        colors={
            'pending': '#f39c12',
            'paid': '#3498db',
            'shipped': '#9b59b6',
            'delivered': '#2ecc71',
            'cancelled': '#e74c3c',
        }
        color=colors.get(obj.status.lower(),'#7f8c8d')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.status
        )
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display=['id','user__username','email','phone','total_orders_display']
    search_fields=['id','user__username']
    
    @admin.display(description='Total Orders')
    def total_orders_display(self,obj):
        total_orders=obj.orders.count()
        return total_orders
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display=['id','customer','product','rating','average_rating']
    search_fields=['rating']
    @admin.display(description='Average Rating')
    def average_rating(self,obj):
        from django.db.models import Avg
        avg_rating=Rating.objects.aggregate(avg=Avg('rating'))
        return avg_rating['avg']
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display=['customer','created_at']
    list_filter=['created_at']
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display=['name']
    search_fields=['name']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display=['id','product__title','cart__id','quantity']
    search_fields=['quantity'] #Foreign Key searching is not allowed so used 'quantity'
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display=['cashfree_payment_id','cashfree_order_id','razorpay_signature','payment_status','amount','created_at']
    list_filter=['created_at']
    search_fields=['cashfree_order_id']
    @admin.display(description='Status')
    def payment_status(self,obj):
        colors={
                'success': '#2ecc71',
                'failed': '#e74c3c',
                'created': '#3498db',
                'pending': '#f39c12'
            }
        color=colors.get(obj.status.lower(),'#7f8c8d')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.status
        )

