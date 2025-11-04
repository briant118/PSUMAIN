from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from account import views as account_views
from . import views

app_name = 'main_app'

urlpatterns = [
    path('', account_views.sf_home, name='home'),
    path('dashboard/', account_views.dashboard, name='dashboard'),
    path('violation-unsuspend/<int:pk>/', views.unsuspend, name='violation-unsuspend'),
    path('ajax/peripheral-event/', views.peripheral_event, name='peripheral-event'),
    path('chats/', views.ChatView.as_view(), name='chats'),
    path('pc-list/', views.PCListView.as_view(), name='pc-list'),
    path('bookings/', views.BookingListView.as_view(), name='bookings'),
    path('users/', views.UserListView.as_view(), name='users'),
    path('user-activities/', views.UserActivityListView.as_view(), name='user-activities'),
    path('violation-suspend/<int:pk>/', views.suspend, name='violation-suspend'),
    path('add-pc-from-form/', views.add_pc_from_form, name='add-pc-from-form'),
    path('delete-pc/<int:pk>/', views.delete_pc, name='delete-pc'),
    path('pc-detail/<int:pk>/', views.PCDetailView.as_view(), name='pc-detail'),
    path('pc-update/<int:pk>/', views.PCUpdateView.as_view(), name='pc-update'),
    path('ping-ip/<int:pk>/', views.ping_ip_address, name='ping-ip'),
    path('reservation-approved/<int:pk>/', views.reservation_approved, name='reservation-approved'),
    path('reservation-declined/<int:pk>/', views.reservation_declined, name='reservation-declined'),
    path('block-reservation-approved/<int:pk>/', views.block_reservation_approved, name='block-reservation-approved'),
    path('block-reservation-declined/<int:pk>/', views.block_reservation_declined, name='block-reservation-declined'),
    path('pc-reservation/', views.ReservePCListView.as_view(), name='pc-reservation'),
    path('reservation-approval/<int:pk>/', views.ReservationApprovalDetailView.as_view(), 
         name='reservation-approval'),
    path('block-reservation-approval/<int:pk>/', views.BlockReservationApprovalDetailView.as_view(), 
         name='block-reservation-approval'),
    path('faculty-booking-confirmation/', views.faculty_booking_confirmation, name='faculty-booking-confirmation'),
    
    path('view/<path:filename>/', views.view_file, name='view_file'),
    path('clearup-pcs/', views.clearup_pcs, name='clearup_pcs'),
    
    # AJAX callback
    path('ajax/get-ping-data/', views.get_ping_data, name='get-ping-data'),
    path('ajax/verify-pc-name/', views.verify_pc_name, name='verify-pc-name'),
    path('ajax/verify-pc-ip-address/', views.verify_pc_ip_address, name='verify-pc-ip-address'),
    path('ajax/get-pc-details/<int:pk>/', views.get_pc_details, name='get-pc-details'),
    path('ajax/get-all-pc-status/', views.get_all_pc_status, name='get-all-pc-status'),
    path('ajax/get-pc-booking/<int:pk>/', views.get_pc_booking, name='get-pc-booking'),
    path('ajax/get-my-active-booking/', views.get_my_active_booking, name='get-my-active-booking'),
    path('ajax/end-session/<int:booking_id>/', views.end_session, name='end-session'),
    path('ajax/extend-session/<int:booking_id>/', views.extend_session, name='extend-session'),
    path('ajax/export-report/', views.export_report, name='export-report'),
    path('ajax/reserve-pc/', views.reserve_pc, name='reserve-pc'),
    path('ajax/waiting-approval/<int:pk>/', views.waiting_approval, name='waiting-approval'),
    path('ajax/cancel-reservation/', views.cancel_reservation, name='cancel-reservation'),
    path('ajax/find-user/', views.find_user, name='find-user'),
    path('ajax/send-init-message/', views.send_init_message, name='send-init-message'),
    path('ajax/send-new-message/<int:room_id>/', views.send_new_message, name='send-new-message'),
    path('ajax/load-messages/', views.load_messages, name='load-messages'),
    path('ajax/load-conversation/<int:room_id>/', views.load_conversation, name='load-conversation'),
    path('ajax/change-message-status/', views.change_message_status, name='change-message-status'),
    path('ajax/submit-block-booking/', views.submit_block_booking, name='submit-block-booking'),
    
    # Reporting
    path('booking-data/', views.bookings_by_college, name='booking-data'),
    path('chat/', views.ChatView.as_view(), name='chat'),
]