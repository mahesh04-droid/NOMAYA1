from django.contrib import admin
from .models import Product, Wishlist, Order, OrderItem, DrapeRecommendation, InventoryLog, UGCPost

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'fabric', 'color', 'style', 'price', 'stock', 'featured')
    list_filter = ('fabric', 'style', 'featured', 'transparency', 'sheen', 'drape_ease')
    search_fields = ('name', 'color')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'price', 'stock', 'featured')
        }),
        ('Characteristics', {
            'fields': ('fabric', 'color', 'style')
        }),
        ('Sensory Metrics', {
            'fields': ('weight', 'transparency', 'sheen', 'drape_ease')
        }),
        ('Images', {
            'fields': ('image', 'secondary_image', 'flat_lay_image', 'video_url')
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Product.objects.get(pk=obj.pk)
            diff = obj.stock - old_obj.stock
            if diff != 0:
                super().save_model(request, obj, form, change)
                InventoryLog.objects.create(
                    product=obj,
                    user=request.user,
                    quantity_changed=diff,
                    reason="Manual admin update"
                )
                return
        elif obj.stock > 0:
            super().save_model(request, obj, form, change)
            InventoryLog.objects.create(
                product=obj,
                user=request.user,
                quantity_changed=obj.stock,
                reason="Initial stock setup"
            )
            return
        super().save_model(request, obj, form, change)

@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity_changed', 'reason', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__name', 'reason', 'user__username')
    readonly_fields = ('product', 'quantity_changed', 'reason', 'user', 'created_at')

    def has_add_permission(self, request):
        return False

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

@admin.register(UGCPost)
class UGCPostAdmin(admin.ModelAdmin):
    list_display = ('instagram_handle', 'product', 'approved', 'created_at')
    list_filter = ('approved', 'created_at')
    search_fields = ('instagram_handle', 'caption')
