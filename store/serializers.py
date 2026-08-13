from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Product, Wishlist, Order, OrderItem, DrapeRecommendation
class UserSerializer(serializers.ModelSerializer):
    class Meta: model=User; fields=('id','username','email','first_name','last_name')
class ProductSerializer(serializers.ModelSerializer):
    class Meta: model=Product; fields='__all__'
class WishlistSerializer(serializers.ModelSerializer):
    product=ProductSerializer(read_only=True)
    class Meta: model=Wishlist; fields=('id','product')
class OrderItemSerializer(serializers.ModelSerializer):
    product=ProductSerializer(read_only=True)
    class Meta: model=OrderItem; fields=('product','quantity','price')
class OrderSerializer(serializers.ModelSerializer):
    items=OrderItemSerializer(many=True,read_only=True)
    class Meta: model=Order; fields=('id','status','total','shipping_address','created_at','items')
class RecommendationSerializer(serializers.ModelSerializer):
    recommendation=ProductSerializer(read_only=True)
    class Meta: model=DrapeRecommendation; fields='__all__'
