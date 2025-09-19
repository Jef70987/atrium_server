from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import*
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'business_name', 'plan', 'created_at')
    list_filter = ('plan', 'created_at')
    search_fields = ('name', 'email', 'business_name')
    readonly_fields = ('created_at',)

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role', {'fields': ('role',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)

User = get_user_model()

class CustomAdminAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        # always allow superuser
        if user.is_superuser:
            return
        # block if any payment status for this user is dormant or inactive
        if Spa.objects.filter(owner=user, payment_status__in=["dormant", "inactive"]).exists():
            raise ValidationError("Your Spa account is dormant or inactive. Renew subscription or Contact support.",code="inactive")
        # Respect normal is_active flag
        if not user.is_active:
            raise ValidationError("This account is inactive. ", code="inactive")
admin.site.login_form = CustomAdminAuthenticationForm
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'role')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(Subscriptions)
class SubscriptionsAdmin(admin.ModelAdmin):
    list_display = ("Subscription_type","price","duration_days","created_at")
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display =('spa' ,'theme_code')
    search_fields = ('id','spa')
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
@admin.register(Spa)
class SpaAdmin(admin.ModelAdmin):
    list_display = ("spa_name","slug","Subscription_status","owner","payment_status","created_at","check_subscription")
    search_fields = ("spa_name","slug","owner__username")
    prepopulated_fields = {"slug": ("slug_name",)}
    list_editable = ("Subscription_status","payment_status")
    
    def check_subscription(self, obj):
        return obj.check_subscription_status()
    check_subscription.short_description = 'Subscription Active'
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(owner=request.user)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("spa","name","staff_id","specialization","profile_pic","is_active","created_at","updated_at")
    search_fields = ("name","staff_id")
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(SubscriptionStatus)
class SubscriptionStatusAdmin(admin.ModelAdmin):
    list_display = ("spa","start_date","End_date","price","Amount_paid","reference_code","is_active","days_remaining")
    search_fields = ("reference_code","Amount_paid")
    list_editable = ("reference_code","Amount_paid")
    readonly_fields = ['days_remaining']
    
    def days_remaining(self, obj):
        return obj.days_remaining()
    days_remaining.short_description = 'Days Left'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
@admin.register(SpaDashboard)
class SpaDashboardAdmin(admin.ModelAdmin):
    list_display = ("spa","venture_date","dashboard_img1","dashboard_img2",
                    "dashboard_img3","dashboard_img4","dashboard_img5",
                    "dashboard_img6","dashboard_img7","dashboard_img8")
    
    list_editable = ("venture_date","dashboard_img1","dashboard_img2",
                    "dashboard_img3","dashboard_img4","dashboard_img5",
                    "dashboard_img6","dashboard_img7","dashboard_img8")

@admin.register(SpaHome_welcome)
class SpaHome_welcomeAdmin(admin.ModelAdmin):
    list_display = ("spa","start_img","welcome_content","slogan")
    list_editable = ("start_img","welcome_content","slogan")
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
@admin.register(SpaHome_offer)
class SpaHome_offerAdmin(admin.ModelAdmin):
    list_display = ("spa","offer_title","offer_message","offer_valid")
    list_editable = ("offer_title","offer_message","offer_valid")
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ("spa","address","phone","email","time")
    list_editable = ("address","phone","email","time")
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
@admin.register(OperatingHours)
class OperatingHoursAdmin(admin.ModelAdmin):
    list_display = ('day','open_time','close_time','is_closed','current_status')
    list_editable =('open_time','close_time','is_closed','current_status')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    

@admin.register(spaNotification)
class notificationAdmin(admin.ModelAdmin):
    list_display=('notification',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name","spa","price")
    search_fields = ("name","spa__name")
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("spa","caption","uploaded_at")
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("spa","booking_reference","customer_name","customer_email","booking_date","booking_time","status","created_at")
    list_filter = ("status","customer_email")
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "services" and not request.user.is_superuser:
            kwargs["queryset"] = Service.objects.filter(spa__owner = request.user)
        if db_field.name == "staff" and not request.user.is_superuser:
            kwargs["queryset"] = Staff.objects.filter(spa__owner = request.user)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ("spa","amount","reference_code","payment_date")
    readonly_fields = ['payment_date']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['name', 'spa', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating', 'spa', 'created_at']
    search_fields = ['name', 'email', 'comment']
    actions = ['approve_reviews']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"

@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ['name', 'review', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'email', 'comment']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(review__spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "review" and not request.user.is_superuser:
            kwargs["queryset"] = Review.objects.filter(spa__owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'spa', 'price', 'stock', 'discount', 'is_active')
    list_filter = ('spa', 'is_active')
    search_fields = ('name', 'spa__name')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'spa', 'client_name', 'total_price', 'created_at')
    list_filter = ('spa', 'delivery_option', 'payment_method')
    search_fields = ('customer_name', 'customer_phone')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(BookingItem)
class BookingItemAdmin(admin.ModelAdmin):
    list_display = ('booking', 'quantity', 'price')
    list_filter = ('product__spa',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs 
        #only show spa owned by this user
        return qs.filter(spa__owner=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "spa" and not request.user.is_superuser:
            kwargs["queryset"] = Spa.objects.filter(owner = request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
