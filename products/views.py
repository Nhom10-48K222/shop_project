import random
from .forms import ReviewForm
from django.contrib import messages
from accounts.models import Cart, CartItem
from products.models import Product,  ProductReview
from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.

def get_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    sorted_size_variants = product.size_variant.all().order_by('size_name')
    related_products = list(product.category.products.filter(parent=None).exclude(uid=product.uid))

    # Review product view
    review = None
    if request.user.is_authenticated:
        # Check if the user has already reviewed the product or not.
        try:
            review = ProductReview.objects.get(product=product, user=request.user)
        except ProductReview.DoesNotExist:
            review = None
    
    # Calculate the rating percentage
    rating_percentage = 0
    if product.reviews.exists():
        rating_percentage = (product.get_rating() / 5) * 100

    # Handle form submission
    if request.method == 'POST' and request.user.is_authenticated:
        if review:
            # If review exists, update it
            review_form = ReviewForm(request.POST, instance=review)
        else:
            # Otherwise, create a new review
            review_form = ReviewForm(request.POST)

        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Đã thêm đánh giá thành công!")
            return redirect('get_product', slug=slug)
    else:
        review_form = ReviewForm()
    
    # Related product view
    if len(related_products) >= 4:
        related_products = random.sample(related_products, 4)

    context = {
        'product': product,
        'sorted_size_variants': sorted_size_variants,
        'related_products': related_products,
        'review_form': review_form,
        'rating_percentage': rating_percentage,
    }

    if request.GET.get('size'):
        size = request.GET.get('size')
        price = product.get_product_price_by_size(size)
        context['selected_size'] = size
        context['updated_price'] = price

    return render(request, 'product/product.html', context=context)

# Move to cart functionality on wishlist page.
def move_to_cart(request, uid):
    product = get_object_or_404(Product, uid=uid)

    # Get or create the user's cart
    cart, created = Cart.objects.get_or_create(user=request.user, is_paid=False)

    # Add the product to the cart with the size variant
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, size_variant=size_variant)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, "Sản phẩm đã được chuyển vào giỏ hàng thành công!")
    return redirect('cart')
