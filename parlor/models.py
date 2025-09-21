import random
import string
from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth.models import User, AbstractUser
from datetime import timedelta, date
from beauty_parlor.settings import AUTH_USER_MODEL as User
from django.core.validators import MaxValueValidator, MinValueValidator



class Request(models.Model):
    PLAN_CHOICES = [
        ('essential', 'Essential - KSh 1,500/month'),
        ('standard', 'standard - KSh 1,800/month'),
        ('premium', 'premium - KSh 2,500/month'),
    ]
    
    name = models.CharField(max_length=200)
    email = models.EmailField()
    business_name = models.CharField(max_length=200, blank=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='standard')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.name} - {self.get_plan_display()}"
    
    class Meta:
        ordering = ['-created_at']
        

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', ('Admin')
        CLIENT = 'CLIENT', ('client')
        STAFF = 'STAFF', ('staff')
    
    role = models.CharField(max_length=50, choices=Role.choices, default=Role.CLIENT)
    
    def _str_(self):
        return f"{self.username} ({self.role})"

class Subscriptions(models.Model):
    Subscription_type = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self): return self.Subscription_type
    


    
class Spa(models.Model):
    PAYMENT_STATUS = [("active", "Active"),("dormant","dormant"),("inactive", "Inactive")]
    LEVEL_STATUS = [("level 0", "Level 0"), ("level 1", "Level 1")]
    slug_name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(unique=True)
    spa_name = models.CharField(max_length=20)
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="spa")
    logo = models.ImageField(upload_to='spa_logos/' ,blank=True, null=True)  
    Subscription_status = models.ForeignKey(Subscriptions,on_delete=models.CASCADE)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='active')
    level = models.CharField(max_length=10, choices=LEVEL_STATUS, default='Level 0')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self): return self.slug_name
    
    def check_subscription_status(self):
        """Check and update subscription status automatically"""
        try:
            subscription = self.subscriptionstatus_set.latest('start_date')
            is_active = subscription.check_status()
            
            if is_active:
                self.payment_status = 'active'
            else:
                self.payment_status = 'dormant'
            self.save()
            
            return is_active
        except:
            self.payment_status = 'inactive'
            self.save()
            return False
    
    def process_payment(self, amount_paid, reference_code=None):
        """Process payment and update subscription"""
        try:
            # Get or create subscription
            try:
                subscription = self.subscriptionstatus_set.latest('start_date')
            except:
                subscription = SubscriptionStatus.objects.create(
                    spa=self,
                    start_date=timezone.now().date(),
                    End_date=timezone.now().date(),
                    Amount_paid=0,
                    reference_code=self._generate_reference_code(),
                    price=self.Subscription_status
                )
            
            # Process payment
            monthly_fee = float(self.Subscription_status.price)
            success = subscription.add_payment(amount_paid, monthly_fee)
            
            if success:
                # Create payment history
                PaymentHistory.objects.create(
                    spa=self,
                    amount=amount_paid,
                    reference_code=reference_code or self._generate_reference_code()
                )
                
                self.payment_status = 'active'
                self.save()
                
            return success
            
        except Exception as e:
            print(f"Payment error: {e}")
            return False
    
    def _generate_reference_code(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
class SubscriptionStatus(models.Model):
    spa = models.ForeignKey(Spa, on_delete=models.CASCADE)
    start_date = models.DateField(auto_now_add=True)
    End_date = models.DateField()
    Amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    reference_code = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    price = models.ForeignKey(Subscriptions,on_delete=models.CASCADE)
    
    def add_payment(self, amount_paid, monthly_fee=1800):
        """Extend subscription period based on payment"""
        try:
            months_paid = float(amount_paid) / float(monthly_fee)
            days_to_add = int(months_paid * 30)
            
            if days_to_add < 1:
                return False
            
            today = timezone.now().date()
            
            if self.End_date < today:
                self.start_date = today
                self.End_date = today + timedelta(days=days_to_add)
            else:
                self.End_date += timedelta(days=days_to_add)
            
            self.Amount_paid += amount_paid
            self.is_active = True
            self.save()
            
            return True
            
        except Exception as e:
            print(f"Add payment error: {e}")
            return False

    def check_status(self):
        """Deactivate if expired"""
        today = timezone.now().date()
        
        if self.End_date < today:
            self.is_active = False
            self.save()
        
        return self.is_active
    
    def days_remaining(self):
        """Calculate days remaining in subscription"""
        today = timezone.now().date()
        if self.End_date >= today:
            return (self.End_date - today).days
        return 0
    
    def __str__(self):
        return f"{self.spa.slug_name} - {self.End_date}"

class Theme(models.Model):
    spa = models.ForeignKey(Spa, on_delete=models.CASCADE, related_name='spa_theme')
    theme_code = models.CharField(max_length=7, default='red')

class Staff(models.Model):
    spa = models.ForeignKey(Spa, on_delete=models.CASCADE, related_name='staff_members')
    name = models.CharField(max_length=100)
    staff_id = models.CharField(max_length=40)
    specialization = models.CharField(max_length=100, blank=True)
    profile_pic = models.ImageField(upload_to='staff_profile/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.spa.spa_name}"
    


    
class SpaDashboard(models.Model):
    spa = models.ForeignKey(Spa, on_delete=models.CASCADE)
    venture_date = models.DateField()
    dashboard_img1 = models.ImageField(upload_to='dashboard_img1/',blank=False, null=False)
    dashboard_img2 = models.ImageField(upload_to='dashboard_img2/', blank=False, null=False)
    dashboard_img3 = models.ImageField(upload_to='dashboard_img3/', blank=False, null=False)
    dashboard_img4 = models.ImageField(upload_to='dashboard_img4/', blank=False, null=False)
    dashboard_img5 = models.ImageField(upload_to='dashboard_img5/', blank=False, null=False)
    dashboard_img6 = models.ImageField(upload_to='dashboard_img6/', blank=False, null=False)
    dashboard_img7 = models.ImageField(upload_to='dashboard_img7/',blank=False, null=False)
    dashboard_img8 = models.ImageField(upload_to='dashboard_img8/',blank=False, null=False)

class SpaHome_welcome(models.Model):
    spa = models.ForeignKey(Spa, on_delete=models.CASCADE)
    start_img = models.ImageField(upload_to='home_img/',blank=False, null=False)
    welcome_content = models.TextField()
    slogan = models.TextField(default='Your Oasis Of Relaxation')
    
class SpaHome_offer(models.Model):
    spa = models.ForeignKey(Spa, on_delete=models.CASCADE)
    offer_title = models.CharField(max_length=20)
    offer_message = models.TextField()
    offer_valid = models.DateField()
    
class ContactInfo(models.Model):
    spa = models.ForeignKey(Spa, on_delete=models.CASCADE, related_name="contact")
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    time = models.CharField(max_length=40)
    def __str__(self):
        return self.address
    
class spaNotification(models.Model):
    spa = models.ForeignKey(Spa, on_delete=models.CASCADE, related_name="notification")
    notification = models.TextField()
    
    
class OperatingHours(models.Model):
    status = [('open','open'),('closed','closed')]
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    spa = models.ForeignKey(Spa, on_delete=models.CASCADE, related_name='operating_hours')
    day = models.IntegerField(choices=DAYS_OF_WEEK)
    open_time = models.TimeField()
    close_time = models.TimeField()
    is_closed = models.BooleanField(default=False)
    current_status = models.CharField(max_length=20, choices=status, default='open')
    
    class Meta:
        ordering = ['day']
        unique_together = ['spa', 'day']
    
    def __str__(self):
        if self.is_closed:
            return f"{self.get_day_display()} - Closed"
        return f"{self.get_day_display()} - {self.open_time} to {self.close_time}"

class Service(models.Model):
    spa = models.ForeignKey(Spa, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    service_img = models.ImageField(upload_to='service_img/',blank=False, null=False)
    is_active = models.BooleanField(default=True)
    def __str__(self): return f"{self.name} - {self.spa.spa_name}"

class GalleryImage(models.Model):
    spa = models.ForeignKey(Spa, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(upload_to='gallery/',blank=False, null=False)
    caption = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Image for {self.spa.spa_name}"

class Booking(models.Model):
    BOOKING_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    spa = models.ForeignKey(Spa, on_delete=models.CASCADE, related_name='bookings')
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=15,blank=True)
    customer_address = models.TextField(blank=True)
    booking_date = models.DateField()
    booking_time = models.TimeField()
    services = models.ManyToManyField(Service)
    staff = models.ManyToManyField(Staff)
    notes = models.TextField(blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    clients = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    booking_reference = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.booking_reference} - {self.customer_name}"

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            # Generate booking reference
            last_booking = Booking.objects.filter(spa=self.spa).order_by('-id').first()
            if last_booking and last_booking.booking_reference:
                try:
                    last_num = int(last_booking.booking_reference.replace('#BK', ''))
                    new_num = last_num + 1
                except ValueError:
                    new_num = 1001
            else:
                new_num = 1001
            self.booking_reference = f"#BK{new_num}"
        super().save(*args, **kwargs)

class PaymentHistory(models.Model):
    spa = models.ForeignKey(Spa, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    reference_code = models.CharField(max_length=100, unique=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        transaction.on_commit(self._process_payment)
    def _process_payment(self):
        try:
            self.spa.process_payment(self.amount, self.reference_code)
        except Exception as e:
            pass
    
    def __str__(self): return f"Payment {self.reference_code} for {self.spa.spa_name}"

class Review(models.Model):
    spa = models.ForeignKey(Spa, on_delete=models.CASCADE, related_name='reviews')
    email = models.EmailField(blank=False)
    name = models.CharField(max_length=100)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    comment = models.TextField()
    is_approved = models.BooleanField(default=True)  # For moderation
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review by {self.name} for {self.spa.spa_name}"

class Reply(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='replies')
    email = models.EmailField()
    name = models.CharField(max_length=100)
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['created_at']
        verbose_name_plural = 'Replies'
    
    def __str__(self):
        return f"Reply by {self.name} to review #{self.review.id}"



#############################################################################################################3
#==============Shop models========================================

class Product(models.Model):
    spa = models.ForeignKey(Spa, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to='product_img/')
    stock = models.PositiveIntegerField(default=0)
    discount = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.spa.spa_name}"

class Order(models.Model):
    PAYMENT_METHODS = [
        ('mpesa', 'M-Pesa'),
        ('card', 'Credit Card'),
        ('cash', 'Cash on Delivery'),
    ]
    
    DELIVERY_OPTIONS = [
        ('delivery', 'Delivery'),
        ('pickup', 'Pick-up'),
    ]
    
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ]
    
    spa = models.ForeignKey('Spa', on_delete=models.CASCADE, related_name='orders')
    order_code = models.CharField(max_length=40, unique=True)
    client_name = models.CharField(max_length=255, null=True, blank=True)
    client_phone = models.CharField(max_length=15, null=True, blank=True)
    client_email = models.EmailField(null=True, blank=True)
    client_address = models.TextField(null=True, blank=True)
    preferred_date = models.DateField(default=timezone.now)
    preferred_time = models.TimeField(default=timezone.now)
    delivery_option = models.CharField(max_length=10, choices=DELIVERY_OPTIONS, default='pickup')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='mpesa')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    terms_accepted = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    
    def save(self, *args, **kwargs):
        if not self.order_code:
            # Generate unique order code
            self.order_code = 'ORD' + timezone.now().strftime('%Y%m%d') + ''.join(random.choices(string.digits, k=9))
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order #{self.order_code} - {self.client_name}"

class BookingItem(models.Model):
    spa = models.ForeignKey('Spa', on_delete=models.CASCADE, related_name='orderItem', default=1)
    booking = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name} - {self.booking.order_code}"

