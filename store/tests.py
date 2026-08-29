from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Cart, CartItem, Category, Customer, Product


class NavigationContextTests(TestCase):
    def test_inherited_navbar_receives_categories_and_cart_count(self):
        user = User.objects.create_user(username="shopper", password="test-pass")
        customer = Customer.objects.create(
            user=user,
            email="shopper@example.com",
            phone="+919000000001",
            address="Test address",
        )
        category = Category.objects.create(name="Electronics")
        product = Product.objects.create(
            title="Headphones",
            title_kn="Headphones",
            description="Test product",
            price="100.00",
            category=category,
        )
        cart = Cart.objects.create(customer=customer)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        self.client.force_login(user)
        response = self.client.get(reverse("cart"))

        self.assertContains(response, "Electronics")
        self.assertEqual(response.context["cart_item_count"], 1)
