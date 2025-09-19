# yourapp/serializers.py
from datetime import datetime
from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'role')


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta: model = Subscriptions; fields = "__all__"
    
class Home_welcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model= SpaHome_welcome
        fields = ["spa","start_img","welcome_content","slogan"]
        read_only_fields = fields
        
class Home_welcomeValidationSerializer(serializers.Serializer):
    exists = serializers.CharField(max_length=10, default='active')
    home = Home_welcomeSerializer(required=False)
    error = serializers.CharField(required= False)
    
    #############################
class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model= SpaHome_offer
        fields = ["id","offer_title","offer_message","offer_valid"]
        read_only_fields = fields
        
class OfferValidationSerializer(serializers.Serializer):
    exists = serializers.CharField(max_length=10, default='active')
    offer = OfferSerializer(required=False)
    error = serializers.CharField(required= False)
    
    #################################################
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model= spaNotification
        fields = ["id","notification"]
        read_only_fields = fields
        
class NotificationValidationSerializer(serializers.Serializer):
    exists = serializers.CharField(max_length=10, default='active')
    notification = NotificationSerializer(required=False)
    error = serializers.CharField(required= False)
    
class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model= ContactInfo
        fields = ["spa","address","phone","email","time"]
        read_only_fields = fields
        
class ContactValidationSerializer(serializers.Serializer):
    exists = serializers.CharField(max_length=10, default='active')
    contact = ContactSerializer(required=False)
    error = serializers.CharField(required= False)
###################################SERVICE AND GALLERY####################################
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id','spa','name','description','price',"service_img","is_active"]
    

class GalleryImageSerializer(serializers.ModelSerializer):
    class Meta: 
        model = GalleryImage
        fields = ["id","spa","image","caption","uploaded_at"]
        

###############################################################################
class ReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Reply
        fields = ['id', 'email', 'name', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']

class ReviewSerializer(serializers.ModelSerializer):
    replies = ReplySerializer(many=True, read_only=True)
    date = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = ['id', 'email', 'name', 'rating', 'comment', 'date', 'replies']
        read_only_fields = ['id', 'date', 'replies']
    
    def get_date(self, obj):
        return obj.created_at.strftime('%Y-%m-%d')
    
################################################################################

class OperatingHoursSerializer(serializers.ModelSerializer):
    day = serializers.CharField(source='get_day_display')
    
    class Meta:
        model = OperatingHours
        fields = ['day', 'open_time', 'close_time', 'is_closed']
        
class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ['id','spa','name','staff_id','specialization','profile_pic','is_active']

class BookingSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)
    staff_name = serializers.CharField(source='staff.name', read_only=True)
    
    class Meta:
        model = Booking
        fields = '__all__'

class BookingCreateSerializer(serializers.ModelSerializer):
    services = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    staff = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Booking
        exclude = ['booking_reference', 'status']
    
    def validate(self, data):
        # Check if date is not in the past
        if data['booking_date'] < timezone.now().date():
            raise serializers.ValidationError("Booking date cannot be in the past")
        
        # Check if the spa is open on the selected day
        day_of_week = data['booking_date'].weekday()
        operating_hours = OperatingHours.objects.filter(
            spa=data['spa'], 
            day=day_of_week
        ).first()
        
        if not operating_hours or operating_hours.is_closed:
            raise serializers.ValidationError("The spa is closed on the selected date")
        
        # Check if the booking time is within operating hours
        booking_time = data['booking_time']
        if operating_hours.open_time > booking_time or operating_hours.close_time < booking_time:
            raise serializers.ValidationError("The booking time is outside operating hours")
        
        # Check for booking conflicts
        booking_end_time = (datetime.combine(data['booking_date'], data['booking_time']) + 
                            timedelta(minutes=data['total_duration'])).time()
        
        conflicting_bookings = Booking.objects.filter(
            spa=data['spa'],
            booking_date=data['booking_date'],
            status__in=['pending', 'confirmed']
        ).exclude(id=self.instance.id if self.instance else None)
        
        for booking in conflicting_bookings:
            booking_end = (datetime.combine(booking.booking_date, booking.booking_time) + 
                            timedelta(minutes=booking.total_duration)).time()
            
            if (data['booking_time'] < booking_end and booking_end_time > booking.booking_time):
                if data.get('staff') and booking.staff and data['staff'] == booking.staff.id:
                    raise serializers.ValidationError("The selected staff is already booked at this time")
                elif not data.get('staff') and data['spa'].level == 0:
                    raise serializers.ValidationError("This time slot is already booked")
        
        return data
    
    def create(self, validated_data):
        services_data = validated_data.pop('services')
        staff_id = validated_data.pop('staff', None)
        
        booking = Booking.objects.create(**validated_data)
        
        # Add services
        booking.services.set(services_data)
        
        # Add staff if provided
        if staff_id:
            try:
                staff = Staff.objects.get(id=staff_id, spa=validated_data['spa'])
                booking.staff = staff
                booking.save()
            except Staff.DoesNotExist:
                pass
        
        return booking


#######################################################################3
class SpaSerializer(serializers.ModelSerializer):
    owner = UserSerializer()
    Subscription_status = SubscriptionSerializer()
    exists = serializers.CharField(max_length=10, default='active')

    class Meta:
        model = Spa
        fields = ["owner","spa_name","slug","payment_status","Subscription_status",'exists','logo']
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['exists'] = True
        return data
    
class ThemeSerializer(serializers.ModelSerializer):
    # spa = SpaSerializer()
    class Meta:
        model = Theme
        fields = ['spa','theme_code']

class DashboardSerializer(serializers.ModelSerializer):
    spa = SpaSerializer()
    
    class Meta:
        model= SpaDashboard
        fields = ["spa","venture_date","dashboard_img1","dashboard_img2","dashboard_img3","dashboard_img4","dashboard_img5","dashboard_img6","dashboard_img7","dashboard_img8"]
        read_only_fields = fields
        
class DashboardValidationSerializer(serializers.Serializer):
    exists = serializers.CharField(max_length=10, default='active')
    dashboard = DashboardSerializer(required=False)
    error = serializers.CharField(required= False)

##########################################################################################################
#=====================shop serializers======================
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image', 'stock', 'discount', 'is_active']

class BookingItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = BookingItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = BookingItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_code', 'client_name', 'client_phone', 'client_email',
            'client_address', 'preferred_date', 'preferred_time', 
            'delivery_option', 'payment_method', 'total_price', 'created_at',
            'terms_accepted', 'status', 'items'
        ]
        

class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.JSONField(write_only=True)
    
    class Meta:
        model = Order
        fields = [
            'client_name', 'client_phone', 'client_email', 'client_address',
            'preferred_date', 'preferred_time', 'delivery_option', 
            'payment_method', 'total_price', 'terms_accepted', 'items'
        ]
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        spa = self.context['spa']
        
        # Create order
        order = Order.objects.create(
            spa=spa,
            **validated_data
        )
        
        # Create booking items and update product stock
        for item_data in items_data:
            product_id = item_data.get('product_id')
            quantity = item_data.get('quantity')
            price = item_data.get('price')
            
            try:
                product = Product.objects.get(id=product_id, spa=spa)
                BookingItem.objects.create(
                    booking=order,
                    product=product,
                    quantity=quantity,
                    price=price
                )
                
                # Update product stock
                if product.stock >= quantity:
                    product.stock -= quantity
                    product.save()
                else:
                    # Handle insufficient stock
                    raise serializers.ValidationError(f"Insufficient stock for {product.name}")
                    
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Product with id {product_id} does not exist")
        
        return order