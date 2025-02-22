

# import json
# import asyncio
# from channels.generic.websocket import AsyncWebsocketConsumer

# # Dictionary to store waiting users for each problem_id (should use Redis in production)
# waiting_users = {}
# active_users = {}  # ✅ Track active users per problem_id
# waiting_locks = asyncio.Lock()  # Prevents race conditions

# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.problem_id = self.scope['url_route']['kwargs']['problem_id']
#         self.username = None
#         self.partner = None  # Store the partner instance

#         await self.accept()  # ✅ Accept the WebSocket connection

#         async with waiting_locks:  
#             # ✅ Ensure active_users is initialized before incrementing
#             if self.problem_id not in active_users:
#                 active_users[self.problem_id] = 0

#             active_users[self.problem_id] += 1  # ✅ Increment active user count

#             if self.problem_id not in waiting_users:
#                 waiting_users[self.problem_id] = []  # Initialize empty list

#             await self.broadcast_user_count()  # ✅ Broadcast updated count

#             # Find a waiting user who is unpaired
#             for i in range(0, len(waiting_users[self.problem_id]), 2):
#                 if len(waiting_users[self.problem_id][i:i+2]) == 1:
#                     # Pair with this waiting user
#                     self.username = "User 2"
#                     self.partner = waiting_users[self.problem_id][i]
#                     waiting_users[self.problem_id].append(self)

#                     # ✅ Establish two-way link
#                     self.partner.partner = self

#                     # Notify both users
#                     await self.partner.send(json.dumps({
#                         'message': "Partner matched! You can start chatting now.",
#                         'username': "System"
#                     }))
#                     await self.send(json.dumps({
#                         'message': "Partner matched! You can start chatting now.",
#                         'username': "System"
#                     }))
#                     break
#             else:
#                 # No available partner, so wait
#                 self.username = "User 1"
#                 waiting_users[self.problem_id].append(self)
#                 await self.send(json.dumps({
#                     'message': "Matching buddy...",
#                     'username': "System"
#                 }))


#     async def disconnect(self, close_code):
#         async with waiting_locks:
#             if self.problem_id in waiting_users and self in waiting_users[self.problem_id]:
#                 waiting_users[self.problem_id].remove(self)

#             # Notify the partner if they exist
#             if self.partner:
#                 try:
#                     await self.partner.send(json.dumps({
#                         'message': "Your partner has disconnected.",
#                         'username': "System"
#                     }))
#                 except Exception:
#                     pass  # Ignore errors if partner already disconnected

#                 self.partner.partner = None  # Remove reference
#                 self.partner = None

#             # Ensure active user count is decremented correctly
#             if self.problem_id in active_users:
#                 active_users[self.problem_id] -= 1
#                 if active_users[self.problem_id] <= 0:
#                     del active_users[self.problem_id]  # Cleanup if no users left

#             await self.broadcast_user_count()  # ✅ Broadcast updated count

#             # If no users left in waiting_users, clean up
#             if self.problem_id in waiting_users and not waiting_users[self.problem_id]:
#                 del waiting_users[self.problem_id]


#     async def receive(self, text_data):
#         data = json.loads(text_data)
#         message = data['message']

#         # ✅ Forward the message to the partner if they exist
#         if self.partner:
#             try:
#                 await self.partner.send(json.dumps({
#                     'message': message,
#                     'username': self.username
#                 }))
#             except Exception:
#                 pass  # ✅ Avoid crash if partner is disconnected

#         # ✅ Also send the message back to the sender so they see it
#         await self.send(json.dumps({
#             'message': message,
#             'username': self.username
#         }))

#     async def broadcast_user_count(self):
#         """ ✅ Added: Broadcast the number of online users for this problem """
#         count = active_users.get(self.problem_id, 0)

#         # ✅ Ensure safe broadcasting (ignore disconnected users)
#         for user in list(waiting_users.get(self.problem_id, [])):
#             try:
#                 await user.send(json.dumps({
#                     'type': 'online_users',
#                     'count': count
#                 }))
#             except Exception:
#                 pass  # ✅ Ignore errors from disconnected clients






















import json
import asyncio
import requests
from channels.generic.websocket import AsyncWebsocketConsumer

waiting_users = {}
active_users = {}
waiting_locks = asyncio.Lock()

def get_leetcode_link(problem_number):
    """Fetches the LeetCode link for the given problem number."""
    url = "https://leetcode.com/api/problems/all/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for question in data["stat_status_pairs"]:
            if question["stat"]["frontend_question_id"] == int(problem_number):
                slug = question["stat"]["question__title_slug"]
                return f"https://leetcode.com/problems/{slug}/"
    return "Problem not found"

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.problem_id = self.scope['url_route']['kwargs']['problem_id']
        self.username = None
        self.partner = None

        await self.accept()

        async with waiting_locks:
            if self.problem_id not in active_users:
                active_users[self.problem_id] = 0
            active_users[self.problem_id] += 1

            if self.problem_id not in waiting_users:
                waiting_users[self.problem_id] = []
            
            # ✅ Get LeetCode link and send as first message
            problem_link = get_leetcode_link(self.problem_id)
            await self.send(json.dumps({
                "message": f"Problem Link: {problem_link}",
                "username": "System"
            }))

            await self.broadcast_user_count()

            for i in range(0, len(waiting_users[self.problem_id]), 2):
                if len(waiting_users[self.problem_id][i:i+2]) == 1:
                    self.username = "User 2"
                    self.partner = waiting_users[self.problem_id][i]
                    waiting_users[self.problem_id].append(self)

                    self.partner.partner = self

                    await self.partner.send(json.dumps({
                        'message': "Partner matched! You can start chatting now.",
                        'username': "System"
                    }))
                    await self.send(json.dumps({
                        'message': "Partner matched! You can start chatting now.",
                        'username': "System"
                    }))
                    break
            else:
                self.username = "User 1"
                waiting_users[self.problem_id].append(self)
                await self.send(json.dumps({
                    'message': "Matching buddy...",
                    'username': "System"
                }))

    async def disconnect(self, close_code):
        async with waiting_locks:
            if self.problem_id in waiting_users and self in waiting_users[self.problem_id]:
                waiting_users[self.problem_id].remove(self)

            if self.partner:
                try:
                    await self.partner.send(json.dumps({
                        'message': "Your partner has disconnected.",
                        'username': "System"
                    }))
                except Exception:
                    pass

                self.partner.partner = None
                self.partner = None

            if self.problem_id in active_users:
                active_users[self.problem_id] -= 1
                if active_users[self.problem_id] <= 0:
                    del active_users[self.problem_id]

            await self.broadcast_user_count()

            if self.problem_id in waiting_users and not waiting_users[self.problem_id]:
                del waiting_users[self.problem_id]

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]

        if self.partner:
            try:
                await self.partner.send(json.dumps({
                    "message": message,
                    "username": self.username
                }))
            except Exception:
                pass

        await self.send(json.dumps({
            "message": message,
            "username": self.username
        }))

    async def broadcast_user_count(self):
        count = active_users.get(self.problem_id, 0)

        for user in list(waiting_users.get(self.problem_id, [])):
            try:
                await user.send(json.dumps({
                    "type": "online_users",
                    "count": count
                }))
            except Exception:
                pass
