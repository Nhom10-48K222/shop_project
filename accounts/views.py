import json
import uuid

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from accounts.forms import UserUpdateForm, UserProfileForm, ShippingAddressForm, CustomPasswordChangeForm
from accounts.models import Profile, Cart, CartItem, Order, OrderItem
from home.models import ShippingAddress
# from weasyprint import CSS, HTML
from products.models import *


# Create your views here.


def login_page(request):
    next_url = request.GET.get('next')  # Default to 'index' if 'next' is not provided
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_obj = User.objects.filter(username=username)

        if not user_obj.exists():
            messages.warning(request, 'Không tìm thấy tài khoản!')
            return HttpResponseRedirect(request.path_info)

        #if not user_obj[0].profile.is_email_verified:
           # messages.error(request, 'Account not verified!')
           # return HttpResponseRedirect(request.path_info)

        # then authenticate user
        user_obj = authenticate(username=username, password=password)
        if user_obj:
            login(request, user_obj)
            messages.success(request, 'Đăng nhập thành công.')

            # Check if the next URL is safe
            if url_has_allowed_host_and_scheme(url=next_url, allowed_hosts=request.get_host()):
                return redirect(next_url)
            else:
                return redirect('home')

        messages.warning(request, 'Thông tin đăng nhập không hợp lệ.')
        return HttpResponseRedirect(request.path_info)

    return render(request, 'accounts/login.html')


def register_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        user_obj = User.objects.filter(username=username, email=email)

        if user_obj.exists():
            messages.info(request, 'Tên người dùng hoặc email đã tồn tại!')
            return HttpResponseRedirect(request.path_info)

        # if user not registered
        user_obj = User.objects.create(
            username=username, first_name=first_name, last_name=last_name, email=email)
        user_obj.set_password(password)
        user_obj.save()

        profile = Profile.objects.get(user=user_obj)
        profile.email_token = str(uuid.uuid4())
        profile.save()

        # send_account_activation_email(email, profile.email_token)
        messages.success(request, profile.email_token)
        return HttpResponseRedirect(request.path_info)

    return render(request, 'accounts/register.html')


@login_required
def user_logout(request):
    logout(request)
    messages.warning(request, "Đã đăng xuất thành công!")
    return redirect('home')


@login_required
def add_to_cart(request, uid):
    try:
        variant = request.GET.get('size')
        if not variant:
            messages.error(request, 'Vui lòng chọn kích thước khác nhau!')
            return redirect(request.META.get('HTTP_REFERER'))

        product = get_object_or_404(Product, uid=uid)

        cart, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)
        size_variant = get_object_or_404(SizeVariant, size_name=variant)

        # Check if the cart item already exists in the cart
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, size_variant=size_variant)

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        messages.success(request, 'Đã thêm sản phẩm vào giỏ hàng thành công.')

    except Exception:
        messages.error(request, 'Có lỗi khi thêm sản phẩm vào giỏ hàng.')

    return redirect(reverse('cart'))


@login_required
def cart(request):
    payment = None
    user = request.user

    try:
        cart_obj = Cart.objects.get(is_paid=False, user=user)

    except Exception:
        messages.warning(request, "Giỏ hàng của bạn đang trống. Vui lòng đăng nhập hoặc thêm sản phẩm vào giỏ hàng.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if request.method == 'POST':
        coupon = request.POST.get('coupon')
        coupon_obj = Coupon.objects.filter(coupon_code__exact=coupon).first()

        if not coupon_obj:
            messages.warning(request, 'Mã phiếu giảm giá không hợp lệ.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if cart_obj and cart_obj.coupon:
            messages.warning(request, 'Mã giảm giá đã tồn tại.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if coupon_obj and coupon_obj.is_expired:
            messages.warning(request, 'Mã giảm giá đã hết hạn.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if cart_obj and coupon_obj and cart_obj.get_cart_total() < coupon_obj.minimum_amount:
            messages.warning(
                request, f'Số lượng phải lớn hơn {coupon_obj.minimum_amount}')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        if cart_obj and coupon_obj:
            cart_obj.coupon = coupon_obj
            cart_obj.save()
            messages.success(request, 'Phiếu giảm giá đã được áp dụng thành công.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if cart_obj:

        cart_total_in_paise = int(cart_obj.get_cart_total_price_after_coupon() * 100)

        if cart_total_in_paise < 100:
            messages.warning(
                request, 'Tổng số tiền trong giỏ hàng ít hơn số tiền tối thiểu yêu cầu (10000vnd). Vui lòng thêm sản phẩm vào giỏ hàng.')
            return redirect('index')

        cart_obj.save()

    context = {'cart': cart_obj, 'payment': payment, 'quantity_range': range(1, 6), }
    return render(request, 'accounts/cart.html', context)


@login_required
def checkout_page(request):
    cart_id = request.GET.get('card_id', None)
    cart = Cart.objects.filter(uid=cart_id).first()

    if not cart:
        return render(request, 'base/404.html', {'message': 'Cart not found'})

    if request.method == 'GET':
        # Tính tổng giá trị giỏ hàng
        cart_items = cart.cart_items.all()

        shipping_address = ShippingAddress.objects.filter(
            user=request.user, current_address=True).first()

        form = ShippingAddressForm(instance=shipping_address)
        return render(request, 'accounts/checkout_page.html', {
            'cart': cart,
            'cart_items': cart_items,
            'form': form
        })
    elif request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=None)
        if form.is_valid():
            shipping_address = ShippingAddress.objects.filter(
                user=request.user, street=form.cleaned_data['street'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                street_number=form.cleaned_data['street_number'],
                zip_code=form.cleaned_data['zip_code'],
                city=form.cleaned_data['city'],
                country=form.cleaned_data['country'],
                phone=form.cleaned_data['phone'],
            ).first()
            if not shipping_address:
                form.user_id = request.user.id
                shipping_address = form.save(commit=False)
                shipping_address.user = request.user
                shipping_address.current_address = True
                shipping_address.save()

            cart.is_paid = True
            cart.razorpay_order_id = uuid.uuid4().hex
            cart.save()
            # Create the order after payment is confirmed
            order = create_order(cart, shipping_address)
            context = {'order_id': order.order_id, 'order': order}
            return render(request, 'payment_success/payment_success.html', context)
        else:
            messages.error(request, 'Địa chỉ không hợp lệ')
            return redirect(request.META.get('HTTP_REFERER'))
    else:
        return render(request, 'base/404.html', {'message': 'Cart not found'})


def payment_success(request, card_id):
    cart = get_object_or_404(Cart, uid=card_id)

    # Đánh dấu giỏ hàng đã thanh toán
    cart.is_paid = True
    cart.save()

    # Tạo đơn hàng
    order = create_order(cart)

    context = {
        'order_id': order.order_id,
        'order': order,
    }
    return render(request, 'payment_success/payment_success.html', context)


def create_order(cart, shipping_address=None):
    # Tạo đơn hàng từ giỏ hàng
    order = Order.objects.create(
        user=cart.user,
        order_id=cart.razorpay_order_id,
        payment_status='Thành công',
        payment_mode='COD',
        shipping_address=shipping_address if shipping_address else cart.user.profile.shipping_address,
        order_total_price=cart.get_cart_total(),
        coupon=cart.coupon,
        grand_total=cart.get_cart_total_price_after_coupon(),
        order_status = 'Chờ xác nhận',
    )

    # Tạo các sản phẩm trong đơn hàng
    for cart_item in CartItem.objects.filter(cart=cart):
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            size_variant=cart_item.size_variant,
            quantity=cart_item.quantity,
            product_price=cart_item.get_product_price()
        )

    return order

@require_POST
@login_required
def update_cart_item(request):
    try:
        data = json.loads(request.body)
        cart_item_id = data.get("cart_item_id")
        quantity = int(data.get("quantity"))

        cart_item = CartItem.objects.get(uid=cart_item_id, cart__user=request.user, cart__is_paid=False)
        cart_item.quantity = quantity
        cart_item.save()

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def remove_cart(request, uid):
    try:
        cart_item = get_object_or_404(CartItem, uid=uid)
        cart_item.delete()
        messages.success(request, 'Sản phẩm đã được xóa khỏi giỏ hàng.')

    except Exception as e:
        print(e)
        messages.warning(request, 'Có lỗi khi xóa sản phẩm khỏi giỏ hàng.')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def remove_coupon(request, cart_id):
    cart = Cart.objects.get(uid=cart_id)
    cart.coupon = None
    cart.save()

    messages.success(request, 'Đã xóa phiếu giảm giá.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# Payment success view
@login_required
def success(request):
    card_id = request.GET.get('card_id')
    cart = get_object_or_404(Cart, uid=card_id)
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=None)
        if form.is_valid():
            shipping = ShippingAddress.objects.create(
                user=cart.user,
                first_name=form.first_name,
                last_name=form.last_name,
                street=form.street,
                street_number=form.street_number,
                zip_code=form.zip_code,
                city=form.city,
                country=form.country,
                phone=form.phone
            )
            # Mark the cart as paid
            cart.is_paid = True
            cart.razorpay_order_id = uuid.uuid4().hex
            cart.save()

            # Create the order after payment is confirmed
            order = create_order(cart, shipping)

            context = {'order_id': order.order_id, 'order': order}
            return render(request, 'payment_success/payment_success.html', context)
        else:
            messages.error(request, 'Địa chỉ không hợp lệ')
            return redirect(request.META.get('HTTP_REFERER'))
    else:
        return render(request, 'base/404.html', {'message': 'Cart not found'})


def profile_view(request, username):
    user_name = get_object_or_404(User, username=username)
    user = request.user
    profile = user.profile

    user_form = UserUpdateForm(instance=user)
    profile_form = UserProfileForm(instance=profile)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Hồ sơ của bạn đã được cập nhật thành công!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    context = {
        'user_name': user_name,
        'user_form': user_form,
        'profile_form': profile_form
    }

    return render(request, 'accounts/profile.html', context)


@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Mật khẩu của bạn đã được cập nhật thành công!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            messages.warning(request, 'Vui lòng sửa lỗi bên dưới.')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def update_shipping_address(request):
    shipping_address = ShippingAddress.objects.filter(
        user=request.user, current_address=True).first()

    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=shipping_address)
        if form.is_valid():
            shipping_address = form.save(commit=False)
            shipping_address.user = request.user
            shipping_address.current_address = True
            shipping_address.save()

            messages.success(request, "Địa chỉ đã được lưu/cập nhật thành công!")

            form = ShippingAddressForm()
        else:
            form = ShippingAddressForm(request.POST, instance=shipping_address)
    else:
        form = ShippingAddressForm(instance=shipping_address)

    return render(request, 'accounts/shipping_address_form.html', {'form': form})


# Order history view
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'accounts/order_history.html', {'orders': orders})


# Order Details view
@login_required
def order_details(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    context = {
        'order': order,
        'order_items': order_items,
        'order_total_price': sum(item.get_total_price() for item in order_items),
        'coupon_discount': order.coupon.discount_amount if order.coupon else 0,
        'grand_total': order.get_order_total_price()
    }
    return render(request, 'accounts/order_details.html', context)


# Delete user account feature
@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Tài khoản của bạn đã được xóa thành công.")
        return redirect('index')


def register_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Kiểm tra nếu tên người dùng hoặc email đã tồn tại
        user_obj = User.objects.filter(username=username, email=email)
        if user_obj.exists():
            messages.info(request, 'Tên người dùng hoặc email đã tồn tại!')
            return HttpResponseRedirect(request.path_info)

        # Tạo người dùng mới
        user_obj = User.objects.create(
            username=username, first_name=first_name, last_name=last_name, email=email)
        user_obj.set_password(password)
        user_obj.save()

        # Đăng nhập ngay sau khi đăng ký
        user_obj = authenticate(username=username, password=password)
        if user_obj:
            login(request, user_obj)
            messages.success(request, 'Đã đăng ký thành công và đã đăng nhập!')

            # Chuyển hướng đến trang chủ hoặc trang tiếp theo
            next_url = request.GET.get('next', 'home')  # Mặc định đến 'index' nếu không có 'next'
            return redirect(next_url)

        messages.warning(request, 'Lỗi khi đăng nhập sau khi đăng ký.')
        return HttpResponseRedirect(request.path_info)

    return render(request, 'accounts/register.html')
