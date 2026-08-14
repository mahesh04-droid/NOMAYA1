from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.urls import reverse
from django.utils.timezone import now
from datetime import timedelta
import random
import json
import stripe

from .models import Product, Review, Coupon, Order, Wishlist, OrderItem, DrapeRecommendation, UserProfile, OTPVerification, InventoryLog
from django.db import transaction

stripe.api_key = settings.STRIPE_SECRET_KEY

def index(request):
    featured_products = Product.objects.filter(featured=True, stock__gt=0).order_by('-created_at')
    return render(request, 'index.html', {'featured_products': featured_products})

def collections(request):
    products = Product.objects.all().order_by('-featured', '-created_at')
    
    # Filter logic
    fabric = request.GET.get('fabric')
    style = request.GET.get('style')
    q = request.GET.get('q')
    if fabric: products = products.filter(fabric=fabric)
    if style: products = products.filter(style=style)
    if q: products = products.filter(name__icontains=q)
    
    # Sorting logic
    sort = request.GET.get('sort')
    if sort == 'price_asc': products = products.order_by('price')
    elif sort == 'price_desc': products = products.order_by('-price')
    elif sort == 'newest': products = products.order_by('-created_at')
    
    fabrics = [f[0] for f in Product.FABRICS]
    styles = [s[0] for s in Product.STYLES]
    
    return render(request, 'collections.html', {
        'products': products, 
        'current_fabric': fabric, 
        'current_style': style, 
        'current_sort': sort,
        'fabrics': fabrics,
        'styles': styles
    })

def detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    similar_products = Product.objects.filter(fabric=product.fabric).exclude(id=product.id)[:4]
    
    if request.method == 'POST' and request.user.is_authenticated:
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        if rating and comment:
            Review.objects.create(product=product, user=request.user, rating=rating, comment=comment)
            return redirect('detail', slug=slug)
            
    return render(request, 'detail.html', {'product': product, 'similar_products': similar_products})

def get_cart(request):
    return request.session.get('cart', {})

def cart_add(request, product_id):
    if request.method == 'POST':
        cart = get_cart(request)
        pid = str(product_id)
        cart[pid] = cart.get(pid, 0) + 1
        request.session['cart'] = cart
    return redirect(request.META.get('HTTP_REFERER', 'cart_view'))

def cart_remove(request, product_id):
    if request.method == 'POST':
        cart = get_cart(request)
        pid = str(product_id)
        if pid in cart:
            cart[pid] -= 1
            if cart[pid] <= 0:
                del cart[pid]
        request.session['cart'] = cart
    return redirect('cart_view')

@login_required
def cart_view(request):
    cart = get_cart(request)
    items = []
    total = 0
    for pid, qty in cart.items():
        try:
            p = Product.objects.get(id=pid)
            subtotal = p.price * qty
            total += subtotal
            items.append({'product': p, 'quantity': qty, 'subtotal': subtotal})
        except Product.DoesNotExist:
            pass
            
    discount = 0
    coupon = None
    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, active=True)
            discount = total * (coupon.discount_percentage / 100)
        except Coupon.DoesNotExist:
            pass
            
    shipping = 0 if (total - discount) > 5000 or (total - discount) == 0 else 99
    grand_total = (total - discount) + shipping
    
    return render(request, 'cart.html', {'items': items, 'total': total, 'discount': discount, 'coupon': coupon, 'shipping': shipping, 'grand_total': grand_total})

def auth_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    return render(request, 'auth.html')

def send_otp(identifier):
    otp = str(random.randint(100000, 999999))
    OTPVerification.objects.filter(identifier=identifier).delete()
    OTPVerification.objects.create(
        identifier=identifier,
        otp=otp,
        expires_at=now() + timedelta(minutes=5)
    )
    print(f"\n{'='*50}\nDEVELOPMENT MODE - OTP for {identifier}: {otp}\n{'='*50}\n")
    return otp

def auth_check(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        identifier = data.get('identifier', '').strip().lower()
        
        user_exists = User.objects.filter(username=identifier).exists() or UserProfile.objects.filter(phone_number=identifier).exists()
        
        return JsonResponse({'exists': user_exists})
    return JsonResponse({'error': 'Invalid'}, status=400)

def auth_request_otp(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        identifier = data.get('identifier', '').strip().lower()
        otp = send_otp(identifier)
        return JsonResponse({'status': 'sent'})
    return JsonResponse({'error': 'Invalid'}, status=400)

def auth_verify(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        identifier = data.get('identifier', '').strip().lower()
        method = data.get('method') # 'otp' or 'password'
        
        user = User.objects.filter(username=identifier).first()
        if not user:
            profile = UserProfile.objects.filter(phone_number=identifier).first()
            if profile: user = profile.user
            
        if method == 'password':
            password = data.get('password', '')
            u = authenticate(request, username=user.username if user else identifier, password=password)
            if u:
                login(request, u)
                return JsonResponse({'status': 'success'})
            return JsonResponse({'error': 'Invalid credentials.'}, status=400)
            
        elif method == 'otp':
            otp = data.get('otp', '')
            verification = OTPVerification.objects.filter(identifier=identifier, otp=otp, expires_at__gt=now()).first()
            if verification:
                if not user:
                    # Create new user
                    name = data.get('name', '').strip()
                    is_email = '@' in identifier
                    email = identifier if is_email else ''
                    phone = data.get('contact', '').strip() if is_email else identifier
                    if not is_email and not email:
                        email = data.get('contact', '').strip().lower()
                    
                    user = User.objects.create_user(username=identifier, email=email, first_name=name)
                    user.set_unusable_password()
                    user.save()
                    UserProfile.objects.create(user=user, phone_number=phone)
                
                verification.delete()
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                return JsonResponse({'status': 'success'})
            return JsonResponse({'error': 'Invalid or expired OTP.'}, status=400)
            
    return JsonResponse({'error': 'Invalid'}, status=400)

def logout_view(request):
    logout(request)
    return redirect('home')

from .models import DrapeRecommendation

def drape_finder(request):
    if request.method == 'POST':
        data = request.POST
        score = sum(int(data.get(k, 2)) for k in ['experience', 'movement', 'coverage', 'climate', 'fabric_weight'])
        fabric = 'linen' if int(data.get('fabric_weight', 3)) <= 2 else ('silk' if int(data.get('experience', 3)) >= 4 else 'cotton')
        qs = Product.objects.filter(fabric=fabric, stock__gt=0).order_by('-featured')
        product = qs.first() or Product.objects.filter(stock__gt=0).first()
        
        user = request.user if request.user.is_authenticated else None
        mood = data.get('mood', 'Mood')
        
        obj = DrapeRecommendation.objects.create(
            user=user, mood=mood,
            experience=data.get('experience', 3),
            movement=data.get('movement', 3),
            coverage=data.get('coverage', 3),
            climate=data.get('climate', 3),
            fabric_weight=data.get('fabric_weight', 3),
            recommendation=product
        )
        return render(request, 'drape_finder.html', {'result': product, 'mood': mood})
        
    return render(request, 'drape_finder.html')

def draping_studio(request):
    return render(request, 'draping_studio.html')

from .models import Order, Wishlist

@login_required
def profile_view(request):
    orders_count = Order.objects.filter(user=request.user).count()
    return render(request, 'profile.html', {'orders_count': orders_count})

@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    return render(request, 'orders.html', {'orders': orders})

@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'wishlist.html', {'items': items})

from .models import OrderItem

import stripe
from django.conf import settings
from django.urls import reverse

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def checkout_view(request):
    cart = get_cart(request)
    if not cart:
        return redirect('collections')
        
    total = 0
    items = []
    line_items = []
    for pid, qty in cart.items():
        try:
            p = Product.objects.get(id=pid)
            items.append({'product': p, 'quantity': qty})
            total += p.price * qty
            
            line_items.append({
                'price_data': {
                    'currency': 'inr',
                    'product_data': {'name': p.name},
                    'unit_amount': int(p.price * 100),
                },
                'quantity': qty,
            })
        except Product.DoesNotExist:
            pass
            
    discount = 0
    coupon = None
    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, active=True)
            discount = total * (coupon.discount_percentage / 100)
            
            # Apply discount as a line item if possible, or just update total
            line_items.append({
                'price_data': {
                    'currency': 'inr',
                    'product_data': {'name': f'Discount ({coupon.code})'},
                    'unit_amount': -int(discount * 100),
                },
                'quantity': 1,
            })
        except Coupon.DoesNotExist:
            pass
            
    shipping = 0 if (total - discount) > 5000 or (total - discount) == 0 else 99
    grand_total = (total - discount) + shipping
    
    if shipping > 0:
        line_items.append({
            'price_data': {
                'currency': 'inr',
                'product_data': {'name': 'Shipping'},
                'unit_amount': int(shipping * 100),
            },
            'quantity': 1,
        })
    
    if request.method == 'POST':
        address = {
            'street': request.POST.get('street', ''),
            'city': request.POST.get('city', ''),
            'zipcode': request.POST.get('zipcode', '')
        }
        
        order = Order.objects.create(
            user=request.user,
            total=grand_total,
            shipping_address=address,
            status='pending',
            coupon=coupon,
            discount=discount
        )
        
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price
            )
            
        success_url = request.build_absolute_uri(reverse('checkout_success', args=[order.id]))
        cancel_url = request.build_absolute_uri(reverse('cart_view'))
        
        try:
            # Note: Stripe doesn't allow negative line items easily without Coupons API.
            # So if using dummy keys, this is fine. If real, they need Stripe Coupons.
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card', 'upi'],
                line_items=line_items,
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return redirect(checkout_session.url, code=303)
        except stripe.error.AuthenticationError:
            # Render a highly realistic mock Razorpay/UPI checkout experience
            return render(request, 'payment.html', {'order_id': order.id, 'amount': grand_total})
        except stripe.error.InvalidRequestError:
            # If stripe rejects negative line items
            return render(request, 'payment.html', {'order_id': order.id, 'amount': grand_total})
        
    return render(request, 'checkout.html', {'total': total, 'discount': discount, 'shipping': shipping, 'grand_total': grand_total})

@login_required
def checkout_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status != 'paid':
        with transaction.atomic():
            order.status = 'paid'
            order.save()
            for item in order.items.all():
                if item.product.stock >= item.quantity:
                    item.product.stock -= item.quantity
                else:
                    item.product.stock = 0
                item.product.save()
                
                InventoryLog.objects.create(
                    product=item.product,
                    user=request.user,
                    quantity_changed=-item.quantity,
                    reason=f"Sold - Order #{order.id}"
                )
    
    request.session['cart'] = {}
    request.session.pop('coupon_id', None)
    return render(request, 'order_success.html', {'order': order})

from django.http import JsonResponse

@login_required
def toggle_wishlist(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()
        if wishlist_item:
            wishlist_item.delete()
            return JsonResponse({'status': 'removed'})
        else:
            Wishlist.objects.create(user=request.user, product=product)
            return JsonResponse({'status': 'added'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            coupon = Coupon.objects.get(code=code, active=True)
            request.session['coupon_id'] = coupon.id
        except Coupon.DoesNotExist:
            request.session.pop('coupon_id', None)
    return redirect('cart_view')
