import html
<<<<<<< HEAD
from contextlib import suppress
from itertools import islice

from pyrogram import Client, filters
from pyrogram.types import Message, MessageEntity, Chat, User
from pyrogram.errors import UsernameNotOccupied, PeerIdInvalid

from SaitamaRobot import PREFIX, DEV_USERS, pyrogram_app
=======
import os
import re
import subprocess

import requests
from telegram import MAX_MESSAGE_LENGTH
from telegram import ParseMode
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.utils.helpers import escape_markdown
from telegram.utils.helpers import mention_html
from telethon import events
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsAdmins

import SaitamaRobot.modules.sql.userinfo_sql as sql
from SaitamaRobot import DEMONS
from SaitamaRobot import DEV_USERS
from SaitamaRobot import dispatcher
from SaitamaRobot import DRAGONS
from SaitamaRobot import INFOPIC
from SaitamaRobot import OWNER_ID
from SaitamaRobot import telethn as SaitamaTelethonClient
from SaitamaRobot import TIGERS
from SaitamaRobot import WOLVES
>>>>>>> parent of b8806b4 (config.yaml)
from SaitamaRobot.__main__ import STATS
from SaitamaRobot.modules.sql import afk_sql


class UserNotChat(Exception):
    """Return Chat if User isn't there"""

    def __init__(self, chat: Chat) -> None:
        self.chat = chat


def username_from_url(url: str):
    if url.startswith("https://t.me/"):
        username = url.removeprefix("https://t.me/")
        if not (username.startswith("joinchat") or username.startswith("+")):
            return f"@{username}"

    elif url.startswith("t.me/"):
        username = url.removeprefix("t.me/")
        if not (username.startswith("joinchat") or username.startswith("+")):
            return f"@{username}"


async def user_from_userid(client: Client, userid: str):
    chat = await client.get_chat(userid)
    if chat.type in frozenset(["bot", "private"]):
        return await client.get_users(chat.id)
    raise UserNotChat(chat)


async def user_from_message(client: Client, msg: Message, limit: int = 1):
    """Get users from message entities and message itself"""

    for entity in islice(
        msg.entities, 1, limit + 1
    ):  # start=1 to avoid bot_command entity, +1 because start=1
        match entity.type:

            case "text_mention":
                yield entity.user

            case "mention":
                username = msg.text[entity.offset : entity.offset + entity.length]
                yield await user_from_userid(client, username)

            case "url":
                user_url = msg.text[entity.offset : entity.offset + entity.length]
                if username := username_from_url(user_url):
                    yield await user_from_userid(client, username)

    for userid in islice(
        msg.text.split(None), 1, limit + 1
    ):  # start=1 to avoid bot_command entity, +1 because start=1
        if (
            userid.startswith("-") and userid.removeprefix("-").isdigit()
        ) or userid.isdigit():
            yield await user_from_userid(client, userid)


async def chat_from_message(client: Client, msg: Message, limit: int = 1):
    """Get chats from message entities and message itself"""
    for entity in islice(
        msg.entities, 1, limit + 1
    ):  # start=1 to avoid bot_command entity, +1 because start=1
        match entity.type:

            case "mention":
                username = msg.text[entity.offset : entity.offset + entity.length]
                yield await client.get_chat(username)

            case "url":
                chat_url = msg.text[entity.offset : entity.offset + entity.length]
                if username := username_from_url(chat_url):
                    yield await client.get_chat(username)

    for chatid in islice(
        msg.text.split(None), 1, limit + 1
    ):  # start=1 to avoid bot_command entity, +1 because start=1
        if (
            chatid.startswith("-") and chatid.removeprefix("-").isdigit()
        ) or chatid.isdigit():
            yield await client.get_chat(chatid)


@pyrogram_app.on_message(filters.command("id", PREFIX))
async def get_id(client: Client, msg: Message) -> None:
    try:
        bot_command = msg.entities[0]

        async for user in user_from_message(client, msg):
            if user:
                await msg.reply_text(
                    f"{user.first_name}'s id is <code>{user.id}</code>"
                )
                break

        else:
            if reply := msg.reply_to_message:

                if sender_name := reply.forward_sender_name:
                    await msg.reply_text(
                        f"{sender_name}'s id is Hidden"
                        f"\n{reply.from_user.first_name}'s id is <code>{reply.from_user.id}</code>"
                    )

                elif user := reply.forward_from:
                    await msg.reply_text(
                        f"{user.first_name}'s id is <code>{user.id}</code>"
                        f"\n{reply.from_user.first_name}'s id is <code>{reply.from_user.id}</code>"
                    )

                else:
                    user = reply.from_user
                    await msg.reply_text(
                        f"{user.first_name}'s id is <code>{user.id}</code>"
                    )

            elif len(msg.text) > bot_command.length:
                await msg.reply_text(f"Invalid input.")
                return

            else:
                await msg.reply_text(f"This group's id is <code>{msg.chat.id}</code>.")

    except UserNotChat as e:
        await msg.reply_text(f"{e.chat.title}'s id is <code>{e.chat.id}</code>")
        return
    except (UsernameNotOccupied, PeerIdInvalid):
        await msg.reply_text(f"Invalid input.")
        return


def ginfo_text(chat: Chat) -> str:
    text = (
        f"<b>ID</b>: <code>{chat.id}</code>"
        f"\n<b>Title</b>: {chat.title}"
        f"\n<b>Type</b>: {chat.type}"
    )

    if chat.username:
        text += f"\n<b>Username</b>: @{chat.username}"
    if chat.invite_link:
        text += f"\n<b>Invitelink</b>: {chat.invite_link}"

    text += (
        f"\n<b>Member Count</b>: {chat.members_count}"
        f"\n<b>Datacenter</b>: {chat.dc_id}"
        f"\n<b>Protected Content</b>: {chat.has_protected_content}"
    )

    if chat.is_verified:
        text += f"\n<b>Verified</b>: {chat.is_verified}"
    if chat.is_restricted:
        text += f"\n<b>Restricted</b>: {chat.is_restricted}"
    if chat.is_scam:
        text += f"\n<b>Scam</b>: {chat.is_scam}"
    if chat.is_fake:
        text += f"\n<b>Fake</b>: {chat.is_fake}"
    if chat.permissions:
        text += f"\n<b>ChatPermissions</b>:\n{chat.permissions}"

    return text


@pyrogram_app.on_message(
    filters.command("ginfo", PREFIX) & filters.user(list(DEV_USERS))
)
async def group_info(client: Client, msg: Message) -> None:
    try:
        bot_command = msg.entities[0]

        async for chat in chat_from_message(client, msg):
            if chat:
                await msg.reply_text(
                    ginfo_text(chat), disable_web_page_preview=True
                )  # Invite links
                break

        else:
            if msg.reply_to_message and msg.reply_to_message.forward_from_chat:
                chat = msg.reply_to_message.forward_from_chat
            elif len(msg.text) > bot_command.length:
                await msg.reply_text(f"Invalid input.")
                return
            else:
                chat = msg.chat

            await msg.reply_text(
                ginfo_text(chat), disable_web_page_preview=True
            )  # Invite links

    except (UsernameNotOccupied, PeerIdInvalid):
        await msg.reply_text("Invalid input.")
        return


def info_text(user: User) -> str:
    text = (
        f"<b>ID</b>: <code>{user.id}</code>"
        f"\n<b>First Name</b>: {html.escape(user.first_name)}"
    )

    if user.last_name:
        text += f"\n<b>Last Name</b>: {html.escape(user.last_name)}"
    if user.username:
        text += f"\n<b>Username</b>: @{html.escape(user.username)}"

    text += (
        f"\n<b>link</b>: {user.mention(style='html')}"
        f"\n<b>AFK</b>: {afk_sql.is_afk(user.id)}"
    )

    return text

<<<<<<< HEAD
=======
        afk_st = is_afk(user.id)
        if afk_st:
            text += _stext.format("AFK")
        else:
            status = status = bot.get_chat_member(chat.id, user.id).status
            if status:
                if status in {"left", "kicked"}:
                    text += _stext.format("Not here")
                elif status == "member":
                    text += _stext.format("Detected")
                elif status in {"administrator", "creator"}:
                    text += _stext.format("Admin")

    disaster_level_present = False

    if user.id == OWNER_ID:
        text += "\n\nThe Disaster level of this person is 'God'."
        disaster_level_present = True
    elif user.id in DEV_USERS:
        text += "\n\nThis user is member of 'Hero Association'."
        disaster_level_present = True
    elif user.id in DRAGONS:
        text += "\n\nThe Disaster level of this person is 'Dragon'."
        disaster_level_present = True
    elif user.id in DEMONS:
        text += "\n\nThe Disaster level of this person is 'Demon'."
        disaster_level_present = True
    elif user.id in TIGERS:
        text += "\n\nThe Disaster level of this person is 'Tiger'."
        disaster_level_present = True
    elif user.id in WOLVES:
        text += "\n\nThe Disaster level of this person is 'Wolf'."
        disaster_level_present = True

    if disaster_level_present:
        text += ' [<a href="https://t.me/OnePunchUpdates/155">?</a>]'.format(
            bot.username
        )
>>>>>>> parent of b8806b4 (config.yaml)

@pyrogram_app.on_message(filters.command("info", PREFIX))
async def info(client: Client, msg: Message) -> None:
    try:
        bot_command = msg.entities[0]

        async for user in user_from_message(client, msg):
            if user:
                await msg.reply_text(info_text(user))
                break

        else:
            if reply := msg.reply_to_message:
                user = reply.from_user
            elif len(msg.text) > bot_command.length:
                await msg.reply_text(f"Invalid input.")
                return
            else:
                user = msg.from_user
            await msg.reply_text(info_text(user))

    except UserNotChat:
        await msg.reply_text("/info doesn't support group/channel.")
    except (UsernameNotOccupied, PeerIdInvalid):
        await msg.reply_text("Invalid input.")


@pyrogram_app.on_message(
    filters.command("stats", PREFIX) & filters.user(list(DEV_USERS))
)
async def stats(_: Client, msg: Message) -> None:
    await msg.reply_text(
        "<b>Current stats:</b>\n" + "\n".join(mod.__stats__() for mod in STATS)
    )


__help__ = """
*ID:*
 • `/id`*:* get the current group id. If used by replying to a message, gets that user's id.
*Overall Information about you:*
 • `/info`*:* get information about a user.

"""


__mod_name__ = "Info"
