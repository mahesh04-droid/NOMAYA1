from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('collections/', views.collections, name='collections'),
    path('product/<slug:slug>/', views.detail, name='detail'),
    
    # Cart & Checkout
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/increment/<str:cart_key>/', views.cart_increment, name='cart_increment'),
    path('cart/remove/<str:cart_key>/', views.cart_remove, name='cart_remove'),
    path('cart/apply_coupon/', views.apply_coupon, name='apply_coupon'),
    
    # API
    path('api/pincode/', views.check_pincode, name='check_pincode'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/success/<int:order_id>/', views.checkout_success, name='checkout_success'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    
    # Auth
    path('auth/', views.auth_view, name='auth'),
    path('auth/check/', views.auth_check, name='auth_check'),
    path('auth/otp/', views.auth_request_otp, name='auth_request_otp'),
    path('auth/verify/', views.auth_verify, name='auth_verify'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('profile/', views.profile_view, name='profile'),
    path('orders/', views.orders_view, name='orders'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    
    # Studio & Finder
    path('drape-finder/', views.drape_finder, name='drape_finder'),
    path('draping-studio/', views.draping_studio, name='draping_studio'),
]
