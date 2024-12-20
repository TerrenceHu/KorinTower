
from telethon.sync import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import User, Channel
from telethon.errors.rpcerrorlist import InviteRequestSentError, UserAlreadyParticipantError

from telethon import utils

api_id = 25452895
api_hash = "9054a96cc2c5fe1bff6c2aa2c8a85a95"

phone = "+8618600874536"
username = "terrencehu"

client = TelegramClient(username, api_id, api_hash)
client.start()

username = "3G1uBKXJUYhiMjBl"
link = "t.me/+3G1uBKXJUYhiMjBl"
username = "YZM_QZ"

'''
try:
    channel = client.get_entity(username)
    print(channel)
except Exception as e:
    print(f"Failed to get_entity {username}: {e}")
'''


'''
try:
    #client(JoinChannelRequest(channel))
    client(ImportChatInviteRequest(username))
except Exception as e:
    print(f"Failed to join {username}: {e} {type(e)}")
'''


username = "kangmimm"
channel = client.get_entity(username)
try:
    client(JoinChannelRequest(channel))
except InviteRequestSentError as e:
    print(f"Successfully requested to join channel: {username}")
except UserAlreadyParticipantError as e:
    print(f"You are already a participant of channel: {username}")
except Exception as e:
    print(f"Failed to join channel {username}: {e} {type(e)}")
print(channel)

messages = client.iter_messages(channel.id)
for message in messages:
    print(message)
    if message.photo:
        path = message.download_media()
        print('File saved to', path) 