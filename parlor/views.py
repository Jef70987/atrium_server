from abc import get_cache_token
from multiprocessing import AuthenticationError
import random
import string
from rest_framework import generics, status,permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from rest_framework.decorators import api_view
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required,user_passes_test
from rest_framework.authtoken.models import Token
from django.db.models import Sum, Count, Q
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta,time
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator

from django.core.mail import send_mass_mail



###########################--REQUESTS------######################################################
@api_view(['POST'])
def submit_request(request):
    try:
        data = request.data
        
        # Create new request
        request_obj = Request.objects.create(
            name=data.get('name', ''),
            email=data.get('email', ''),
            business_name=data.get('business', ''),
            plan=data.get('plan', 'premium').split(' - ')[0].lower(),
            message=data.get('message', '')
        )
        
        return Response({
            'success': True,
            'message': 'Request submitted successfully!'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=400)
#################################LOGIN############################################################
@api_view(['GET','POST'])
@permission_classes([AllowAny])
def multi_tenant_login(request):
    """
    Multi-tenant login that requires spa slug and user credentials
    Expected POST data: {username, password, spa_slug}
    """
    username = request.data.get('username')
    password = request.data.get('password')
    spa_slug = request.data.get('spa_slug')
    
    if not username or not password or not spa_slug:
        return Response(
            {'error': 'Username, password, and spa slug are required'},
            status=400
        )
    
    # Verify the spa exists
    try:
        spa = Spa.objects.get(slug=spa_slug)
    except Spa.DoesNotExist:
        return Response(
            {'error': 'Spa not found'},
            status=404
        )
    
    # Authenticate user
    user = authenticate(username=username, password=password)
    
    #Authenticate spa
    Spa_owner = spa.owner.username
    
    
    if Spa_owner:
        if user is not None:
            # Check if user belongs to this spa
            if not Spa_owner == username:
                return Response(
                    {'error': 'User does not have access to this site'},
                    status=403
                )
            
            # Create JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Add custom claims to the token
            refresh['spa_slug'] = spa_slug
            refresh['user_role'] = user.role
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'username': user.username,
                    'role': user.role,
                    'spa_slug': spa_slug
                }
            })
        else:
            return Response(
                {'error': 'Invalid credentials'},
                status=401
            )

@api_view(['POST'])
@permission_classes([AllowAny])
def multi_tenant_token_refresh(request):
    """
    Token refresh for multi-tenant system
    """
    from rest_framework_simplejwt.tokens import RefreshToken
    
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({'error': 'Refresh token is required'}, status=400)
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        
        # Return the same spa_slug and user role in the response
        return Response({
            'access': access_token,
            'spa_slug': refresh.get('spa_slug', ''),
            'user_role': refresh.get('user_role', 'client')
        })
    except Exception as e:
        return Response({'error': 'Invalid refresh token'}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get user profile with spa context
    """
    # Get spa slug from query parameter or token
    spa_slug = request.GET.get('spa_slug') or request.auth.get('spa_slug', '')
    
    if not spa_slug:
        return Response({'error': 'Spa slug is required'}, status=400)
    
    try:
        spa = Spa.objects.get(slug=spa_slug)
        
        # Check if user has access to this spa
        if not request.user.spas.filter(id=spa.id).exists():
            return Response(
                {'error': 'User does not have access to this spa'},
                status=403
            )
        
        return Response({
            'username': request.user.username,
            'email': request.user.email,
            'role': request.user.role,
            'spa_slug': spa_slug,
            'spa_name': spa.name,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        })
    except Spa.DoesNotExist:
        return Response({'error': 'Spa not found'}, status=404)
######################################################################################################################

class ValidateSpaView(APIView):
    """ validate if a spa exists and is active"""
    def get(self, request, slug):
        try:
            #try to get the spa by slug
            spa = get_object_or_404(Spa, slug = slug)
            
            #spa is valid and active
            serializer_class = SpaSerializer(spa)
            return Response(serializer_class.data)
        except Spa.DoesNotExist:
            return Response(
                {'valid': False,'error':'spa not found'},
                status=status.HTTP_200_OK
            )
class DashboardView(APIView):
    """
    Get Dashboard Data
    """
    def get(self, request, slug):
        try:
            spa = Spa.objects.get(slug = slug)
        except Spa.DoesNotExist:
            return Response(
                {'valid': False,'error':'spa not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            dashboard = SpaDashboard.objects.get(spa=spa)
            serializer = DashboardSerializer(dashboard)
            return Response(serializer.data)
        except SpaDashboard.DoesNotExist:
            return Response(
                
                {'valid': False,'error':'spa not found'},
                status=status.HTTP_200_OK
            )
class HomeAPIView(APIView):
    """
    Get home welcome message and the startpic
    """
    def get(self, request, slug):
        try:
            spa = Spa.objects.get(slug = slug)
        except Spa.DoesNotExist:
            return Response(
                {'valid': False,'error':'spa not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            home = SpaHome_welcome.objects.get(spa=spa)
            serializer = Home_welcomeSerializer(home)
            return Response(serializer.data)
        except SpaHome_welcome.DoesNotExist:
            return Response(
                
                {'valid': False,'error':'spa not found'},
                status=status.HTTP_200_OK
            )
            
class ContactAPIView(APIView):
    """
    Get contact details
    """
    def get(self, request, slug):
        try:
            spa = Spa.objects.get(slug = slug)
        except Spa.DoesNotExist:
            return Response(
                {'valid': False,'error':'spa not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            contact = ContactInfo.objects.get(spa = spa)
            serializer = ContactSerializer(contact)
            return Response(serializer.data)
        except ContactInfo.DoesNotExist:
            return Response(
                
                {'valid': False ,'error':'spa not found'},
                status=status.HTTP_200_OK
            )
class OffersAPIView(APIView):
    """
    Get home welcome message and the startpic
    """
    def get(self, request, slug):
        try:
            spa = Spa.objects.get(slug = slug)
        except Spa.DoesNotExist:
            return Response(
                {'valid': False,'error':'spa not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            offer = SpaHome_offer.objects.get(spa=spa)
            serializer = OfferSerializer(offer)
            return Response(serializer.data)
        except SpaHome_offer.DoesNotExist:
            return Response(
                
                {'valid': False,'error':'spa not found'},
                status=status.HTTP_200_OK
            )
            
class NotificationsAPIView(APIView):
    """
    Get home notification
    """
    def get(self, request, slug):
        try:
            spa = Spa.objects.get(slug = slug)
        except Spa.DoesNotExist:
            return Response(
                {'valid': False,'error':'spa not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            notification = spaNotification.objects.filter(spa=spa)
            serializer = NotificationSerializer(notification, many=True)
            return Response(serializer.data)
        except spaNotification.DoesNotExist:
            return Response(
                
                {'valid': False,'error':'spa not found'},
                status=status.HTTP_200_OK
            )
class SpaDetailView(generics.RetrieveAPIView):
    queryset = Spa.objects.all()
    serializer_class = SpaSerializer
    lookup_field = "slug"
    

######################################-----SERVICE AND GALLERY-----------#############################
@api_view(['GET'])
def get_services(request, slug):
    try:
        spa = Spa.objects.get(slug=slug)
        
        service = Service.objects.filter(spa=spa)
        serializer = ServiceSerializer(service, many=True)
        return Response(serializer.data)
    
    except Spa.DoesNotExist:
        return Response({"error": "Spa not found"}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['GET'])
def get_gallery(request, slug):
    try:
        spa = Spa.objects.get(slug=slug)
        
        # Check subscription
        if not spa.payment_status:
                return Response({"error": "No data available at this time"}, status=status.HTTP_403_FORBIDDEN)
        
        gallery = GalleryImage.objects.filter(spa=spa)
        serializer = GalleryImageSerializer(gallery, many=True)
        return Response(serializer.data)
    
    except Spa.DoesNotExist:
        return Response({"error": "Spa not found"}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST','GET'])
# @permission_classes([IsAuthenticated])
def add_service(request, slug):
    """Add a new service to a spa"""
    spa = get_object_or_404(Spa, slug=slug)
    
    service = Service.objects.create(
        spa = spa,
        name=request.data.get('name'),
        description = request.data.get('description'),
        price=request.data.get('price'),
        service_img = request.data.get('service_img'),
        is_active=request.data.get('is_active')
    )
    
    return Response({
        'id':service.id,
        'name':service.name,
        'description':service.description,
        'price':service.price,
        'service_img':service.service_img,
        'is_active':service.is_active
    },status=status.HTTP_201_CREATED)

@api_view(['POST','GET'])
# @permission_classes([IsAuthenticated])
def add_gallery_image(request, slug):
    """Add a new image to spa gallery"""
    spa = get_object_or_404(Spa, slug=slug)
    data = request.data
    
    gallery = GalleryImage.objects.create(
        spa = spa,
        image=request.data.get('image'),
        caption = request.data.get('caption'),
    )
    return Response({
        'id':gallery.id,
        'image':gallery.image,
        'caption':gallery.caption,
    },status=status.HTTP_201_CREATED)
    
########################ADMIN BOOKING VIEW##################################################################################################
class BookingListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    
    def get_queryset(self):
        slug = self.kwargs['slug']
        return Booking.objects.filter(spa__slug=slug).order_by('-created_at')

class BookingDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = BookingSerializer
    queryset = Booking.objects.all()
    
    def get_object(self):
        slug = self.kwargs['slug']
        booking_id = self.kwargs['pk']
        return get_object_or_404(Booking, id=booking_id, spa__slug=slug)
    
########################CLIENT BOOKINGS VIEW#######################################################################################################3##
class ClientBookingsVerifyView(APIView):
    
    def post(self, request, slug):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if email exists in bookings
        has_bookings = Booking.objects.filter(
            spa__slug=slug, 
            customer_email=email
        ).exists()
        
        if not has_bookings:
            return Response({'error': 'No bookings found for this email'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({'success': True}, status=status.HTTP_200_OK)

class ClientBookingsListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    
    def get_queryset(self):
        slug = self.kwargs['slug']
        email = self.request.GET.get('email')
        if not email:
            return Booking.objects.none()
        
        return Booking.objects.filter(
            spa__slug=slug, 
            customer_email=email
        ).order_by('-created_at')
    
##########################BOOKING#############################################################################################################

@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCSRFToken(APIView):
    def get(self, request):
        return JsonResponse({'csrfToken': get_cache_token()})
class SpaMixin:
    def get_spa(self):
        slug = self.kwargs.get('slug')
        return get_object_or_404(Spa, slug=slug)

class TenantServicesView(generics.ListAPIView):
    serializer_class = ServiceSerializer
    
    def get_queryset(self):
        slug = self.kwargs['slug']
        return Service.objects.filter(spa__slug=slug, is_active=True)

class TenantOperatingHoursView(generics.ListAPIView):
    serializer_class = OperatingHoursSerializer
    
    def get_queryset(self):
        slug = self.kwargs['slug']
        return OperatingHours.objects.filter(spa__slug=slug)
    
class StaffListView(SpaMixin, generics.ListAPIView):
    serializer_class = StaffSerializer
    
    def get_queryset(self):
        spa = self.get_spa()
        return Staff.objects.filter(spa=spa, is_active=True)
    
class AvailableSlotsView(APIView):
    def get(self, request, slug):
        date_str = request.GET.get('date')
        
        if not date_str:
            return Response({'error': 'Date parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the spa object to check its level
        try:
            spa = Spa.objects.get(slug=slug)
        except Spa.DoesNotExist:
            return Response({'error': 'Spa not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get day of week (0=Monday, 6=Sunday)
        day_of_week = date.weekday()
        
        try:
            operating_hours = OperatingHours.objects.get(spa__slug=slug, day=day_of_week)
        except OperatingHours.DoesNotExist:
            return Response({'available_slots': []})
        
        if operating_hours.is_closed:
            return Response({'available_slots': []})
        
        # Get existing bookings for this date
        existing_bookings = Booking.objects.filter(
            spa__slug=slug,
            booking_date=date,
            status__in=['pending', 'confirmed']  # Only count active bookings
        )
        
        
        # Generate all possible time slots
        time_slots = []
        current_time = operating_hours.open_time
        close_time = operating_hours.close_time
        
        # Create time slots in 30-minute intervals
        current_dt = datetime.combine(date, current_time)
        close_dt = datetime.combine(date, close_time)
        
        while current_dt < close_dt:
            time_slots.append(current_dt.time().strftime('%H:%M'))
            current_dt += timedelta(minutes=90)
        
        
        # Filter out booked slots based on spa level
        available_slots = []
        for slot in time_slots:
            slot_time = datetime.strptime(slot, '%H:%M').time()
            slot_end = (datetime.combine(date, slot_time) + timedelta(minutes=90)).time()
            
            is_available = True
            
            for booking in existing_bookings:
                booking_time = booking.booking_time
                booking_end = (datetime.combine(date, booking_time) + timedelta(minutes=90)).time()
                
                
                # Check for time overlap - FIXED LOGIC
                if not (slot_end <= booking_time or slot_time >= booking_end):
                    # There is an overlap
                    if spa.level == 0:
                        # Level 0: Any overlap makes slot unavailable
                        is_available = False
                        break
                    elif spa.level == 1:
                        # Level 1: Only block if specific staff is requested and booked
                        requested_staff_id = request.GET.get('staff')
                        if requested_staff_id:
                            try:
                                if booking.staff and booking.staff.id == int(requested_staff_id):
                                    is_available = False
                                    break
                            except (ValueError, TypeError):
                                # Invalid staff ID, ignore and continue
                                pass
            
            if is_available:
                available_slots.append(slot)
        
        return Response({'available_slots': available_slots})
    
class AvailableStaffView(APIView):
    def get(self, request, slug):
        spa = Spa.objects.get(slug=slug)
        date_str = request.GET.get('date')
        time_str = request.GET.get('time')
        
        if not date_str or not time_str:
            return Response({'error': 'Date and time parameters are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            booking_time = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            return Response({'error': 'Invalid date or time format'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all active staff
        all_staff = Staff.objects.filter(spa=spa, is_active=True)
        
        available_staff = []
        
        # Check each staff member's availability
        for staff in all_staff:
            
            # Check for existing bookings for this staff member
            conflicting_bookings = Booking.objects.filter(
                spa=spa,
                staff=staff,
                booking_date=booking_date,
                booking_time=booking_time,
                status__in=['pending', 'confirmed']
            )
            
            
            if not conflicting_bookings.exists():
                available_staff.append(staff.staff_id)
            
        return Response({'available_staff': available_staff})

class BookingCreateView(APIView):
    def post(self, request, slug):
        try:
            
            # 1. Get the spa
            spa = get_object_or_404(Spa, slug=slug)
            
            # 2. Extract data from request
            data = request.data
            
            
            # staff_id = data.get('staff')
            # booked_staff = Staff.objects.get(staff_id=staff_id, spa=spa)
            
            def generate_unique_reference():
                while True:
                    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 6))
                    reference = f"#BK{random_chars}"
                    if not Booking.objects.filter(booking_reference=reference).exists():
                        return reference
                    
            booking_reference = generate_unique_reference()
            
            # 3. Create the booking
            booking = Booking.objects.create(
                spa=spa,
                customer_name=data.get('client_name', ''),
                customer_email=data.get('client_email', ''),
                customer_phone=data.get('client_phone', ''),
                customer_address=data.get('client_address', ''),
                booking_date=data.get('booking_date'),
                booking_time=data.get('booking_time'),
                notes=data.get('notes', ''),
                total_price=data.get('total_price', 0),
                clients=data.get('clients', 1),
                status='pending',
                booking_reference = booking_reference
            )
            
            # 4. Add services
            service_ids = data.get('services', [])
            
            services = Service.objects.filter(id__in=service_ids, spa=spa)
            booking.services.set(services)
            
            staff_id = data.get('staff',[])
            booked_staff = Staff.objects.filter(staff_id=staff_id, spa=spa)
            booking.staff.set(booked_staff)
            
            # 7. Return success response
            return Response({
                'success': True,
                'message': 'Booking created successfully',
                'booking_reference': booking_reference,
                'booking_id': booking.id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
            
class BookingServicesView(APIView):
    def get(self, request, slug):
        reference = request.GET.get('reference')
        
        if not reference:
            return Response({'error': 'Booking reference required'}, status=400)
        
        booking_reference = f"#{reference}"
        try:
            booking = Booking.objects.select_related('spa').prefetch_related('services').get(
                spa__slug=slug,
                booking_reference= booking_reference
            )
            
            # Return ONLY client name and services (no other booking details)
            booking_data = {
                'booking_reference': booking.booking_reference,
                'client_name': booking.customer_name,
                'services': [
                    {
                        'id': service.id,
                        'name': service.name,
                        'price': float(service.price)
                    }
                    for service in booking.services.all()
                ],
                'total_price': float(booking.total_price)
            }
            
            return Response(booking_data)
            
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=404)
        
        
#################################################----client REVIEWS----------###################################################################
@api_view(['GET'])
@permission_classes([AllowAny])
def get_reviews(request, slug):
    try:
        # Get only approved reviews for this spa
        reviews = Review.objects.filter(
            spa__slug=slug, 
            is_approved=True
        ).prefetch_related('replies').order_by('-created_at')
        
        # Serialize the data
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_review(request, slug):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        # Check if client has made a booking
        has_booking = Booking.objects.filter(
            spa__slug=slug, 
            customer_email=email, 
            status__in=['confirmed', 'completed']
        ).exists()
        
        if not has_booking:
            return Response({'error': 'Only clients with confirmed bookings can submit reviews'}, status=403)
        
        # Get the spa instance
        spa = Spa.objects.get(slug=slug)
        
        # Create the review
        review = Review.objects.create(
            spa=spa,
            email=email,
            name=data.get('name', 'Anonymous'),
            rating=data.get('rating', 5),
            comment=data.get('comment', ''),
            is_approved=True  # Requires admin approval
        )
        
        return Response({
            'message': 'Review submitted for approval', 
            'id': review.id
        })
    except Spa.DoesNotExist:
        return Response({'error': 'Spa not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST','GET'])
@permission_classes([AllowAny])
def submit_reply(request, slug, review_id):
    try:
        data = json.loads(request.body)
        
        # Get the review
        review = Review.objects.get(id=review_id, spa__slug=slug)
        
        # Create the reply
        reply = Reply.objects.create(
            review=review,
            email=data.get('email'),
            name=data.get('name'),
            comment="welcome"
            
        )
        
        return Response({
            'message': 'Reply posted', 
            'id': reply.id
        })
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET','POST'])
@permission_classes([AllowAny])
def verify_client(request, slug):
    
    try:
        email=request.data.get('email')
        # email = "japhethmasinde@gmail.com"
        has_booking = Booking.objects.filter(
            spa__slug=slug, 
            customer_email = email,
            # status__in=['confirmed', 'completed']
        ).exists()
        
        client_name = None
        if has_booking:
            booking = Booking.objects.filter(
                spa__slug = slug,
                customer_email=email
            ).first()
            client_name = booking.customer_name if booking else "verified client"
        
        
        return Response({
            'is_verified': has_booking,
            'name': client_name
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)
#################################################----ADMIN REVIEWS----------###################################################################
def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@api_view(['GET','POST'])
# @permission_classes([IsAuthenticated])
# @user_passes_test(is_admin)
def admin_get_reviews(request, slug):
    try:
        # Get all reviews (including unapproved) for this spa
        reviews = Review.objects.filter(
            spa__slug=slug
        ).prefetch_related('replies').order_by('-created_at')
        
        # Serialize the data
        reviews_data = []
        for review in reviews:
            review_data = {
                'id': review.id,
                'email': review.email,
                'name': review.name,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.isoformat(),
                'is_approved': review.is_approved,
                'replies': []
            }
            
            for reply in review.replies.all():
                review_data['replies'].append({
                    'id': reply.id,
                    'email': reply.email,
                    'name': reply.name,
                    'comment': reply.comment,
                    'created_at': reply.created_at.isoformat()
                })
            
            reviews_data.append(review_data)
        
        return Response(reviews_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST','GET'])
# @permission_classes([IsAuthenticated])
# @user_passes_test(is_admin)
def admin_submit_reply(request, slug, review_id):
    try:
        data = json.loads(request.body)
        #try to get the spa by slug
        spa = get_object_or_404(Spa, slug = slug)
        # Get the review
        review = Review.objects.get(id=review_id, spa__slug=slug)
        
        # Create the reply as admin
        reply = Reply.objects.create(
            review=review,
            email="notapplicable@gmail.com",
            name= spa or "Parlor Admin",
            comment=data.get('comment')
        )
        
        return Response({
            'message': 'Reply posted successfully', 
            'id': reply.id
        })
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST','GET'])
# @permission_classes([IsAuthenticated])
# @user_passes_test(is_admin)
def admin_approve_review(request, slug, review_id):
    try:
        review = Review.objects.get(id=review_id, spa__slug=slug)
        review.is_approved = True
        review.save()
        
        return Response({'message': 'Review approved successfully'})
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['DELETE'])
# @permission_classes([IsAuthenticated])
# @user_passes_test(is_admin)
def admin_delete_review(request, slug, review_id):
    try:
        review = Review.objects.get(id=review_id, spa__slug=slug)
        review.delete()
        
        return Response({'message': 'Review deleted successfully'})
    except Review.DoesNotExist:
        return Response({'error': 'Review not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    
############################################E-commerce#############################################################

@api_view(['GET'])
def validate_shop(request, slug):
    try:
        spa = Spa.objects.get(slug=slug)
        serializer = SpaSerializer(spa)
        return Response(serializer.data)
    except Spa.DoesNotExist:
        return Response(
            {'error': 'Shop not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
        
@api_view(['GET'])
def spa_theme(request, slug):
    try:
        spa = Spa.objects.get(slug=slug)
        
        theme = Theme.objects.get(spa=spa)
        serializer = ThemeSerializer(theme)
        return Response(serializer.data)
    
    except Spa.DoesNotExist:
        return Response({"error": "Spa not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def shop_products(request, slug):
    try:
        spa = Spa.objects.get(slug=slug)
        products = Product.objects.filter(spa=spa, is_active=True)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    except Spa.DoesNotExist:
        return Response(
            {'error': 'Shop not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
        
# def send_orderCode_email(spa,order):
#     """Send email using SMTP"""
#     try:
#         message = (f"""
#             {spa.spa_name} stores
#             ----------------------------------------------------
#             ORDER -CODE #{order.order_code}
#             ----------------------------------------------------
#             CLIENT: {order.client_name}
#             PHONE: {order.client_phone}
#             ----------------------------------------------------
#             ORDER DETAILS
#             ---------------------------------------------------
#             ---------------------------------
#             Reference: {order.order_code}
#             --------------------------------------
#             Thank you for shopping with us
#         """)
#         send_mail(
        
#             'Falkon Parlor',
#             message,#message
#             'settings.Email_HOST_USER', #sender if not available
#             [order.client_email],#receiver
            
#             send_mass_mail(message, fail_silently = False)
#         )
#     except Exception as e:
#         return Response(
#             {'error': 'Email failed'},
#             # status=status.HTTP_404_NOT_FOUND
#         )

@api_view(['POST','GET'])
def create_booking(request, slug):
    try:
        spa = Spa.objects.get(slug=slug)
    except Spa.DoesNotExist:
        return Response(
            {'error': 'Shop not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = OrderCreateSerializer(data=request.data, context={'spa': spa})
    
    if serializer.is_valid():
        try:
            order = serializer.save()
            response_serializer = OrderSerializer(order)
            
            return Response({
                'message': 'Order created successfully',
                'order_code': order.order_code,
                'order': response_serializer.data
                
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#####---E-COMMERCE MANAGEMENT----#########################################
@api_view(['GET'])
def shop_orders(request, slug):
    try:
        spa = Spa.objects.get(slug=slug)
        orders = Order.objects.filter(spa=spa).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    except Spa.DoesNotExist:
        return Response(
            {'error': 'Shop not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST','GET'])
def create_product(request, slug):
    try:
        spa = Spa.objects.get(slug=slug)
        print(f"spa data",spa)
    except Spa.DoesNotExist:
        return Response(
            {'error': 'Shop not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Handle file upload
    data = request.data.copy()
    print(f"added products :",data)
    # data['spa'] = spa.id
    
    serializer = ProductSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT','GET'])
def update_product(request, slug, product_id):
    try:
        spa = Spa.objects.get(slug=slug)
        product = Product.objects.get(id=product_id, spa=spa)
    except (Spa.DoesNotExist, Product.DoesNotExist):
        return Response(
            {'error': 'Shop or product not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = ProductSerializer(product, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT','GET',"PATCH"])
def update_order(request, slug, order_code):
    try:
        spa = Spa.objects.get(slug=slug)
        order = Order.objects.get(order_code=order_code, spa=spa)
    except (Spa.DoesNotExist, Order.DoesNotExist):
        return Response(
            {'error': 'Shop or Order not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    partial = request.method == 'PATCH'
    serializer = OrderSerializer(order, data=request.data, partial=partial)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE','GET'])
def delete_product(request, slug, product_id):
    try:
        spa = Spa.objects.get(slug=slug)
        product = Product.objects.get(id=product_id, spa=spa)
    except (Spa.DoesNotExist, Product.DoesNotExist):
        return Response(
            {'error': 'Shop or product not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    product.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def customer_bookings_by_order_code(request, slug):
    try:
        spa = Spa.objects.get(slug=slug)
    except Spa.DoesNotExist:
        return Response(
            {'error': 'Shop not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    order_code = request.GET.get('order_code')
    if not order_code:
        return Response(
            {'error': 'Order code is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    orders = Order.objects.filter(spa=spa, order_code=order_code)
    if not orders.exists():
        return Response([], status=status.HTTP_200_OK)
    
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

#############-------STAFF--###################################################################################################
@api_view(['GET'])
def get_staff(request, slug):
    """Get all staff for a spa"""
    spa = get_object_or_404(Spa, slug=slug)
    staff_members = Staff.objects.filter(spa=spa)
    
    staff_data = []
    for staff in staff_members:
        staff_data.append({
            'id': staff.id,
            'staff_id': staff.staff_id,
            'name': staff.name,
            'specialization': staff.specialization,
            'is_active': staff.is_active
        })
    
    return Response(staff_data)

@api_view(['POST','GET'])
def save_staff(request, slug):
    """Create new staff"""
    spa = get_object_or_404(Spa, slug=slug)
    
    # Generate unique staff ID
    def generate_staff_id():
        while True:
            staff_id = 'STF' + ''.join(random.choices(string.digits, k=9))
            if not Staff.objects.filter(staff_id=staff_id).exists():
                return staff_id
    
    staff = Staff.objects.create(
        spa=spa,
        staff_id=generate_staff_id(),
        name=request.data.get('name'),
        specialization=request.data.get('specialization', ''),
        is_active=True
    )
    
    return Response({
        'id': staff.id,
        'staff_id': staff.staff_id,
        'name': staff.name,
        'specialization': staff.specialization,
        'is_active': staff.is_active
    }, status=status.HTTP_201_CREATED)

class StaffDetailAPIView(APIView):
    def put(self, request, slug, staff_id):
        """Update staff"""
        staff = get_object_or_404(Staff, id=staff_id, spa__slug=slug)
        
        staff.name = request.data.get('name', staff.name)
        staff.specialization = request.data.get('specialization', staff.specialization)
        staff.is_active = request.data.get('is_active', staff.is_active)
        staff.save()
        
        return Response({
            'id': staff.id,
            'staff_id': staff.staff_id,
            'name': staff.name,
            'specialization': staff.specialization,
            'is_active': staff.is_active
        })

    def delete(self, request, slug, staff_id):
        """Delete staff"""
        staff = get_object_or_404(Staff, id=staff_id, spa__slug=slug)
        staff.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
########################----------------------------------------------STAFF-VIEW--------------------------------------------########################################################
class StaffLoginView(APIView):
    def post(self, request, slug):
        """Verify staff ID and return staff data"""
        staff_id = request.data.get('staff_id')
        
        try:
            spa = get_object_or_404(Spa, slug=slug)
            staff = get_object_or_404(Staff, staff_id=staff_id, spa=spa)
            
            return Response({
                'id': staff.id,
                'staff_id': staff.staff_id,
                'name': staff.name,
                'specialization': staff.specialization,
                'is_active': staff.is_active
            })
            
        except Staff.DoesNotExist:
            return Response({'error': 'Invalid staff ID'}, status=status.HTTP_404_NOT_FOUND)

class StaffStatusView(APIView):
    def put(self, request, slug, staff_id):
        """Update staff availability status"""
        staff = get_object_or_404(Staff, id=staff_id, spa__slug=slug)
        
        staff.is_active = request.data.get('is_active', staff.is_active)
        staff.save()
        
        return Response({
            'id': staff.id,
            'is_active': staff.is_active,
            'message': 'Status updated successfully'
        })

class StaffAppointmentsView(APIView):
    def get(self, request, slug, staff_id):
        """Get upcoming appointments for a specific staff member"""
        spa = get_object_or_404(Spa, slug=slug)
        staff = get_object_or_404(Staff, id=staff_id, spa=spa)
        
        # Get today's date
        today = timezone.now().date()
        
        # Get appointments from today onwards
        appointments = Booking.objects.filter(
            spa=spa,
            staff=staff,
            booking_date__gte=today,
            status__in=['pending', 'confirmed']
        ).order_by('booking_date', 'booking_time')
        
        appointments_data = []
        for appointment in appointments:
            appointments_data.append({
                'id': appointment.id,
                'booking_reference': appointment.booking_reference,
                'customer_name': appointment.customer_name,
                'customer_phone': appointment.customer_phone,
                'booking_date': appointment.booking_date.strftime('%Y-%m-%d'),
                'booking_time': appointment.booking_time.strftime('%H:%M'),
                'services': [
                    {'name': service.name}
                    for service in appointment.services.all()
                ],
                'status': appointment.status,
                'notes': appointment.notes
            })
        
        return Response(appointments_data)