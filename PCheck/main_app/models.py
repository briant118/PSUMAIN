from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone


class College(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name
    

class PC(models.Model):
    name = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField()
    status = models.CharField(
        max_length=20, choices=[('connected', 'Connected'), ('disconnected', 'Disconnected')]
    )
    system_condition = models.CharField(
        max_length=20, choices=[('active', 'Active'), ('repair', 'Repair')]
    )
    sort_number = models.CharField(max_length=3, default=0)
    booking_status = models.CharField(
        max_length=20, null=True, choices=[('available', 'Available'), ('in_queue', 'In Queue'), ('in_use', 'In Use')], default='available'
    )
    
    def reserve(self):
        self.booking_status = 'in_queue'
        self.save()
    
    def approve(self):
        self.booking_status = 'in_use'
        self.save()
    
    def decline(self):
        self.booking_status = 'available'
        self.save()

    def __str__(self):
        return self.name


class FacultyBooking(models.Model):
    faculty = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    college = models.ForeignKey(College, null=True, on_delete=models.CASCADE)
    course = models.CharField(max_length=100, null=True, blank=True)
    block = models.CharField(max_length=100, null=True, blank=True)
    start_datetime = models.DateTimeField(null=True, blank=True)
    end_datetime = models.DateTimeField(null=True, blank=True)
    num_of_devices = models.PositiveIntegerField(default=1)
    file = models.FileField(upload_to='bookings_attachments/', null=True, blank=True)
    email_addresses = models.TextField(null=True, blank=True)
    status = models.CharField(
        null=True, max_length=20, choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')]
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pc = models.ForeignKey(PC, null=True, on_delete=models.CASCADE)
    faculty_booking = models.ForeignKey(FacultyBooking, null=True, on_delete=models.CASCADE)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        null=True, max_length=20, choices=[('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')]
    )
    duration = models.DurationField(null=True, blank=True)
    expiry = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Violation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pc = models.ForeignKey(PC, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(
        max_length=20, choices=[('minor', 'Minor'), ('moderate', 'Moderate'), ('major', 'Major')]
    )
    reason = models.CharField(max_length=255)
    resolved = models.BooleanField(default=False)
    status = models.CharField(max_length=20, null=True, blank=True, choices=[('suspended','Suspended'), ('active','Active')])


class PeripheralEvent(models.Model):
    pc = models.ForeignKey(PC, null=True, on_delete=models.SET_NULL)
    device_id = models.CharField(max_length=255, null=True, blank=True)
    device_name = models.CharField(max_length=255, null=True, blank=True)
    action = models.CharField(max_length=32, choices=[('removed','Removed'), ('attached','Attached')])
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pc} {self.action} {self.device_name or self.device_id}"

class ChatRoom(models.Model):
    initiator = models.ForeignKey(User, null=True, related_name='chat_room_initiator', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, null=True, related_name='chat_room_receiver', on_delete=models.CASCADE)


class Chat(models.Model):
    chatroom = models.ForeignKey(ChatRoom, null=True, related_name='chats', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, null=True, related_name='sent_chats', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, null=True, related_name='received_chats', on_delete=models.CASCADE)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=[('sent', 'Sent'), ('delivered', 'Delivered'), ('read', 'Read')])
    timestamp = models.DateTimeField(auto_now_add=True)