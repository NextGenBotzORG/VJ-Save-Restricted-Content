# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import asyncio
import pyrogram
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, InputMediaPhoto, InputMediaVideo, InputMediaDocument
from config import API_ID, API_HASH, ERROR_MESSAGE
from database.db import db
from TechVJ.strings import HELP_TXT

class batch_temp(object):
    IS_BATCH = {}

async def downstatus(client, statusfile, message, chat):
    while True:
        if os.path.exists(statusfile):
            break
        await asyncio.sleep(3)  
    while os.path.exists(statusfile):  
        with open(statusfile, "r") as downread:  
            txt = downread.read()  
        try:  
            await client.edit_message_text(chat, message.id, f"**Downloaded:** **{txt}**")  
            await asyncio.sleep(10)  
        except:  
            await asyncio.sleep(5)

async def upstatus(client, statusfile, message, chat):
    while True:
        if os.path.exists(statusfile):
            break
        await asyncio.sleep(3)        
    while os.path.exists(statusfile):  
        with open(statusfile, "r") as upread:  
            txt = upread.read()  
        try:  
            await client.edit_message_text(chat, message.id, f"**Uploaded:** **{txt}**")  
            await asyncio.sleep(10)  
        except:  
            await asyncio.sleep(5)

def progress(current, total, message, type):
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")

@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    buttons = [[
        InlineKeyboardButton("❣️ Developer", url="https://t.me/kingvj01")
    ],[
        InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/vj_bot_disscussion'),
        InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/vj_botz')
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await client.send_message(
        chat_id=message.chat.id,
        text=f"<b>👋 Hi {message.from_user.mention}, I am Save Restricted Content Bot, I can send you restricted content by its post link.\n\nFor downloading restricted content /login first.\n\nKnow how to use bot by - /help</b>",
        reply_markup=reply_markup,
        reply_to_message_id=message.id
    )
    return

@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await client.send_message(
        chat_id=message.chat.id,
        text=f"{HELP_TXT}"
    )

@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client: Client, message: Message):
    batch_temp.IS_BATCH[message.from_user.id] = True
    await client.send_message(
        chat_id=message.chat.id,
        text="Batch Successfully Cancelled."
    )

@Client.on_message(filters.text & filters.private)
async def save(client: Client, message: Message):
    if "https://t.me/" not in message.text:
        return
    if batch_temp.IS_BATCH.get(message.from_user.id) == False:
        return await message.reply_text("One Task Is Already Processing. Wait For Complete It. If You Want To Cancel This Task Then Use - /cancel")
    
    datas = message.text.split("/")
    temp = datas[-1].replace("?single", "").split("-")
    fromID = int(temp[0].strip())
    try:
        toID = int(temp[1].strip())
    except:
        toID = fromID
    batch_temp.IS_BATCH[message.from_user.id] = False
    
    # Track processed media groups to avoid duplicates
    processed_groups = set()
    
    for msgid in range(fromID, toID + 1):
        if batch_temp.IS_BATCH.get(message.from_user.id):
            break
        user_data = await db.get_session(message.from_user.id)
        if user_data is None:
            await message.reply("For Downloading Restricted Content You Have To /login First.")
            batch_temp.IS_BATCH[message.from_user.id] = True
            return
        try:
            acc = Client("saverestricted", session_string=user_data, api_hash=API_HASH, api_id=API_ID)
            await acc.connect()
        except:
            batch_temp.IS_BATCH[message.from_user.id] = True
            return await message.reply("Your Login Session Expired. So /logout First Then Login Again By - /login")

        # Private channel
        if "https://t.me/c/" in message.text:
            chatid = int("-100" + datas[4])
            try:
                await handle_private(client, acc, message, chatid, msgid, processed_groups)
            except Exception as e:
                if ERROR_MESSAGE:
                    await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
        
        # Bot
        elif "https://t.me/b/" in message.text:
            username = datas[4]
            try:
                await handle_private(client, acc, message, username, msgid, processed_groups)
            except Exception as e:
                if ERROR_MESSAGE:
                    await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
        
        # Public channel
        else:
            username = datas[3]
            try:
                msg = await client.get_messages(username, msgid)
            except UsernameNotOccupied:
                await client.send_message(message.chat.id, "The username is not occupied by anyone", reply_to_message_id=message.id)
                return
            try:
                await client.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
            except:
                try:
                    await handle_private(client, acc, message, username, msgid, processed_groups)
                except Exception as e:
                    if ERROR_MESSAGE:
                        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
        
        await asyncio.sleep(3)
    batch_temp.IS_BATCH[message.from_user.id] = True

async def handle_private(client: Client, acc, message: Message, chatid, msgid: int, processed_groups: set):
    msg: Message = await acc.get_messages(chatid, msgid)
    if msg.empty:
        return
    msg_type = get_message_type(msg)
    if not msg_type:
        return
    chat = message.chat.id
    if batch_temp.IS_BATCH.get(message.from_user.id):
        return
    
    # Handle media group (album)
    if msg.media_group_id and msg.media_group_id not in processed_groups:
        processed_groups.add(msg.media_group_id)
        media_group = await acc.get_media_group(chatid, msgid)
        media_list = []
        # Search for caption in any message of the media group
        caption = None
        caption_entities = None
        for media_msg in media_group:
            if media_msg.caption:
                caption = media_msg.caption
                caption_entities = media_msg.caption_entities
                break
        
        if caption:
            print(f"Album Caption: {caption}, Entities: {caption_entities}")
        else:
            print("No caption found in media group")
        
        smsg = await client.send_message(message.chat.id, '**Downloading Album**', reply_to_message_id=message.id)
        asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg, chat))
        
        for media_msg in media_group:
            media_type = get_message_type(media_msg)
            print(f"Processing media type: {media_type}")
            try:
                file = await acc.download_media(media_msg, progress=progress, progress_args=[message, "down"])
                if media_type == "Photo":
                    media_item = InputMediaPhoto(
                        file,
                        caption=caption if not media_list else None,
                        caption_entities=caption_entities if not media_list else None,
                        parse_mode=enums.ParseMode.HTML
                    )
                elif media_type == "Video":
                    media_item = InputMediaVideo(
                        file,
                        caption=caption if not media_list else None,
                        caption_entities=caption_entities if not media_list else None,
                        duration=media_msg.video.duration if media_msg.video else 0,
                        width=media_msg.video.width if media_msg.video else 0,
                        height=media_msg.video.height if media_msg.video else 0,
                        parse_mode=enums.ParseMode.HTML
                    )
                elif media_type == "Document":
                    media_item = InputMediaDocument(
                        file,
                        caption=caption if not media_list else None,
                        caption_entities=caption_entities if not media_list else None,
                        parse_mode=enums.ParseMode.HTML
                    )
                else:
                    print(f"Unsupported media type: {media_type}")
                    continue  # Skip unsupported media types
                media_list.append(media_item)
            except Exception as e:
                if ERROR_MESSAGE:
                    await client.send_message(message.chat.id, f"Error downloading media ({media_type}): {e}", reply_to_message_id=message.id)
                print(f"Error downloading media ({media_type}): {e}")
                continue
        
        if os.path.exists(f'{message.id}downstatus.txt'):
            os.remove(f'{message.id}downstatus.txt')
        
        if not media_list or batch_temp.IS_BATCH.get(message.from_user.id):
            await smsg.delete()
            return
        
        asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg, chat))
        try:
            await client.send_media_group(chat, media_list, reply_to_message_id=message.id)
            print("Media group uploaded successfully")
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error uploading album: {e}", reply_to_message_id=message.id)
            print(f"Error uploading album: {e}")
        
        for media in media_list:
            try:
                os.remove(media.media)
            except:
                pass
        if os.path.exists(f'{message.id}upstatus.txt'):
            os.remove(f'{message.id}upstatus.txt')
        await smsg.delete()
        return
    
    # Handle non-album messages
    if msg.media_group_id:
        return  # Skip individual album messages

    if "Text" == msg_type:
        try:
            await client.send_message(chat, msg.text, entities=msg.entities, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
            return
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
            return
    
    smsg = await client.send_message(message.chat.id, '**Downloading**', reply_to_message_id=message.id)
    asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg, chat))
    try:
        file = await acc.download_media(msg, progress=progress, progress_args=[message, "down"])
        os.remove(f'{message.id}downstatus.txt')
    except Exception as e:
        if ERROR_MESSAGE:
            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        return await smsg.delete()
    if batch_temp.IS_BATCH.get(message.from_user.id):
        return
    asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg, chat))
    
    if msg.caption:
        caption = msg.caption
        caption_entities = msg.caption_entities
    else:
        caption = None
        caption_entities = None
    if batch_temp.IS_BATCH.get(message.from_user.id):
        return
    
    if "Document" == msg_type:
        try:
            ph_path = await acc.download_media(msg.document.thumbs[0].file_id)
        except:
            ph_path = None
        try:
            await client.send_document(chat, file, thumb=ph_path, caption=caption, caption_entities=caption_entities, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message, "up"])
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        if ph_path:
            os.remove(ph_path)
    
    elif "Video" == msg_type:
        try:
            ph_path = await acc.download_media(msg.video.thumbs[0].file_id)
        except:
            ph_path = None
        try:
            await client.send_video(chat, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=ph_path, caption=caption, caption_entities=caption_entities, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message, "up"])
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        if ph_path:
            os.remove(ph_path)
    
    elif "Animation" == msg_type:
        try:
            await client.send_animation(chat, file, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
    
    elif "Sticker" == msg_type:
        try:
            await client.send_sticker(chat, file, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
    
    elif "Voice" == msg_type:
        try:
            await client.send_voice(chat, file, caption=caption, caption_entities=caption_entities, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message, "up"])
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
    
    elif "Audio" == msg_type:
        try:
            ph_path = await acc.download_media(msg.audio.thumbs[0].file_id)
        except:
            ph_path = None
        try:
            await client.send_audio(chat, file, thumb=ph_path, caption=caption, caption_entities=caption_entities, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, progress=progress, progress_args=[message, "up"])
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        if ph_path:
            os.remove(ph_path)
    
    elif "Photo" == msg_type:
        try:
            await client.send_photo(chat, file, caption=caption, caption_entities=caption_entities, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            if ERROR_MESSAGE:
                await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
    
    if os.path.exists(f'{message.id}upstatus.txt'):
        os.remove(f'{message.id}upstatus.txt')
    os.remove(file)
    await client.delete_messages(message.chat.id, [smsg.id])

def get_message_type(msg: pyrogram.types.messages_and_media.message.Message):
    try:
        msg.document.file_id
        return "Document"
    except:
        pass
    try:
        msg.video.file_id
        return "Video"
    except:
        pass
    try:
        msg.animation.file_id
        return "Animation"
    except:
        pass
    try:
        msg.sticker.file_id
        return "Sticker"
    except:
        pass
    try:
        msg.voice.file_id
        return "Voice"
    except:
        pass
    try:
        msg.audio.file_id
        return "Audio"
    except:
        pass
    try:
        msg.photo.file_id
        return "Photo"
    except:
        pass
    try:
        msg.text
        return "Text"
    except:
        pass