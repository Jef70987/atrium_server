from django.urls import*
from .views import *
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView


router = DefaultRouter()

urlpatterns = [
    
    path('api/submit-request/', submit_request, name='submit_request'),
    
    path('api/theme/<str:slug>/', spa_theme, name='spa_theme'),
    path('api/<str:slug>/services/', TenantServicesView.as_view(), name='tenant-services'),
    path('api/<str:slug>/operating-hours/', TenantOperatingHoursView.as_view(), name='tenant-operating-hours'),
    path('api/<str:slug>/available-slots/', AvailableSlotsView.as_view(), name='available-slots'),
    ###
    path('api/csrf-token/', GetCSRFToken.as_view(), name='csrf_token'),
    path('api/<str:slug>/staff/', StaffListView.as_view(), name='staff'),
    path('api/<str:slug>/available-staff/', AvailableStaffView.as_view(), name='available_staff'),
    path('api/<str:slug>/bookings/create/', BookingCreateView.as_view(), name='create_booking'),
    
    ########################################---------ADD SERVICE AND GALLERY---################################
    path('api/spa/<str:slug>/services/', add_service, name='add-service'),
    path('api/spa/<str:slug>/gallery/', add_gallery_image, name='add-gallery'),
    
    ########admin bookings view#################################################################################
    path('api/<str:slug>/bookings/', BookingListView.as_view(), name='booking-list'),
    path('api/<str:slug>/bookings/<int:pk>/', BookingDetailView.as_view(), name='booking-detail'),
    path('api/<str:slug>/bookings/services/', BookingServicesView.as_view(), name='booking_services'),
    ###########CLIENT BOOKINGS VIEW############################################################################
    path('api/<str:slug>/client-bookings/verify/', ClientBookingsVerifyView.as_view(), name='client-bookings-verify'),
    path('api/<str:slug>/client-bookings/', ClientBookingsListView.as_view(), name='client-bookings'),
    
    ###########################################################################################################
    path('api/validate/<str:slug>/',ValidateSpaView.as_view(), name='validate-spa' ) ,
    path('api/home/<str:slug>/details',HomeAPIView.as_view(), name='home' ) ,
    path('api/home/<str:slug>/contact',ContactAPIView.as_view(), name='contact' ) ,
    path('api/home/<str:slug>/offers',OffersAPIView.as_view(), name='offer' ) ,
    path('api/home/<str:slug>/notifications',NotificationsAPIView.as_view(), name='notification' ) ,
    path('api/services/<str:slug>/service', get_services, name='get_services'),
    path('api/gallery/<str:slug>/gallery', get_gallery, name='get_gallery'),
    
    path('api/dashboard/<str:slug>/items', DashboardView.as_view(), name='get_dashboard'),
    path('api/reviews/<str:slug>/', get_reviews, name='get_review'),
    path('api/reviews/<str:slug>/verify/', verify_client, name='verify_client'),
    path('api/reviews/<str:slug>/submit/', submit_review, name='submit_review'),
    # path('api/reviews/<str:slug>/reply/<str:reviewid>/', submit_reply, name='submit_reply'),
    path('api/admin/reviews/<str:slug>/', admin_get_reviews, name='admin_get_reviews'),
    path('api/admin/reviews/<str:slug>/reply/<int:review_id>/', admin_submit_reply, name='admin_submit_reply'),
    path('api/admin/reviews/<str:slug>/approve/<int:review_id>/', admin_approve_review, name='admin_approve_review'),
    path('api/admin/reviews/<str:slug>/delete/<int:review_id>/', admin_delete_review, name='admin_delete_review'),
    # Authentication##############################
    path('api/', include(router.urls)),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/login/', multi_tenant_login, name = 'multi_tenant_login'),
    path('api/auth/token/refresh/', multi_tenant_token_refresh, name='multi_tenant_token_refresh'),
    path('api/user/profile/', user_profile, name='user_profile'),
    ###################--SHOP----#######################################################################################
    path('api/validate/<str:slug>/', validate_shop, name='validate_shop'),
    path('api/shop/<str:slug>/products/', shop_products, name='shop_products'),
    path('api/shop/<str:slug>/bookings/', create_booking, name='create_booking'),
    path('api/shop/<str:slug>/customer-bookings/',customer_bookings_by_order_code, name='customer_bookings_by_order_code'),
    # e-commerce management#############################################################################################
    path('api/shop/<str:slug>/orders/', shop_orders, name='shop_orders'),
    path('api/shop/<str:slug>/addproducts/', create_product, name='create_product'),
    path('api/shop/<str:slug>/products/<int:product_id>/', update_product, name='update_product'),
    path('api/shop/<str:slug>/orders/<str:order_code>/', update_order, name='update_order'),
    path('api/shop/<str:slug>/products/<int:product_id>/delete/', delete_product, name='delete_product'),
    ###-STAFF--##################################################################################################
    path('api/<str:slug>/get/staff/', get_staff, name='staff_list'),
    path('api/<str:slug>/add/staff/', save_staff, name='staff_list'),
    path('api/<str:slug>/get/staff/<int:staff_id>/', StaffDetailAPIView.as_view(), name='staff_detail'),
    
    #-----------------STAFF-VIEW----------------------------------#################################################
    path('api/<slug>/staff/login/', StaffLoginView.as_view(), name='staff_login'),
    path('api/<slug>/staff/<int:staff_id>/status/',StaffStatusView.as_view(), name='staff_status'),
    path('api/<slug>/staff/<int:staff_id>/appointments/', StaffAppointmentsView.as_view(), name='staff_appointments'),
    
]