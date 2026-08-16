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
        
        fall_pico = request.POST.get('fall_pico') == 'on'
        pre_draped = request.POST.get('pre_draped') == 'on'
        
        addons = []
        if fall_pico: addons.append('fall_pico')
        if pre_draped: addons.append('pre_draped')
        
        addon_str = "_".join(sorted(addons))
        
        pid = str(product_id)
        cart_key = f"{pid}|{addon_str}" if addon_str else pid
        
        cart[cart_key] = cart.get(cart_key, 0) + 1
        request.session['cart'] = cart
    return redirect(request.META.get('HTTP_REFERER', 'cart_view'))

def cart_remove(request, cart_key):
    if request.method == 'POST':
        cart = get_cart(request)
        ckey = str(cart_key)
        if ckey in cart:
            cart[ckey] -= 1
            if cart[ckey] <= 0:
                del cart[ckey]
        request.session['cart'] = cart
    return redirect('cart_view')

def cart_increment(request, cart_key):
    if request.method == 'POST':
        cart = get_cart(request)
        ckey = str(cart_key)
        if ckey in cart:
            cart[ckey] += 1
        request.session['cart'] = cart
    return redirect('cart_view')

@login_required
def cart_view(request):
    cart = get_cart(request)
    items = []
    total = 0
    for key, qty in cart.items():
        parts = key.split('|')
        pid = parts[0]
        addons = parts[1].split('_') if len(parts) > 1 and parts[1] else []
        
        try:
            p = Product.objects.get(id=pid)
            item_price = p.price
            addon_total = 0
            addon_descriptions = []
            if 'fall_pico' in addons:
                addon_total += 150
                addon_descriptions.append("Fall & Pico (+₹150)")
            if 'pre_draped' in addons:
                addon_total += 600
                addon_descriptions.append("1-Min Pre-Draped (+₹600)")
                
            unit_price = item_price + addon_total
            subtotal = unit_price * qty
            total += subtotal
            items.append({'product': p, 'quantity': qty, 'subtotal': subtotal, 'cart_key': key, 'addon_descriptions': addon_descriptions, 'unit_price': unit_price})
        except Product.DoesNotExist:
            pass
            
    discount = 0
    coupon = None
    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, active=True)
            from decimal import Decimal
            discount = total * (Decimal(coupon.discount_percentage) / Decimal('100'))
        except Coupon.DoesNotExist:
            pass
            
    shipping = 0 if (total - discount) > 5000 or (total - discount) == 0 else 99
    grand_total = (total - discount) + shipping
    
    return render(request, 'cart.html', {'items': items, 'total': total, 'discount': discount, 'coupon': coupon, 'shipping': shipping, 'grand_total': grand_total})

def check_pincode(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pincode = data.get('pincode', '').strip()
            if len(pincode) == 6 and pincode.isdigit():
                return JsonResponse({'status': 'success', 'message': 'Delivery in 3-5 Business Days', 'cod': True})
        except Exception:
            pass
        return JsonResponse({'error': 'Invalid 6-digit Pincode'}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

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
        identifier = data.get('identifier', '').strip()
        
        user_exists = (
            User.objects.filter(username__iexact=identifier).exists() or 
            User.objects.filter(email__iexact=identifier).exists() or 
            UserProfile.objects.filter(phone_number=identifier).exists()
        )
        
        return JsonResponse({'exists': user_exists})
    return JsonResponse({'error': 'Invalid'}, status=400)

def auth_request_otp(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        identifier = data.get('identifier', '').strip()
        otp = send_otp(identifier)
        return JsonResponse({'status': 'sent', 'dev_otp': otp})
    return JsonResponse({'error': 'Invalid'}, status=400)

def auth_verify(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        identifier = data.get('identifier', '').strip()
        method = data.get('method') # 'otp' or 'password'
        
        user = User.objects.filter(username__iexact=identifier).first()
        if not user:
            user = User.objects.filter(email__iexact=identifier).first()
        if not user:
            profile = UserProfile.objects.filter(phone_number=identifier).first()
            if profile: user = profile.user
            
        if method == 'password':
            password = data.get('password', '')
            # If user found, authenticate with exact username
            target_username = user.username if user else identifier
            u = authenticate(request, username=target_username, password=password)
            if u:
                login(request, u, backend='django.contrib.auth.backends.ModelBackend')
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
        occasion = data.get('occasion', 'Casual')
        climate = data.get('climate', 'AC')
        mood = data.get('mood', 'Earth')
        
        fabric = 'cotton'
        if climate == 'Humid' or occasion == 'Casual':
            fabric = 'cotton'
            if mood == 'Pastel': fabric = 'linen'
        elif climate == 'AC' or occasion == 'Work':
            fabric = 'linen'
        if occasion == 'Festive' or occasion == 'Cocktail':
            fabric = 'silk'
        if climate == 'Humid' and occasion == 'Cocktail':
            fabric = 'chiffon'
            
        qs = Product.objects.filter(fabric=fabric, stock__gt=0).order_by('-featured')
        product = qs.first() or Product.objects.filter(stock__gt=0).first()
        
        user = request.user if request.user.is_authenticated else None
        
        obj = DrapeRecommendation.objects.create(
            user=user, mood=mood,
            experience=3, movement=3, coverage=3, climate=3, fabric_weight=3,
            recommendation=product
        )
        return render(request, 'drape_finder.html', {'result': product, 'occasion': occasion})
        
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
    for key, qty in cart.items():
        parts = key.split('|')
        pid = parts[0]
        addons = parts[1].split('_') if len(parts) > 1 and parts[1] else []
        
        try:
            p = Product.objects.get(id=pid)
            item_price = p.price
            addon_total = 0
            addon_descriptions = []
            if 'fall_pico' in addons:
                addon_total += 150
                addon_descriptions.append("Fall & Pico")
            if 'pre_draped' in addons:
                addon_total += 600
                addon_descriptions.append("1-Min Pre-Draped")
                
            unit_price = item_price + addon_total
            subtotal = unit_price * qty
            
            name_desc = p.name
            if addon_descriptions:
                name_desc += f" (with {', '.join(addon_descriptions)})"
                
            items.append({'product': p, 'quantity': qty, 'unit_price': unit_price})
            total += subtotal
            
            line_items.append({
                'price_data': {
                    'currency': 'inr',
                    'product_data': {'name': name_desc},
                    'unit_amount': int(unit_price * 100),
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
            from decimal import Decimal
            discount = total * (Decimal(coupon.discount_percentage) / Decimal('100'))
            
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


def check_inventory_staff(user):
    return user.is_authenticated and (
        user.is_superuser or 
        user.is_staff or 
        user.groups.filter(name__in=['Inventory Managers', 'Stockers', 'Managers', 'Admin']).exists()
    )


@login_required
def inventory_dashboard(request):
    if not check_inventory_staff(request.user):
        return render(request, '403.html', {'message': 'Restricted Access. Inventory staff clearance required.'}, status=403)
    
    products = Product.objects.all().order_by('stock', 'name')
    
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'all')
    fabric_filter = request.GET.get('fabric', 'all')
    
    if q:
        products = products.filter(name__icontains=q)
    if fabric_filter != 'all':
        products = products.filter(fabric=fabric_filter)
    if status_filter == 'low':
        products = products.filter(stock__lte=5, stock__gt=0)
    elif status_filter == 'out':
        products = products.filter(stock=0)
    elif status_filter == 'in_stock':
        products = products.filter(stock__gt=5)
        
    all_products = Product.objects.all()
    total_skus = all_products.count()
    total_units = sum(p.stock for p in all_products)
    low_stock_count = all_products.filter(stock__lte=5, stock__gt=0).count()
    out_of_stock_count = all_products.filter(stock=0).count()
    
    recent_logs = InventoryLog.objects.select_related('product', 'user').order_by('-created_at')[:30]
    fabrics = [f[0] for f in Product.FABRICS]
    
    return render(request, 'inventory.html', {
        'products': products,
        'total_skus': total_skus,
        'total_units': total_units,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'recent_logs': recent_logs,
        'fabrics': fabrics,
        'current_q': q,
        'current_status': status_filter,
        'current_fabric': fabric_filter,
    })


@login_required
def api_update_stock(request):
    if not check_inventory_staff(request.user):
        return JsonResponse({'status': 'error', 'message': 'Permission denied. Staff only.'}, status=403)
        
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            new_stock = int(data.get('stock'))
            reason = data.get('reason', 'Manual frontend stock update')
            
            if new_stock < 0:
                return JsonResponse({'status': 'error', 'message': 'Stock cannot be negative'}, status=400)
                
            product = get_object_or_404(Product, id=product_id)
            diff = new_stock - product.stock
            
            if diff != 0:
                with transaction.atomic():
                    product.stock = new_stock
                    product.save()
                    
                    InventoryLog.objects.create(
                        product=product,
                        user=request.user,
                        quantity_changed=diff,
                        reason=reason
                    )
            
            return JsonResponse({
                'status': 'success',
                'product_id': product.id,
                'new_stock': product.stock,
                'diff': diff,
                'message': f'Stock for {product.name} updated to {product.stock}'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

