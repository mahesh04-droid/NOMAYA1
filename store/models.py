from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    FABRICS=[('linen','Linen'),('silk','Silk'),('cotton','Cotton'),('chiffon','Chiffon'),('traditional','Traditional')]
    STYLES=[('pre-stitched','Pre-stitched'),('classic','Classic'),('easy','Easy Drape')]
    name=models.CharField(max_length=180); slug=models.SlugField(unique=True); description=models.TextField(); price=models.DecimalField(max_digits=10,decimal_places=2)
    fabric=models.CharField(max_length=30,choices=FABRICS); color=models.CharField(max_length=40); style=models.CharField(max_length=30,choices=STYLES)
    image=models.URLField(default=""); secondary_image=models.URLField(blank=True, default=""); stock=models.PositiveIntegerField(default=0); featured=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name
    
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return round(sum(r.rating for r in reviews) / len(reviews), 1)
        return 0

    @property
    def review_count(self):
        return self.reviews.count()

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.PositiveIntegerField()
    active = models.BooleanField(default=True)
    def __str__(self): return self.code

class Wishlist(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='wishlist'); product=models.ForeignKey(Product,on_delete=models.CASCADE)
    class Meta: unique_together=('user','product')

class Order(models.Model):
    STATUS=[('placed','Placed'),('processing','Processing'),('shipped','Shipped'),('delivered','Delivered'),('cancelled','Cancelled')]
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='orders'); status=models.CharField(max_length=20,choices=STATUS,default='placed')
    total=models.DecimalField(max_digits=10,decimal_places=2); shipping_address=models.JSONField(default=dict); created_at=models.DateTimeField(auto_now_add=True)
    coupon=models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    discount=models.DecimalField(max_digits=10, decimal_places=2, default=0)

class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items'); product=models.ForeignKey(Product,on_delete=models.PROTECT); quantity=models.PositiveIntegerField(); price=models.DecimalField(max_digits=10,decimal_places=2)

class DrapeRecommendation(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True); mood=models.CharField(max_length=30); experience=models.IntegerField(); movement=models.IntegerField(); coverage=models.IntegerField(); climate=models.IntegerField(); fabric_weight=models.IntegerField(); recommendation=models.ForeignKey(Product,on_delete=models.SET_NULL,null=True); created_at=models.DateTimeField(auto_now_add=True)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

class OTPVerification(models.Model):
    identifier = models.CharField(max_length=255) # email or phone
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"OTP for {self.identifier}"

class InventoryLog(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    quantity_changed = models.IntegerField()
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name} ({self.quantity_changed}) - {self.reason}"
