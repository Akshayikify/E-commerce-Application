from .models import CartItem, Category


def navigation_context(request):
    """Provide the shared navbar with categories and the user's cart count."""
    cart_item_count = 0

    if request.user.is_authenticated:
        cart_item_count = CartItem.objects.filter(
            cart__customer__user=request.user
        ).count()

    return {
        "categories": Category.objects.all(),
        "cart_item_count": cart_item_count,
    }
