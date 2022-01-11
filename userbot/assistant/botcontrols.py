import asyncio
from datetime import datetime

from telethon.errors import BadRequestError, FloodWaitError, ForbiddenError

from userbot import iqthon

from ..Config import Config
from ..core.logger import logging
from ..core.managers import edit_delete, edit_or_reply
from ..helpers import reply_id, time_formatter
from ..helpers.utils import _format
from ..sql_helper.bot_blacklists import check_is_black_list, get_all_bl_users
from ..sql_helper.bot_starters import del_starter_from_db, get_all_starters
from ..sql_helper.globals import addgvar, delgvar, gvarstatus
from . import BOTLOG, BOTLOG_CHATID
from .botmanagers import (
    ban_user_from_bot,
    get_user_and_reason,
    progress_str,
    unban_user_from_bot,
)

LOGS = logging.getLogger(__name__)

plugin_category = "bot"
botusername = Config.TG_BOT_USERNAME
cmhd = Config.COMMAND_HAND_LER


@iqthon.iq_cmd(
    pattern=f"^/$",
    from_users=Config.OWNER_ID,
)
async def bot_help(event):
    await event.reply(
        f"""**       :
   :** {botusername}
**1** `/`  +    
           . 
 
**2** `/` 
       .
**3** `/` +     
                 .
**4** `/ ` +     
                  .
**5** `/ ` +   
        .
"""
    )


@iqthon.iq_cmd(
    pattern=f"^/$",
    from_users=Config.OWNER_ID,
)
async def bot_broadcast(event):
    replied = await event.get_reply_message()
    if not replied:
        return await event.reply("**      !**")
    start_ = datetime.now()
    br_cast = await replied.reply("**     **")
    blocked_users = []
    count = 0
    bot_users_count = len(get_all_starters())
    if bot_users_count == 0:
        return await event.reply("**      **")
    users = get_all_starters()
    if users is None:
        return await event.reply("**        **")
    for user in users:
        try:
            await event.client.send_message(
                int(user.user_id), "     ."
            )
            await event.client.send_message(int(user.user_id), replied)
            await asyncio.sleep(0.8)
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
        except (BadRequestError, ValueError, ForbiddenError):
            del_starter_from_db(int(user.user_id))
        except Exception as e:
            LOGS.error(str(e))
            if BOTLOG:
                await event.client.send_message(
                    BOTLOG_CHATID, f"**     **\n`{str(e)}`"
                )
        else:
            count += 1
            if count % 5 == 0:
                try:
                    prog_ = (
                        "**   ..**\n\n"
                        + progress_str(
                            total=bot_users_count,
                            current=count + len(blocked_users),
                        )
                        + f"\n\n**  :**  `{count}`\n"
                        + f"**   : **  `{len(blocked_users)}`"
                    )
                    await br_cast.edit(prog_)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
    end_ = datetime.now()
    b_info = f"      :  <b>{count}    .</b>"
    if len(blocked_users) != 0:
        b_info += f"\n   <b>{len(blocked_users)} </b>       ."
    b_info += (
        f"\n  <code>   : {time_formatter((end_ - start_).seconds)}</code>."
    )
    await br_cast.edit(b_info, parse_mode="html")


@iqthon.iq_cmd(
    pattern=f"^/$",
    command=("bot_users", plugin_category),
    info={
        "header": "To get users list who started bot.",
        "description": "To get compelete list of users who started your bot",
        "usage": "{tr}bot_users",
    },
)
async def ban_starters(event):
    "To get list of users who started bot."
    ulist = get_all_starters()
    if len(ulist) == 0:
        return await edit_delete(event, "**      **")
    msg = "**      :\n\n**"
    for user in ulist:
        msg += f"•  {_format.mentionuser(user.first_name , user.user_id)}\n** :** `{user.user_id}`\n** :** @{user.username}\n** : **__{user.date}__\n\n"
    await edit_or_reply(event, msg)


@iqthon.iq_cmd(
    pattern=f"^/\s+([\s\S]*)",
    from_users=Config.OWNER_ID,
)
async def ban_botpms(event):
    user_id, reason = await get_user_and_reason(event)
    reply_to = await reply_id(event)
    if not user_id:
        return await event.client.send_message(
            event.chat_id, "**       **", reply_to=reply_to
        )
    if not reason:
        return await event.client.send_message(
            event.chat_id, "**          **", reply_to=reply_to
        )
    try:
        user = await event.client.get_entity(user_id)
        user_id = user.id
    except Exception as e:
        return await event.reply(f"**    :**\n`{str(e)}`")
    if user_id == Config.OWNER_ID:
        return await event.reply("**    . **")
    check = check_is_black_list(user.id)
    if check:
        return await event.client.send_message(
            event.chat_id,
            f"** _ :**\
            \n**       **\
            \n**    :** `{check.reason}`\
            \n**   :** `{check.date}`.",
        )
    msg = await ban_user_from_bot(user, reason, reply_to)
    await event.reply(msg)


@iqthon.iq_cmd(
     pattern=f"^/ (?:\s|$)([\s\S]*)",
    from_users=Config.OWNER_ID,
)
async def ban_botpms(event):
    user_id, reason = await get_user_and_reason(event)
    reply_to = await reply_id(event)
    if not user_id:
        return await event.client.send_message(
            event.chat_id, "**       .**", reply_to=reply_to
        )
    try:
        user = await event.client.get_entity(user_id)
        user_id = user.id
    except Exception as e:
        return await event.reply(f"**    :**\n`{str(e)}`")
    check = check_is_black_list(user.id)
    if not check:
        return await event.client.send_message(
            event.chat_id,
            f"**    **\
            \n  {_format.mentionuser(user.first_name , user.id)}       ",
        )
    msg = await unban_user_from_bot(user, reason, reply_to)
    await event.reply(msg)


@iqthon.iq_cmd(
   pattern=f"^/$",
    command=("bblist", plugin_category),
    info={
        "header": "To get users list who are banned in bot.",
        "description": "To get list of users who are banned in bot.",
        "usage": "{tr}bblist",
    },
)
async def ban_starters(event):
    "To get list of users who are banned in bot."
    ulist = get_all_bl_users()
    if len(ulist) == 0:
        return await edit_delete(event, "**         **")
    msg = "**     :\n\n**"
    for user in ulist:
        msg += f"•  {_format.mentionuser(user.first_name , user.chat_id)}\n** :** `{user.chat_id}`\n** :** @{user.username}\n** : **{user.date}\n** :** {user.reason}\n\n"
    await edit_or_reply(event, msg)


@iqthon.iq_cmd(
    pattern=f"^/ (|)$",
    command=("bot_antif", plugin_category),
    info={
        "header": "To enable or disable bot antiflood.",
        "description": "if it was turned on then after 10 messages or 10 edits of same messages in less time then your bot auto loacks them.",
        "usage": [
            "{tr}bot_antif on",
            "{tr}bot_antif off",
        ],
    },
)
async def ban_antiflood(event):
    "To enable or disable bot antiflood."
    input_str = event.pattern_match.group(1)
    if input_str == "":
        if gvarstatus("bot_antif") is not None:
            return await edit_delete(event, "**     **")
        addgvar("bot_antif", True)
        await edit_delete(event, "**     **")
    elif input_str == "":
        if gvarstatus("bot_antif") is None:
            return await edit_delete(event, "**     **")
        delgvar("bot_antif")
        await edit_delete(event, "**     **")