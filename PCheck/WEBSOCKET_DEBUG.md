# WebSocket Debugging Guide

## Testing Real-time Messaging

1. **Open Browser Console (F12)** before testing

2. **As Staff:**
   - Open `/users/` or `/user-activities/`
   - Click on a conversation
   - Check console for:
     - "Modal shown, loading conversation for room: X"
     - "Connecting to WebSocket: ws://..."
     - "✅ WebSocket connection established"

3. **As Student:**
   - Open `/chat/`
   - Open the same conversation
   - Send a message

4. **Check Console Logs:**
   - Staff side should show:
     - "📨 WebSocket message received"
     - "=== handleNewMessage START ==="
     - Message details
     - "✅ Added receiver message to chat"

## Common Issues:

1. **WebSocket not connecting:**
   - Check if server is running with `daphne` (not `runserver`)
   - Check browser console for connection errors

2. **Messages received but not displayed:**
   - Check console for "Modal not visible" warnings
   - Check if `chatContainer` is found
   - Check if modal has 'show' class

3. **Room ID mismatch:**
   - Check if `window.currentOpenRoomId` matches message `room_id`





