import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"
        self.user = self.scope["user"]

        print(f"🔌 WebSocket connection attempt - Room: {self.room_id}, User: {self.user.username if self.user.is_authenticated else 'Anonymous'}")

        # Check if user is authenticated and part of this room
        if not self.user.is_authenticated:
            print(f"❌ User not authenticated, closing connection")
            await self.close()
            return

        # Verify user is part of this room
        is_valid = await self.is_user_in_room(self.user, self.room_id)
        if not is_valid:
            print(f"❌ User {self.user.username} not authorized for room {self.room_id}, closing connection")
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"✅ WebSocket connection accepted - Room: {self.room_id}, User: {self.user.username}")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            # Note: Actual message saving is handled by the view
            # This can be used for typing indicators or other real-time features
        except json.JSONDecodeError:
            pass

    async def chat_message(self, event):
        # Send message to WebSocket
        message_data = {
            "type": "new_message",
            "message": event["message"],
            "sender_id": event["sender_id"],
            "sender_first_name": event.get("sender_first_name", ""),
            "sender_last_name": event.get("sender_last_name", ""),
            "recipient_id": event["recipient_id"],
            "timestamp": event.get("timestamp", ""),
            "chat_id": event.get("chat_id"),
            "room_id": self.room_id  # Include room_id to verify message belongs to current room
        }
        print(f"📤 Sending message via WebSocket to room {self.room_id}: {message_data}")
        await self.send(text_data=json.dumps(message_data))

    async def message_read(self, event):
        # Notify that a message was read
        await self.send(text_data=json.dumps({
            "type": "message_read",
            "chat_id": event.get("chat_id")
        }))

    @database_sync_to_async
    def is_user_in_room(self, user, room_id):
        from .models import ChatRoom
        try:
            room = ChatRoom.objects.get(id=room_id)
            return room.initiator == user or room.receiver == user
        except ChatRoom.DoesNotExist:
            return False

class AlertsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group = "alerts_staff"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def alert_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "alert",
            "title": event.get("title"),
            "message": event.get("message"),
            "payload": event.get("payload", {})
        }))