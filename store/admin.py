from django.contrib import admin
from .models import Product, Wishlist, Order, OrderItem, DrapeRecommendation

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'fabric', 'color', 'style', 'price', 'stock', 'featured')
    list_filter = ('fabric', 'style', 'featured')
    search_fields = ('name', 'color')
    prepopulated_fields = {'slug': ('name',)}

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email', 'id')
    inlines = [OrderItemInline]

admin.site.register(Wishlist)
admin.site.register(DrapeRecommendation)
