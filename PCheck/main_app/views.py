import re
import os
import qrcode
import base64
import mimetypes
from django.http import FileResponse, Http404
from django.conf import settings
from io import BytesIO
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseBadRequest
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView, CreateView, ListView, UpdateView, DetailView
from django.views.generic.edit import FormMixin
from django.contrib.auth.decorators import permission_required
from django.db.models import Count
from django.db.models import Prefetch
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from account.models import Profile
from functools import wraps
from django.core.exceptions import PermissionDenied
from . import forms, models, ping_address
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


today = timezone.now()

@login_required
def clearup_pcs(request):
    today = timezone.now()
    bookings = models.Booking.objects.filter(end_time__lt=today,expiry__isnull=True)
    for booking in bookings:
        pc = booking.pc
        pc.booking_status = 'available'
        pc.save()
        booking.expiry = booking.end_time
        booking.save()
    data = {"message": "All PC have been cleared."}
    return JsonResponse(data)


def staff_required(view_func):
    """Decorator to ensure only staff users can access a view."""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account:login')
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'staff':
            raise PermissionDenied("You don't have permission to access this page.")
        return view_func(request, *args, **kwargs)
    return wrapped_view


class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only staff users can access a class-based view."""
    def test_func(self):
        return self.request.user.is_authenticated and hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'staff'


@login_required
def bookings_by_college(request):
    data = (
        models.Booking.objects
        .values("user__profile__college")  # group by college
        .annotate(total=Count("id"))  # count bookings
        .order_by("user__profile__college")
    )

    labels = [d["user__profile__college"] or "Unknown" for d in data]
    values = [d["total"] for d in data]

    return JsonResponse({"labels": labels, "values": values})


def extract_number(value):
    try:
        match = re.search(r'\d+', str(value))
        if match:
            return int(match.group())
        return 0
    except (ValueError, TypeError, AttributeError):
        return 0
    

@login_required
def ping_ip_address(request, pk):
    ip_address = models.PC.objects.get(id=pk).ip_address
    result = ping_address.ping(ip_address)
    return render(request, "main/ping_address.html", {"result": result, 'ip_address': ip_address})


def faculty_booking_confirmation(request):
    return render(request, "main/faculty_booking_confirmation.html")


def get_ping_data(request):
    ip_address = request.GET.get('ip_address')
    result = ping_address.ping(ip_address)
    data = {
        'result': result,
        'ip_address': ip_address
    }
    return JsonResponse(data)


def get_pc_details(request, pk):
    try:
        pc = models.PC.objects.get(pk=pk)
        data = {
            'id': pc.id,
            'name': pc.name,
            'ip_address': pc.ip_address,
            'status': pc.status,
            'system_condition': pc.system_condition
        }
    except models.PC.DoesNotExist:
        data = {
            'error': 'PC not found'
        }
    return JsonResponse(data)


@login_required
def get_all_pc_status(request):
    """Get status of all PCs for dashboard auto-refresh"""
    try:
        pcs = models.PC.objects.all().order_by('sort_number')
        pc_statuses = []
        for pc in pcs:
            pc_statuses.append({
                'id': pc.id,
                'name': pc.name,
                'status': pc.status,
                'system_condition': pc.system_condition,
                'booking_status': pc.booking_status
            })
        return JsonResponse({'pcs': pc_statuses})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def verify_pc_name(request):
    name = request.GET.get('name')
    result = models.PC.objects.filter(name=name).exists()
    data = {
        'result': result,
        'name': name
    }
    return JsonResponse(data)


def waiting_approval(request,pk):
    try:
        booking = models.Booking.objects.get(pk=pk)
        data = {
            'status': booking.status,
            'booking_id': booking.pk
        }
    except models.Booking.DoesNotExist:
        data = {
            'error': 'Booking not found'
        }
    return JsonResponse(data)


def verify_pc_ip_address(request):
    ip_address = request.GET.get('ip_address')
    result = models.PC.objects.filter(ip_address=ip_address).exists()
    data = {
        'result': result,
        'ip_address': ip_address
    }
    return JsonResponse(data)


@login_required
def find_user(request):
    """Only staff can search for users to chat with."""
    # Check if user is staff
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'staff':
        return JsonResponse({
            'result': [],
            'error': 'Only staff can search for users.'
        }, status=403)
    
    find_user = request.GET.get('find_user', '')
    # Only show non-staff users (staff can only chat with users, not other staff)
    result = User.objects.prefetch_related("profile").filter(
        first_name__icontains=find_user
    ).exclude(
        pk=request.user.pk
    ).exclude(
        profile__role='staff'  # Exclude staff users
    ).values(
        'id','first_name','last_name','email',
        'profile__role','profile__college__name','profile__course',
        'profile__year','profile__block','profile__school_id')
    data = {
        'result': list(result),
    }
    return JsonResponse(data, safe=False)


@login_required
@staff_required
def add_pc_from_form(request):
    if request.method == "POST":
        name = request.POST.get('name')
        ip_address = request.POST.get('ip_address')

        name_exists = models.PC.objects.filter(name=name).exists()
        ip_address_exists = models.PC.objects.filter(ip_address=ip_address).exists()

        if name_exists or ip_address_exists:
            if name_exists:
                messages.error(request, "PC with this name already exists.")
            if ip_address_exists:
                messages.error(request, "PC with this IP address already exists.")
            
            context = {
                "name": name,
                "ip_address": ip_address,
                "pc_list": models.PC.objects.all(),
            }
            return render(request, "main/pc_list.html", context)
        
        sort_num = extract_number(name)
        value_length = len(str(sort_num))
        if value_length == 1:
            prefix_zero = '00'
        elif value_length == 2:
            prefix_zero = '0'
        else:
            prefix_zero = ''
        
        sort_number = f"{prefix_zero}{sort_num}"

        # If no errors, create PC
        models.PC.objects.create(
            name=name,
            ip_address=ip_address,
            status='connected',
            system_condition='active',
            sort_number=sort_number
        )
        messages.success(request, "PC added successfully.")
        return HttpResponseRedirect(reverse_lazy('main_app:pc-list'))

    # fallback for GET
    context = {
        "pc_list": models.PC.objects.all()
    }
    return render(request, "main/pc_list.html", context)


@login_required
def submit_block_booking(request):
    if request.method == "POST":
        cust_num_of_pc = request.POST.get('custNumOfPc')
        num_of_pc = request.POST.get('numOfPc')
        course = request.POST.get('course')
        block = request.POST.get('block')
        college = request.POST.get('college')
        date_start = request.POST.get('dateStart')
        date_end = request.POST.get('dateEnd')
        email_list = request.POST.get('emailList')
        attachment = request.FILES.get('attachment')
        
        college_obj = get_object_or_404(models.College, pk=college)
        
        models.FacultyBooking.objects.create(
            faculty=request.user,
            college=college_obj,
            course=course,
            block=block,
            start_datetime=date_start,
            end_datetime=date_end,
            num_of_devices=cust_num_of_pc if cust_num_of_pc and int(cust_num_of_pc) > 0 else num_of_pc,
            file=attachment,
            email_addresses=email_list,
            status="pending"
        )
        
        return HttpResponseRedirect(reverse_lazy('main_app:faculty-booking-confirmation'))


@login_required
@staff_required
def delete_pc(request, pk):
    models.PC.objects.filter(pk=pk).delete()
    messages.success(request, "PC deleted successfully.")
    return HttpResponseRedirect(reverse_lazy('main_app:pc-list'))


@login_required
def get_pc_booking(request, pk):
    """Get booking information for a specific PC"""
    try:
        from django.utils import timezone
        pc = models.PC.objects.get(pk=pk)
        # Get the most recent active booking for this PC
        booking = models.Booking.objects.filter(
            pc=pc,
            status__in=['confirmed', None]
        ).exclude(status='cancelled').order_by('-created_at').first()
        
        data = {
            'pc_name': pc.name,
            'booking_status': pc.booking_status,
            'status': pc.status,  # connected/disconnected
            'system_condition': pc.system_condition,  # active/repair
            'time_remaining': 'Unknown',
            'created_time': 'Unknown',
            'user': 'Unknown',
            'college': 'Unknown'
        }
        
        if booking:
            data['user'] = booking.user.get_full_name() or booking.user.username
            data['booking_id'] = booking.id  # Only include booking_id when booking exists
            data['created_time'] = booking.created_at.strftime('%Y-%m-%d %H:%M:%S')
            
            # Get college if available
            if hasattr(booking.user, 'profile') and booking.user.profile.college:
                data['college'] = booking.user.profile.college.name
            
            # Calculate time remaining if booking is active
            if pc.booking_status == 'in_use' and booking.end_time:
                now = timezone.now()
                # Handle timezone-aware datetime
                if booking.end_time.tzinfo:
                    remaining = booking.end_time - now
                else:
                    from datetime import datetime
                    remaining = booking.end_time - datetime.now()
                    
                if remaining.total_seconds() > 0:
                    hours = int(remaining.total_seconds() // 3600)
                    minutes = int((remaining.total_seconds() % 3600) // 60)
                    data['time_remaining'] = f"{hours}h {minutes}m"
                else:
                    data['time_remaining'] = 'Expired'
            elif pc.booking_status == 'in_queue':
                data['time_remaining'] = 'Waiting for approval'
        
        return JsonResponse(data)
    except models.PC.DoesNotExist:
        return JsonResponse({'error': 'PC not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_my_active_booking(request):
    """Get active booking for current user"""
    try:
        from django.utils import timezone
        
        # Get the user's most recent booking that's either in_queue or confirmed
        booking = models.Booking.objects.filter(
            user=request.user,
            status__in=['confirmed', None]
        ).exclude(status='cancelled').order_by('-created_at').first()
        
        if booking:
            pc = booking.pc
            data = {
                'has_booking': True,
                'booking_id': booking.id,  # Include booking_id so frontend can use it for ending session
                'pc_id': pc.id if pc else None,
                'pc_name': pc.name if pc else 'Unknown',
                'status': pc.booking_status if pc else 'unknown',
                'booking_status': booking.status,
                'time_remaining': 'Unknown',
                'end_time': None,
                'duration_minutes': 0
            }
            
            # Calculate time remaining if booking is active
            if booking.end_time and pc and pc.booking_status == 'in_use':
                now = timezone.now()
                # Handle timezone-aware datetime
                if booking.end_time.tzinfo:
                    # Both are timezone-aware
                    remaining = booking.end_time - now
                else:
                    # If end_time is naive, compare with naive datetime
                    from datetime import datetime
                    remaining = booking.end_time - datetime.now()
                
                if remaining.total_seconds() > 0:
                    hours = int(remaining.total_seconds() // 3600)
                    minutes = int((remaining.total_seconds() % 3600) // 60)
                    data['time_remaining'] = f"{hours}h {minutes}m"
                    data['end_time'] = booking.end_time.isoformat()
                else:
                    data['time_remaining'] = 'Expired'
                    data['has_booking'] = False
            elif pc and pc.booking_status == 'in_queue':
                data['time_remaining'] = 'Waiting for approval'
            
            # Calculate duration in minutes
            if booking.duration:
                data['duration_minutes'] = int(booking.duration.total_seconds() / 60)
                
            return JsonResponse(data)
        else:
            return JsonResponse({'has_booking': False})
            
    except Exception as e:
        return JsonResponse({'has_booking': False, 'error': str(e)})


@login_required
def end_session(request, booking_id):
    """End user's session early - staff can end any session, users can only end their own"""
    if request.method == "POST":
        try:
            from django.utils import timezone
            booking = get_object_or_404(models.Booking, pk=booking_id)
            
            # Staff can end any session, users can only end their own
            if not (request.user.profile.role == 'staff' or booking.user == request.user):
                return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            
            if booking:
                pc = booking.pc
                pc.booking_status = 'available'
                pc.save()
                
                booking.status = 'cancelled'
                booking.save()
                
                return JsonResponse({'success': True, 'message': 'Session ended successfully'})
            else:
                return JsonResponse({'success': False, 'error': 'No active session found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required
@staff_required
def extend_session(request, booking_id):
    """Extend user's session by specified minutes"""
    if request.method == "POST":
        try:
            import json
            from django.utils import timezone
            data = json.loads(request.body)
            minutes = int(data.get('minutes', 30))
            
            booking = get_object_or_404(models.Booking, pk=booking_id)
            
            if booking.status == 'confirmed' and booking.end_time:
                # Extend the end time
                booking.end_time = booking.end_time + timedelta(minutes=minutes)
                booking.save()
                
                # Get user information
                user_name = booking.user.get_full_name() or booking.user.username
                user_college = ''
                if hasattr(booking.user, 'profile') and booking.user.profile.college:
                    user_college = booking.user.profile.college.name
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Session extended by {minutes} minutes',
                    'new_end_time': booking.end_time.isoformat(),
                    'user_name': user_name,
                    'user_college': user_college,
                    'pc_name': booking.pc.name if booking.pc else ''
                })
            else:
                return JsonResponse({'success': False, 'error': 'Session not active or cannot be extended'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


@login_required
@staff_required
def export_report(request):
    """Export analytics report as CSV"""
    import csv
    from django.http import HttpResponse
    from datetime import datetime, timedelta
    
    period = request.GET.get('period', 'daily')
    
    # Determine date range based on period
    today = datetime.now()
    if period == 'daily':
        start_date = today - timedelta(days=1)
        filename = f'report_daily_{today.strftime("%Y%m%d")}.csv'
    elif period == 'weekly':
        start_date = today - timedelta(days=7)
        filename = f'report_weekly_{today.strftime("%Y%m%d")}.csv'
    elif period == 'monthly':
        start_date = today - timedelta(days=30)
        filename = f'report_monthly_{today.strftime("%Y%m%d")}.csv'
    else:
        start_date = today - timedelta(days=1)
        filename = f'report_{today.strftime("%Y%m%d")}.csv'
    
    # Get booking data
    bookings = models.Booking.objects.filter(created_at__gte=start_date)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow(['Date', 'Time', 'User', 'PC Name', 'College', 'Status', 'Duration (minutes)'])
    
    # Write data rows
    for booking in bookings:
        duration_minutes = 0
        if booking.duration:
            duration_minutes = int(booking.duration.total_seconds() / 60)
        
        writer.writerow([
            booking.created_at.strftime('%Y-%m-%d'),
            booking.created_at.strftime('%H:%M:%S'),
            booking.user.get_full_name(),
            booking.pc.name if booking.pc else 'N/A',
            booking.user.profile.college.name if hasattr(booking.user, 'profile') else 'N/A',
            booking.status or 'Pending',
            duration_minutes
        ])
    
    return response


@csrf_exempt
def reserve_pc(request):
    if request.method == "POST":
        try:
            pc_id = request.POST.get("pc_id")
            duration = request.POST.get("duration")
            
            if not pc_id or not duration:
                return JsonResponse({
                    "success": False,
                    "error": "Missing pc_id or duration"
                }, status=400)

            pc = get_object_or_404(models.PC, id=pc_id)
            
            # Check if PC is in repair
            if pc.system_condition == 'repair':
                return JsonResponse({
                    "success": False,
                    "error": f"PC {pc.name} is currently in repair and not available for reservation."
                }, status=400)
            
            # Check if PC is offline/disconnected
            if pc.status == 'disconnected':
                return JsonResponse({
                    "success": False,
                    "error": f"PC {pc.name} is currently offline and not available for reservation."
                }, status=400)
            
            # Check if PC is already booked
            if pc.booking_status in ['in_use', 'in_queue']:
                return JsonResponse({
                    "success": False,
                    "error": f"PC {pc.name} is already booked or in queue."
                }, status=400)
            
            pc.reserve()
            
            # Convert duration (minutes) to DurationField (timedelta)
            duration_timedelta = timedelta(minutes=int(duration))
            
            print(f"Creating booking: user={request.user}, pc={pc}, duration={duration_timedelta}")
            
            booking = models.Booking.objects.create(
                user=request.user,
                pc=pc,
                start_time=datetime.now(),
                duration=duration_timedelta,
            )
            
            print(f"Booking created successfully: {booking.id}, status={booking.status}")
            
            scheme = 'https' if request.is_secure() else 'http'
            host = request.get_host()

            # Generate QR code (data = reservation details or URL)
            qr_data = f"{scheme}://{host}/reservation-approval/{booking.pk}/"
            qr = qrcode.make(qr_data)
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            return JsonResponse({
                "success": True,
                "message": f"{pc.name} reserved for {duration} minutes",
                "qr_code": qr_base64,
                "booking_id": booking.pk
            })
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"ERROR creating booking: {error_details}")
            return JsonResponse({
                "success": False,
                "error": str(e),
                "details": error_details[:500]  # First 500 chars of traceback
            }, status=500)
    
    return JsonResponse({
        "success": False,
        "error": "Method not allowed"
    }, status=405)


@login_required
@never_cache
def load_messages(request):
    """Load chat rooms. For non-staff users, only show conversations with staff."""
    is_staff = (hasattr(request.user, 'profile') and request.user.profile.role == 'staff')
    
    if is_staff:
        # Staff can see all their conversations
        chatrooms = models.ChatRoom.objects.filter(
            Q(initiator=request.user) | Q(receiver=request.user)
        ).prefetch_related(
            Prefetch('chats', queryset=models.Chat.objects.all().order_by('-timestamp'))
        )
    else:
        # Non-staff users: show all their conversations (more robust; avoids missing rooms if staff profile role is unset)
        chatrooms = models.ChatRoom.objects.filter(
            Q(initiator=request.user) | Q(receiver=request.user)
        ).prefetch_related(
            Prefetch('chats', queryset=models.Chat.objects.all().order_by('-timestamp'))
        )

    result = []
    for room in chatrooms:
        # Ensure both initiator and receiver exist
        if not room.initiator or not room.receiver:
            continue
            
        # Get role for initiator and receiver
        initiator_role = None
        receiver_role = None
        if hasattr(room.initiator, 'profile') and room.initiator.profile.role:
            initiator_role = room.initiator.profile.role
        if hasattr(room.receiver, 'profile') and room.receiver.profile.role:
            receiver_role = room.receiver.profile.role
        
        room_data = {
            'id': room.id,
            'initiator': {
                'id': room.initiator.id,
                'first_name': room.initiator.first_name or '',
                'last_name': room.initiator.last_name or '',
                'email': room.initiator.email or '',
                'role': initiator_role or '',
            },
            'receiver': {
                'id': room.receiver.id,
                'first_name': room.receiver.first_name or '',
                'last_name': room.receiver.last_name or '',
                'email': room.receiver.email or '',
                'role': receiver_role or '',
            },
            'chats': [
                {
                    'id': chat.id,
                    'message': chat.message,
                    'status': chat.status,
                    'sender': chat.sender.id if chat.sender else None,
                    'recipient': chat.recipient.id if chat.recipient else None,
                    'timestamp': chat.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                }
                for chat in room.chats.all()
            ]
        }
        result.append(room_data)

    return JsonResponse({'result': result})


@login_required
@never_cache
def load_conversation(request, room_id):
    # Verify user is part of this conversation
    try:
        room = models.ChatRoom.objects.get(id=room_id)
        if room.initiator != request.user and room.receiver != request.user:
            return JsonResponse({
                "success": False,
                "error": "You are not part of this conversation."
            }, status=403)
    except models.ChatRoom.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Conversation not found."
        }, status=404)
    
    result = models.Chat.objects.filter(chatroom=room_id).order_by('timestamp').values(
            'recipient__first_name','recipient__last_name','recipient__email','recipient__id',
            'sender__first_name','sender__last_name','sender__email','sender__id','message','timestamp',
            'chatroom__initiator__id','chatroom__receiver__id','chatroom__id')
    data = {
        'result': list(result),
    }
    return JsonResponse(data, safe=False)


@csrf_exempt
@login_required
def send_init_message(request):
    """
    Initiate a chat. Supports a special recipient value "PCheck" which broadcasts
    the message to all staff/admin users by creating/using individual rooms.
    """
    if request.method == "POST":
        message = request.POST.get("message")
        recipient_value = request.POST.get("recipient") or ""

        # If recipient is the special alias, broadcast to all staff
        if recipient_value.strip().lower() == "pcheck":
            staff_users = User.objects.filter(profile__role='staff').exclude(pk=request.user.pk)
            broadcasted_room_ids = []
            for staff_user in staff_users:
                room = models.ChatRoom.objects.filter(
                    Q(initiator=request.user, receiver=staff_user) | Q(initiator=staff_user, receiver=request.user)
                ).first()
                if not room:
                    room = models.ChatRoom.objects.create(initiator=request.user, receiver=staff_user)
                chat = models.Chat.objects.create(
                    chatroom=room,
                    sender=request.user,
                    recipient=staff_user,
                    message=message,
                    status="sent"
                )
                broadcasted_room_ids.append(room.id)

                # Broadcast via WebSocket per room
                try:
                    channel_layer = get_channel_layer()
                    if channel_layer:
                        async_to_sync(channel_layer.group_send)(
                            f'chat_{room.id}',
                            {
                                'type': 'chat_message',
                                'message': message,
                                'sender_id': request.user.id,
                                'sender_first_name': request.user.first_name or '',
                                'sender_last_name': request.user.last_name or '',
                                'recipient_id': staff_user.id,
                                'timestamp': chat.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                'chat_id': chat.id
                            }
                        )
                except Exception:
                    pass

            return JsonResponse({
                "success": True,
                "message": message,
                "rooms": broadcasted_room_ids
            })

        # Otherwise, normal 1:1 init: staff can message non-staff; users may also reach staff
        try:
            recipient = User.objects.filter(email=recipient_value).first()
            if not recipient:
                return JsonResponse({"success": False, "error": "Recipient not found."}, status=404)
        except Exception:
            return JsonResponse({"success": False, "error": "Recipient not found."}, status=404)

        # If the sender is staff, allow contacting any non-staff (existing rule)
        is_sender_staff = hasattr(request.user, 'profile') and request.user.profile.role == 'staff'
        if is_sender_staff and hasattr(recipient, 'profile') and recipient.profile.role == 'staff':
            return JsonResponse({"success": False, "error": "Staff can only chat with non-staff users."}, status=403)

        # If sender is not staff, require recipient to be staff
        if not is_sender_staff and not (hasattr(recipient, 'profile') and recipient.profile.role == 'staff'):
            return JsonResponse({"success": False, "error": "You can only message PCheck or staff."}, status=403)

        room = models.ChatRoom.objects.filter(
            Q(initiator=request.user, receiver=recipient) | Q(initiator=recipient, receiver=request.user)
        ).first()
        if not room:
            room = models.ChatRoom.objects.create(initiator=request.user, receiver=recipient)

        chat = models.Chat.objects.create(
            chatroom=room,
            sender=request.user,
            recipient=recipient,
            message=message,
            status="sent"
        )

        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f'chat_{room.id}',
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender_id': request.user.id,
                        'sender_first_name': request.user.first_name or '',
                        'sender_last_name': request.user.last_name or '',
                        'recipient_id': recipient.id,
                        'timestamp': chat.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'chat_id': chat.id
                    }
                )
        except Exception:
            pass

        return JsonResponse({
            "success": True,
            "message": message,
            "room_id": room.id
        })


@csrf_exempt
@login_required
def send_new_message(request, room_id):
    """Allow staff to send messages, or users to reply to staff-initiated conversations."""
    if request.method == "POST":
        room = get_object_or_404(models.ChatRoom, id=room_id)
        
        # Ensure user is part of this conversation
        if room.initiator != request.user and room.receiver != request.user:
            return JsonResponse({
                "success": False,
                "error": "You are not part of this conversation."
            }, status=403)
        
        # Check if user is staff - staff can always send
        is_staff = (hasattr(request.user, 'profile') and request.user.profile.role == 'staff')
        
        # If user is not staff, ensure this conversation was started by staff
        if not is_staff:
            staff_initiator = (hasattr(room.initiator, 'profile') and room.initiator.profile.role == 'staff')
            if not staff_initiator:
                return JsonResponse({
                    "success": False,
                    "error": "Users can only reply to conversations started by staff."
                }, status=403)
        # Staff can send in any conversation they're part of - no additional checks needed
        
        message = request.POST.get("message")
        receiver = room.receiver if room.initiator == request.user else room.initiator

        chat = models.Chat.objects.create(
            sender=request.user,
            recipient=receiver,
            chatroom=room,
            message=message,
            status="sent"
        )

        # Broadcast message via WebSocket
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f'chat_{room.id}',
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender_id': request.user.id,
                        'sender_first_name': request.user.first_name or '',
                        'sender_last_name': request.user.last_name or '',
                        'recipient_id': receiver.id,
                        'timestamp': chat.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'chat_id': chat.id
                    }
                )
                print(f"✅ WebSocket broadcast sent to chat_{room.id}")
            else:
                print("⚠️ Channel layer not available")
        except Exception as e:
            import traceback
            print(f"❌ WebSocket broadcast failed: {e}")
            traceback.print_exc()
            # WebSocket broadcast failed, but message is saved

        return JsonResponse({
            "success": True,
            "message": message,
            "room_id": room.id
        })


@login_required
@staff_required
def reservation_approved(request, pk):
    booking = models.Booking.objects.get(pk=pk)
    pc = models.PC.objects.get(pk=booking.pc.pk)
    pc.approve()
    booking.start_time = timezone.now()
    # booking.duration is already a timedelta, so use it directly
    booking.end_time = booking.start_time + booking.duration
    booking.status = 'confirmed'
    booking.save()
    messages.success(request, "Reservation has been approved.")
    return HttpResponseRedirect(reverse_lazy('main_app:bookings'))


@login_required
@staff_required
def reservation_declined(request, pk):
    booking = models.Booking.objects.get(pk=pk)
    pc = models.PC.objects.get(pk=booking.pc.pk)
    pc.decline()
    booking.status = 'cancelled'
    booking.start_time = timezone.now()
    booking.save()
    messages.success(request, "Reservation has been declined.")
    return HttpResponseRedirect(reverse_lazy('main_app:dashboard'))


@login_required
@staff_required
def block_reservation_approved(request, pk):
    booking = models.FacultyBooking.objects.get(pk=pk)
    booking.status = 'confirmed'
    booking.save()
    messages.success(request, "Reservation confirmed!")
    return HttpResponseRedirect(reverse_lazy('main_app:bookings'))


@login_required
@staff_required
def block_reservation_declined(request, pk):
    booking = models.FacultyBooking.objects.get(pk=pk)
    booking.status = 'cancelled'
    booking.save()
    messages.success(request, "Reservation declined!")
    return HttpResponseRedirect(reverse_lazy('main_app:dashboard'))


@login_required
@staff_required
@csrf_exempt
def suspend(request, pk):
    if request.method == "POST":
        level = request.POST.get("level")
        reason = request.POST.get("reason")
    booking = models.Booking.objects.get(pk=pk)
    models.Violation.objects.create(
        user = booking.user,
        pc=booking.pc,
        level=level,
        reason=reason,
        status="suspended"
    )
    messages.success(request, "Account suspended!")
    return HttpResponseRedirect(reverse_lazy('main_app:user-activities'))


@login_required
@staff_required
@csrf_exempt
def unsuspend(request, pk):
    """Mark a violation as active (unsuspend)."""
    try:
        violation = models.Violation.objects.get(pk=pk)
        violation.status = 'active'
        violation.resolved = True
        violation.save(update_fields=['status', 'resolved'])
        messages.success(request, "Account unsuspended!")
        return JsonResponse({"success": True})
    except models.Violation.DoesNotExist:
        return JsonResponse({"success": False, "error": "Violation not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@csrf_exempt
def change_message_status(request):
    if request.method == "POST":
        room_id = request.POST.get("room_id")
        chat = models.Chat.objects.filter(chatroom=room_id,status="sent")
        chat.update(status="read")
        
        return JsonResponse({
            "success": True,
        })


@login_required
@csrf_exempt
def cancel_reservation(request):
    if request.method == "POST":
        booking_id = request.POST.get("booking_id")
        pc_id = request.POST.get("pc_id")
        
        try:
            # Check if user is staff
            is_staff = (hasattr(request.user, 'profile') and request.user.profile.role == 'staff')
            
            # If booking_id is provided, cancel the booking properly
            if booking_id:
                # Staff can cancel any booking, users can only cancel their own
                if is_staff:
                    booking = get_object_or_404(models.Booking, pk=booking_id)
                else:
                    booking = get_object_or_404(models.Booking, pk=booking_id, user=request.user)
                
                booking.status = 'cancelled'
                booking.save()
                
                # Free up the PC
                if booking.pc:
                    booking.pc.booking_status = 'available'
                    booking.pc.save()
                    
                return JsonResponse({
                    "success": True,
                    "message": "Booking cancelled successfully"
                })
            # Fallback to old behavior if only pc_id provided
            elif pc_id:
                pc = models.PC.objects.get(pk=pc_id)
                pc.booking_status = 'available'
                pc.save()
                
                # Also cancel any pending booking for this user and PC
                booking = models.Booking.objects.filter(
                    user=request.user,
                    pc=pc,
                    status__isnull=True
                ).first()
                if booking:
                    booking.status = 'cancelled'
                    booking.save()
                
                return JsonResponse({
                    "success": True,
                    "message": "Reservation cancelled successfully"
                })
            else:
                return JsonResponse({
                    "success": False,
                    "error": "booking_id or pc_id required"
                }, status=400)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=500)
    
    return JsonResponse({
        "success": False,
        "error": "Method not allowed"
    }, status=405)
        

@login_required
def view_file(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    
    if not os.path.exists(file_path):
        raise Http404("File not found")
    
    mime_type, _ = mimetypes.guess_type(file_path)
    return FileResponse(open(file_path, 'rb'), content_type=mime_type)
        

class PCListView(StaffRequiredMixin, LoginRequiredMixin, FormMixin, ListView):
    model = models.PC
    template_name = "main/pc_list.html"
    form_class = forms.CreatePCForm
    success_url = reverse_lazy("main_app:pc-list")
    
    def get_queryset(self):
        qs = super().get_queryset()
        filter_type = self.request.GET.get("filter")

        if filter_type == "repair":
            qs = qs.filter(system_condition='repair')
        return qs.order_by('sort_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pc_list = self.get_queryset()
        context = {
            "form": self.get_form(),
            "pc_list": pc_list,
            "section": "pc_list",
        }
        return context

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        pc_id = request.POST.get("pc_id")
        if pc_id:  # update
            pc = get_object_or_404(models.PC, id=pc_id)
            form = forms.CreatePCForm(request.POST, instance=pc)
        else:  # create
            form = forms.CreatePCForm(request.POST)

        if form.is_valid():
            f = form.save(commit=False)
            
            # Set default values for new PCs if not provided
            if not pc_id:
                if not f.status:
                    f.status = 'connected'
                if not f.system_condition:
                    f.system_condition = 'active'
                if not f.booking_status:
                    f.booking_status = 'available'
                
            sort_number = extract_number(f.name)
            value_length = len(str(sort_number))
            if value_length == 1:
                prefix_zero = '00'
            elif value_length == 2:
                prefix_zero = '0'
            else:
                prefix_zero = ''
            sort_number = f"{prefix_zero}{sort_number}"
            f.sort_number = sort_number
            f.save()
            messages.success(request, "PC saved successfully!")
            return redirect(self.get_success_url())
        else:
            # Form has errors
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            messages.error(request, f"Form validation errors: {' '.join(error_messages)}")
        return self.render_to_response(self.get_context_data(form=form))
        

class PCDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'main/pc_detail.html'
    
    def get_context_data(self, **kwargs):
        pc = models.PC.objects.get(id=self.kwargs['pk'])
        context = super().get_context_data(**kwargs)
        context.update({
            'pc': pc,
        })
        return context


class ReservationApprovalDetailView(StaffRequiredMixin, LoginRequiredMixin, TemplateView):
    """Automatically approve when accessed via QR scan. Approve/Decline only for faculty bulk bookings."""
    
    def dispatch(self, request, *args, **kwargs):
        # Auto-approve when accessed (QR scan or direct link)
        # This removes the need for approve/decline buttons
        try:
            reservation = models.Booking.objects.get(id=self.kwargs['pk'])
            pc = reservation.pc
            pc.approve()  # Mark PC as in_use (green)
            reservation.start_time = timezone.now()
            reservation.end_time = reservation.start_time + reservation.duration
            reservation.status = 'confirmed'
            reservation.save()
            
            messages.success(request, f"Reservation for {pc.name} has been automatically approved!")
            return HttpResponseRedirect(reverse_lazy('main_app:dashboard'))
        except models.Booking.DoesNotExist:
            messages.error(request, "Reservation not found.")
            return HttpResponseRedirect(reverse_lazy('main_app:dashboard'))
        except Exception as e:
            messages.error(request, f"Error approving reservation: {str(e)}")
            return HttpResponseRedirect(reverse_lazy('main_app:dashboard'))


class BlockReservationApprovalDetailView(StaffRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = 'main/block_reservation_approval.html'
    
    def get_context_data(self, **kwargs):
        reservation = models.FacultyBooking.objects.get(id=self.kwargs['pk'])
        context = super().get_context_data(**kwargs)
        context.update({
            'reservation': reservation,
        })
        return context
    

class PCUpdateView(StaffRequiredMixin, LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = forms.UpdatePCForm
    success_message = 'successfully updated!'
    template_name = 'main/update_pc.html'

    def get_success_url(self):
        return reverse_lazy('main_app:pc-detail', kwargs={'pk' : self.object.pk})

    def get_queryset(self, **kwargs):
        return models.PC.objects.filter(pk=self.kwargs['pk'])


class BookingListView(StaffRequiredMixin, LoginRequiredMixin, ListView):
    model = models.Booking
    template_name = "main/bookings.html"
    success_url = reverse_lazy("main_app:bookings")
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_bookings = self.get_queryset()
        student_pending_approvals = models.Booking.objects.filter(
            status__isnull=True).order_by('-created_at')
        student_approved_bookings = models.Booking.objects.filter(
            status='confirmed').order_by('-created_at')
        
        # Debug: Print booking counts
        total_bookings = models.Booking.objects.count()
        pending_count = student_pending_approvals.count()
        approved_count = student_approved_bookings.count()
        
        print(f"DEBUG BookingsListView:")
        print(f"  Total bookings: {total_bookings}")
        print(f"  Pending bookings: {pending_count}")
        print(f"  Approved bookings: {approved_count}")
        
        if total_bookings > 0:
            sample_booking = models.Booking.objects.first()
            print(f"  Sample booking: status={sample_booking.status}, user={sample_booking.user}, created={sample_booking.created_at}")
        
        faculty_bookings = models.FacultyBooking.objects.all().order_by('-created_at')
        faculty_pending_approvals = models.FacultyBooking.objects.filter(status="pending").order_by('-created_at')
        faculty_approved_bookings = models.FacultyBooking.objects.filter(status="confirmed").order_by('-created_at')
        student_pending_count = student_pending_approvals.count()
        faculty_pending_count = faculty_pending_approvals.count()
        context = {
            "student_bookings": student_bookings,
            "faculty_bookings": faculty_bookings,
            "faculty_pending_approvals": faculty_pending_approvals,
            "faculty_approved_bookings": faculty_approved_bookings,
            "student_pending_approvals": student_pending_approvals,
            "student_approved_bookings": student_approved_bookings,
            "faculty_pending_count": faculty_pending_count,
            "student_pending_count": student_pending_count,
            "section": 'bookings',
        }
        return context


class ReservePCListView(LoginRequiredMixin, ListView):
    model = models.PC
    template_name = "main/reserve_pc.html"
    context_object_name = "available_pcs"
    success_url = reverse_lazy("main_app:dashboard")
    paginate_by = 12
    
    def get_queryset(self):
        qs = super().get_queryset()
        # Return all PCs, not just connected ones
        print(f"Total PCs in database: {qs.count()}")
        return qs.order_by('sort_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_pc'] = models.PC.objects.count()  # total number of PCs in database
        context['colleges'] = models.College.objects.all()
        context['connected_pcs'] = models.PC.objects.filter(status='connected').count()
        # Calculate truly available PCs (not offline, not in repair, not booked)
        context['available_count'] = models.PC.objects.filter(
            status='connected',
            system_condition='active',
            booking_status__in=['available', None]
        ).count()
        return context
    

class UserActivityListView(LoginRequiredMixin, ListView):
    model = models.Booking
    template_name = "main/user_activity.html"
    paginate_by = 12

    def dispatch(self, request, *args, **kwargs):
        # Only allow staff; others get denied/re-directed
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated or not hasattr(user, "profile") or user.profile.role != "staff":
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("You do not have access to this page.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.order_by('created_at').distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bookings = models.Booking.objects.all()
        user_activities = self.get_queryset()
        violations = models.Violation.objects.filter(status='suspended')
        unread_messages = models.Chat.objects.filter(
            recipient=self.request.user, status="sent").count()
        search_user = self.request.GET.get("search_user")
        if search_user != None:
            users = User.objects.filter(first_name__icontains=search_user)
        else:
            users = User.objects.all()
        chat = models.Chat.objects.filter(sender=self.request.user)
        context = {
            "user_activities": user_activities,
            "violations": violations,
            "section": "user",
            "users": users,
            "chat": chat,
            "unread_messages": unread_messages,
        }
        return context


class UserListView(StaffRequiredMixin, LoginRequiredMixin, ListView):
    model = User
    template_name = "main/users.html"
    context_object_name = "users"
    success_url = reverse_lazy("main_app:dashboard")
    paginate_by = 50
    
    def get_queryset(self):
        qs = super().get_queryset()
        search_user = self.request.GET.get("search-user")
        # Do NOT exclude any role; always include staff/admin too
        if search_user and search_user != "":
            qs = qs.filter(username__icontains=search_user) | qs.filter(email__icontains=search_user)
        return qs


class ChatView(LoginRequiredMixin, TemplateView):
    template_name = "main/chat.html"
    def dispatch(self, request, *args, **kwargs):
        user = getattr(request, "user", None)
        # Allow all authenticated users (staff can use Users page, but can also access this)
        # Non-staff users need this page to view messages from staff
        if not user or not user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not hasattr(user, "profile"):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("User profile not found.")
        return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Chat
        unread_messages = Chat.objects.filter(recipient=self.request.user, status="sent").count()
        context["unread_messages"] = unread_messages
        return context


@csrf_exempt
def peripheral_event(request):
    if request.method != 'POST':
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)
    try:
        pc_name = request.POST.get('pc_name') or request.POST.get('pc')
        device_id = request.POST.get('device_id')
        device_name = request.POST.get('device_name')
        action = request.POST.get('action')  # removed/attached
        metadata = request.POST.dict()

        pc = None
        if pc_name:
            pc = models.PC.objects.filter(name=pc_name).first()
        evt = models.PeripheralEvent.objects.create(
            pc=pc,
            device_id=device_id,
            device_name=device_name,
            action=action or 'removed',
            metadata=metadata
        )
        # Broadcast to staff
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'alerts_staff',
                {
                    'type': 'alert_message',
                    'title': 'Peripheral change',
                    'message': f"{pc_name or 'PC'}: {device_name or device_id} {action}",
                    'payload': {
                        'pc': pc_name,
                        'device_id': device_id,
                        'device_name': device_name,
                        'action': action,
                        'created_at': evt.created_at.isoformat()
                    }
                }
            )
        except Exception:
            pass
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)