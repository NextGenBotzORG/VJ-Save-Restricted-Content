import os
import asyncio
import pyrogram
from pyrogram import Client, filters, enums
from pyrogram.errors import UsernameNotOccupied
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from TechVJ.strings import HELP_TXT

class batch_temp(object):
    IS_BATCH = {}

# Download and upload progress functions
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

# Start command
@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    buttons = [[
        InlineKeyboardButton("❣️ Developer", url = "https://t.me/kingvj01")
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

# Help command
@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await client.send_message(
        chat_id=message.chat.id, 
        text=f"{HELP_TXT}"
    )

# Save function (Modified for albums)
@Client.on_message(filters.text & filters.private)
async def save(client: Client, message: Message):
    if "https://t.me/" in message.text:
        if batch_temp.IS_BATCH.get(message.from_user.id) == False:
            return await message.reply_text("**One Task Is Already Processing. Wait For Complete It. If You Want To Cancel This Task Then Use - /cancel**")
        datas = message.text.split("/")
        temp = datas[-1].replace("?single","").split("-")
        fromID = int(temp[0].strip())
        try:
            toID = int(temp[1].strip())
        except:
            toID = fromID
        batch_temp.IS_BATCH[message.from_user.id] = False
        for msgid in range(fromID, toID+1):
            if batch_temp.IS_BATCH.get(message.from_user.id): break
            user_data = await db.get_session(message.from_user.id)
            if user_data is None:
                await message.reply("**For Downloading Restricted Content You Have To /login First.**")
                batch_temp.IS_BATCH[message.from_user.id] = True
                return
            try:
                acc = Client("saverestricted", session_string=user_data, api_hash=API_HASH, api_id=API_ID)
                await acc.connect()
            except:
                batch_temp.IS_BATCH[message.from_user.id] = True
                return await message.reply("**Your Login Session Expired. So /logout First Then Login Again By - /login**")

            # Handle media group (album)
            try:
                msg = await client.get_messages(datas[3], msgid)
                if msg.media_group:
                    await handle_album(client, acc, message, datas[3], msgid, msg.media_group)
                else:
                    await handle_single_media(client, acc, message, datas[3], msgid)
            except Exception as e:
                if ERROR_MESSAGE == True:
                    await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

            await asyncio.sleep(3)
        batch_temp.IS_BATCH[message.from_user.id] = True

# Handle media group (album)
async def handle_album(client: Client, acc, message: Message, username: str, msgid: int, media_group: list):
    chat = message.chat.id
    files = []
    caption = None
    
    for msg in media_group:
        if msg.caption:
            caption = msg.caption
        file = await acc.download_media(msg)
        files.append(file)
    
    try:
        await client.send_media_group(chat, files, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        if ERROR_MESSAGE == True:
            await client.send_message(chat, f"Error: {e}", reply_to_message_id=message.id)
    
    # Cleanup downloaded files
    for file in files:
        os.remove(file)

# Handle single media
async def handle_single_media(client: Client, acc, message: Message, username: str, msgid: int):
    msg = await client.get_messages(username, msgid)
    chat = message.chat.id
    file = await acc.download_media(msg)
    
    if msg.caption:
        caption = msg.caption
    else:
        caption = None
    
    try:
        await client.send_document(chat, file, caption=caption, reply_to_message_id=message.id)
    except Exception as e:
        if ERROR_MESSAGE == True:
            await client.send_message(chat, f"Error: {e}", reply_to_message_id=message.id)
    
    os.remove(file)

# Helper to detect media type
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