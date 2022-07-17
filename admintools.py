__version__ = (1, 0, 9)


# ▄▀█ █▄ █ █▀█ █▄ █ █▀█ ▀▀█ █▀█ █ █ █▀
# █▀█ █ ▀█ █▄█ █ ▀█ ▀▀█   █ ▀▀█ ▀▀█ ▄█
#
#              © Copyright 2022
#
#             developed by @anon97945
#
#          https://t.me/apodiktum_modules
#
# 🔒 Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/gpl-3.0.html

# meta developer: @apodiktum_modules

# scope: hikka_only
# scope: hikka_min 1.1.28

import asyncio
import logging

import contextlib
import collections  # for MigratorClass
import hashlib  # for MigratorClass
import copy     # for MigratorClass

from typing import Union
from datetime import timedelta
from telethon.errors import UserNotParticipantError
from telethon.tl.types import (
    Channel,
    Chat,
    ChatAdminRights,
    Message,
    User,
    ChatBannedRights,
)
from telethon.tl.functions.channels import (
    GetFullChannelRequest,
    EditAdminRequest,
    InviteToChannelRequest,
    EditBannedRequest,
)
from aiogram.types import ChatPermissions
from aiogram.utils.exceptions import (
    MessageCantBeDeleted,
    MessageToDeleteNotFound,
    ChatNotFound,
    BotKicked,
)

from .. import loader, utils

logger = logging.getLogger(__name__)


async def is_linkedchannel(
    user: Union[User, int],
    chat: Union[Chat, int],
    message: Union[None, Message] = None,
):
    if isinstance(user, User):
        return False
    full_chat = await message.client(GetFullChannelRequest(channel=user.id))
    if full_chat.full_chat.linked_chat_id:
        return chat.id == int(full_chat.full_chat.linked_chat_id)


def represents_int(s: str) -> bool:
    try:
        loader.validators.Integer().validate(s)
        return True
    except loader.validators.ValidationError:
        return False


def represents_tgid(s: str) -> bool:
    try:
        loader.validators.TelegramID().validate(s)
        return True
    except loader.validators.ValidationError:
        return False


def to_bool(value: str) -> bool:
    try:
        loader.validators.Boolean().validate(value)
        if value.lower() in "true":
            return True
        return False
    except loader.validators.ValidationError:
        return None


@loader.tds
class ApodiktumAdminToolsMod(loader.Module):
    """
    Toolpack for Channel and Group Admins.
    """
    strings = {
        "name": "Apo AdminTools",
        "developer": "@anon97945",
        "bcu_db_string": ("<b>[BlockChannelUser]</b> Current Database:\n\nWatcher:\n{}"
                          "\n\nChatsettings:\n{}"),
        "bcu_settings": ("<b>[BlockChannelUser]</b> Current settings in this "
                         "chat are:\n{}"),
        "bcu_start": "<b>[BlockChannelUser]</b> Activated in this chat.</b>",
        "bcu_stopped": "<b>[BlockChannelUser]</b> Deactivated in this chat.</b>",
        "bcu_triggered": "{}, you can't write as a channel here.",
        "bcu_turned_off": "<b>[BlockChannelUser]</b> The module is now turned off in all chats.</b>",
        "bnd_db_string": ("<b>[BlockNonDiscussion]</b> Current Database:\n\nWatcher:\n{}"
                          "\n\nChatsettings:\n{}"),
        "bnd_settings": ("<b>[BlockNonDiscussion]</b> Current settings in this "
                         "chat are:\n{}"),
        "bnd_start": "<b>[BlockNonDiscussion]</b> Activated in this chat.</b>",
        "bnd_stopped": "<b>[BlockNonDiscussion]</b> Deactivated in this chat.</b>",
        "bnd_triggered": ("{}, the comments are limited to discussiongroup members, "
                          "please join our discussiongroup first."
                          "\n\n👉🏻 {}\n\nRespectfully, the admins."),
        "bnd_turned_off": "<b>[BlockNonDiscussion]</b> The module is now turned off in all chats.</b>",
        "error": "<b>Your command was wrong.</b>",
        "gl_db_string": ("<b>[Grouplogger]</b> Current Database:\n\nWatcher:\n{}"
                         "\n\nChatsettings:\n{}"),
        "gl_settings": ("<b>[Grouplogger]</b> Current settings in this "
                        "chat are:\n{}"),
        "gl_start": "<b>[Grouplogger]</b> Activated for the given chat.</b>",
        "gl_stopped": "<b>[Grouplogger]</b> Deactivated in this chat.</b>",
        "gl_turned_off": "<b>[Grouplogger]</b> The module is now turned off in all chats.</b>",
        "no_id": "<b>Your input was no TG ID.</b>",
        "no_int": "<b>Your input was no Integer.</b>",
        "not_dc": "<b>This is no Groupchat.</b>",
        "permerror": "<b>You have no delete permissions in this chat.</b>",
    }

    strings_en = {
        "bcu_db_string": ("<b>[BlockChannelUser]</b> Current Database:\n\nWatcher:\n{}"
                          "\n\nChatsettings:\n{}"),
        "bcu_settings": ("<b>[BlockChannelUser]</b> Current settings in this "
                         "chat are:\n{}"),
        "bcu_start": "<b>[BlockChannelUser]</b> Activated in this chat.</b>",
        "bcu_stopped": "<b>[BlockChannelUser]</b> Deactivated in this chat.</b>",
        "bcu_triggered": "{}, you can't write as a channel here.",
        "bcu_turned_off": "<b>[BlockChannelUser]</b> The module is now turned off in all chats.</b>",
        "bnd_db_string": ("<b>[BlockNonDiscussion]</b> Current Database:\n\nWatcher:\n{}"
                          "\n\nChatsettings:\n{}"),
        "bnd_settings": ("<b>[BlockNonDiscussion]</b> Current settings in this "
                         "chat are:\n{}"),
        "bnd_start": "<b>[BlockNonDiscussion]</b> Activated in this chat.</b>",
        "bnd_stopped": "<b>[BlockNonDiscussion]</b> Deactivated in this chat.</b>",
        "bnd_triggered": ("{}, the comments are limited to discussiongroup members, "
                          "please join our discussiongroup first."
                          "\n\n👉🏻 {}\n\nRespectfully, the admins."),
        "bnd_turned_off": "<b>[BlockNonDiscussion]</b> The module is now turned off in all chats.</b>",
        "error": "<b>Your command was wrong.</b>",
        "gl_db_string": ("<b>[Grouplogger]</b> Current Database:\n\nWatcher:\n{}"
                         "\n\nChatsettings:\n{}"),
        "gl_settings": ("<b>[Grouplogger]</b> Current settings in this "
                        "chat are:\n{}"),
        "gl_start": "<b>[Grouplogger]</b> Activated for the given chat.</b>",
        "gl_stopped": "<b>[Grouplogger]</b> Deactivated in this chat.</b>",
        "gl_turned_off": "<b>[Grouplogger]</b> The module is now turned off in all chats.</b>",
        "no_id": "<b>Your input was no TG ID.</b>",
        "no_int": "<b>Your input was no Integer.</b>",
        "not_dc": "<b>This is no Groupchat.</b>",
        "permerror": "<b>You have no delete permissions in this chat.</b>",
    }

    strings_de = {
        "_cls_doc": "Toolpack für Kanal- und Gruppenadministratoren.",
        "bcu_db_string": ("<b>[BlockChannelUser]</b> Aktuelle Datenbank:\n\nWatcher:\n{}"
                          "\n\nChateinstellungen:\n{}"),
        "bcu_settings": ("<b>[BlockChannelUser]</b> Aktuelle Einstellungen in diesem "
                         "Chat:\n{}"),
        "bcu_start": "<b>[BlockChannelUser]</b> In diesem Chat aktiviert.</b>",
        "bcu_stopped": "<b>[BlockChannelUser]</b> Der Chat wurde aus der Liste entfernt.</b>",
        "bcu_triggered": "{}, du kannst hier nicht als Kanal schreiben.",
        "bcu_turned_off": "<b>[BlockChannelUser]</b> In allen Chats ausgeschaltet.</b>",
        "bnd_db_string": ("<b>[BlockNonDiscussion - Settings]</b> Aktuelle Datenbank:\n\nWatcher:\n{}"
                          "\n\nChateinstellungen:\n{}"),
        "bnd_settings": ("<b>[BlockNonDiscussion - Settings]</b> Aktuelle Einstellungen in diesem "
                         "Chat:\n{}"),
        "bnd_start": "<b>[BlockNonDiscussion]</b> In diesem Chat aktiviert.</b>",
        "bnd_stopped": "<b>[BlockNonDiscussion]</b> Der Chat wurde aus der Liste entfernt.</b>",
        "bnd_triggered": ("{}, die Kommentarfunktion wurde auf die Chatmitglieder begrenzt, "
                          "tritt bitte zuerst unserem Chat bei."
                          "\n\n👉🏻 {}\n\nHochachtungsvoll, die Obrigkeit."),
        "bnd_turned_off": "<b>[BlockNonDiscussion]</b> In allen Chats ausgeschaltet.</b>",
        "error": "<b>Dein Befehl war falsch.</b>",
        "gl_db_string": ("<b>[Grouplogger]</b> Aktuelle Datenbank:\n\nWatcher:\n{}"
                         "\n\nChateinstellungen:\n{}"),
        "gl_settings": ("<b>[Grouplogger]</b> Aktuelle Einstellungen in diesem "
                        "Chat:\n{}"),
        "gl_start": "<b>[Grouplogger]</b> In gewähltem Chat aktiviert.</b>",
        "gl_stopped": "<b>[Grouplogger]</b> Der Chat wurde aus der Liste entfernt.</b>",
        "gl_turned_off": "<b>[Grouplogger]</b> In allen Chats ausgeschaltet.</b>",
        "no_id": "<b>Ihre Eingabe war keine TG ID.</b>",
        "no_int": "<b>Ihre Eingabe war keine Integer.</b>",
        "not_dc": "<b>Dies ist kein Gruppenchat.</b>",
        "permerror": "<b>Sie haben in diesem Chat keine Löschberechtigung.</b>",
        "_cfg_cst_auto_migrate": "Wheather to auto migrate defined changes on startup.",
        "_cfg_cst_auto_migrate_log": "Wheather log auto migrate as info(True) or debug(False).",
        "_cfg_cst_auto_migrate_debug": "Wheather log debug messages of auto migrate.",
    }

    strings_ru = {
        "_cls_doc": "Пакет инструментов для администраторов каналов и групп.",
        "_cmd_doc_bcu": (" ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬\n"
                         " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Переключает BlockChannelUser для текущего чата.\n"
                         ".bcu notify <true/false>\n"
                         " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Переключает уведомление.\n"
                         ".bcu ban <true/false>\n"
                         " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Банит канал.\n"
                         ".bcu deltimer <секунды/или 0>\n"
                         " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Удаляет уведомление в считанные секунды. 0, чтобы отключить.\n"
                         ".bcu settings\n"
                         " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Показывает текущую конфигурацию чата.\n"
                         ".bcu db\n"
                         " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Показывает текущую базу данных.\n"
                         ".bcu clearall\n"
                         " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Очищает базу данных от BlockChannelUser.\n"),

        "_cmd_doc_bnd": (" ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬\n"
                         " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Переключает BlockNonDiscussion для текущего чата.\n"
                         ".bnd notify <true/false>\n"
                         " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Переключает уведомление.\n"
                         ".bnd mute <минут/или 0>\n"
                         " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Заглушает пользователя на Х минут. 0 чтобы отключить.\n"
                         ".bnd deltimer <секунды/или 0>\n"
                         " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Удаляет уведомление в считанные секунды. 0 чтобы отключить.\n"
                         ".bnd settings\n"
                         " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Показывает текущую конфигурацию чата.\n"
                         ".bnd db\n"
                         " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Показывает текущую базу данных.\n"
                         ".bnd clearall\n"
                         " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Очищает базу данных от BlockNonDiscussion.\n"),

        "_cmd_doc_gl": ("⁭⁫⁪⁫⁬⁭⁫⁪<chatid> <logchannelid>\n"
                        " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Регистрирует групповой чат на данном канале.\n"
                        ".gl rem <chatid>\n"
                        " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Удаляет данный чат из наблюдателя.\n"
                        ".gl db\n"
                        " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Показываеттекущую базу данных.\n"
                        ".gl settings\n"
                        " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Показывает текущую конфигурацию чата.\n"
                        ".gl clearall\n"
                        " ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Очищает базу данных от Group/Channel Logger.\n"),
        "bcu_db_string": ("<b>[BlockChannelUser]</b> Текущая база данных:\n\nНаблюдающий:\n{}"
                          "\n\nНастройки чата:\n{}"),
        "bcu_settings": ("<b>[BlockChannelUser]</b> Текущие настройки "
                         "в этом чате:\n{}"),
        "bcu_start": "<b>[BlockChannelUser]</b> Активировано в этом чате</b>",
        "bcu_stopped": "<b>[BlockChannelUser]</b> Деактивировано в этом чате</b>",
        "bcu_triggered": "{}, ты не можешь писать тут от имени канала.",
        "bcu_turned_off": "<b>[BlockChannelUser]</b> Теперь этот модуль выключен во всех чатах</b>",
        "bnd_db_string": ("<b>[BlockNonDiscussion]</b> Текущая база данных:\n\nНаблюдающий:\n{}"
                          "\n\nНастройки чата:\n{}"),
        "bnd_settings": ("<b>[BlockNonDiscussion]</b> Текущие настройки "
                         "в этом чате:\n{}"),
        "bnd_start": "<b>[BlockNonDiscussion]</b> Активировано в этом чате</b>",
        "bnd_stopped": "<b>[BlockNonDiscussion]</b> Деактивировано в этом чате</b>",
        "bnd_triggered": ("{}, комментарии ограничены для участников группы обсуждения, "
                          "Пожалуйста, для начала присоединитесь к нашей группе обсуждения."
                          "\n\n👉🏻 {}\n\nС уважением, администраторы."),
        "bnd_turned_off": "<b>[BlockNonDiscussion]</b> Теперь этот модуль выключен во всех чатах</b>",
        "error": "<b>Неверная команда</b>",
        "gl_db_string": ("<b>[Grouplogger]</b> Текущая база данных:\n\nНаблюдающий:\n{}"
                         "\n\nНастройки чата:\n{}"),
        "gl_settings": ("<b>[Grouplogger]</b> Текущие настройки "
                        "в этом чате:\n{}"),
        "gl_start": "<b>[Grouplogger]</b> Активирован в выбранном чате.</b>",
        "gl_stopped": "<b>[Grouplogger]</b> Деактивировано в этом чате.</b>",
        "gl_turned_off": "<b>[Grouplogger]</b> Теперь этот модуль выключен во всех чатах.</b>",
        "no_id": "<b>Ты ввёл не телеграм айди.</b>",
        "no_int": "<b>Ваш ввод не является целочисленным типом (int)</b>",
        "not_dc": "<b>Это не групповой чат</b>",
        "permerror": "<b>Вы не имеете права на удаление сообщений в этом чате</b>",
    }

    _global_queue = []

    def __init__(self):
        self._ratelimit = []
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "auto_migrate",
                True,
                doc=lambda: self.strings("_cfg_cst_auto_migrate"),
                validator=loader.validators.Boolean(),
            ),  # for MigratorClass
            loader.ConfigValue(
                "auto_migrate_log",
                True,
                doc=lambda: self.strings("_cfg_cst_auto_migrate_log"),
                validator=loader.validators.Boolean(),
            ),  # for MigratorClass
            loader.ConfigValue(
                "auto_migrate_debug",
                False,
                doc=lambda: self.strings("_cfg_cst_auto_migrate_debug"),
                validator=loader.validators.Boolean(),
            ),  # for MigratorClass
        )

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self.base_strings = self.strings._base_strings
        self._pt_task = asyncio.ensure_future(self._global_queue_handler())
        # MigratorClass
        self._migrator = MigratorClass()  # MigratorClass define
        await self._migrator.init(client, db, self, self.__class__.__name__, self.strings("name"), self.config["auto_migrate_log"], self.config["auto_migrate_debug"])  # MigratorClass Initiate
        await self._migrator.auto_migrate_handler(self.config["auto_migrate"])
        # MigratorClass

    async def on_unload(self):
        self._pt_task.cancel()
        return

    def _strings(self, string: str, chat_id: int = None):
        if self.lookup("Apo-Translations") and chat_id:
            forced_translation_db = self.lookup("Apo-Translations").config
            strings_en = self.strings_en if getattr(self, "strings_en", False) else {}
            strings_de = self.strings_de if getattr(self, "strings_de", False) else {}
            strings_ru = self.strings_ru if getattr(self, "strings_ru", False) else {}
            languages = {
                "en_chats": {**self.base_strings, **strings_en},
                "de_chats": {**self.base_strings, **strings_de},
                "ru_chats": {**self.base_strings, **strings_ru},
            }
            for lang, strings in languages.items():
                if chat_id in forced_translation_db[lang]:
                    if string in strings:
                        return strings[string]
                    logger.debug(f"String: {string} not found in\n{strings}")
                    break
        return self.strings(string)

    async def _mute(
        self,
        chat: Union[Chat, int],
        user: Union[User, int],
        message: Union[None, Message] = None,
        MUTETIMER: int = 0,
        UseBot: bool = False,
    ):
        if UseBot:
            with contextlib.suppress(Exception):
                await self.inline.bot.restrict_chat_member(
                    int(f"-100{getattr(chat, 'id', chat)}"),
                    user.id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=timedelta(minutes=MUTETIMER),
                )
                return
        await message.client.edit_permissions(chat.id, user.id,
                                              timedelta(minutes=MUTETIMER), send_messages=False)
        return

    async def _ban(
        self,
        chat: Union[Chat, int],
        user: Union[User, int],
        message: Union[None, Message] = None,
        UseBot: bool = False,
    ):
        if UseBot:
            with contextlib.suppress(Exception):
                if isinstance(user, Channel):
                    return await self.inline.bot.ban_chat_sender_chat(
                        int(f"-100{getattr(chat, 'id', chat)}"),
                        f"-100{user.id}",
                    )
                return await self.inline.bot.kick_chat_member(
                    int(f"-100{getattr(chat, 'id', chat)}"),
                    user.id,
                )
        await message.client(EditBannedRequest(chat.id, user.id, ChatBannedRights(until_date=None, view_messages=True)))

    async def _delete_message(
        self,
        chat: Union[Chat, int],
        message: Union[None, Message] = None,
        UseBot: bool = False,
    ):
        chat_id = getattr(chat, 'id', chat)
        if UseBot:
            try:
                await self.inline.bot.delete_message(
                    int(f"-100{chat_id}"),
                    message.id,
                )
                return
            except MessageToDeleteNotFound:
                pass
            except (MessageCantBeDeleted, BotKicked, ChatNotFound):
                pass
        return await message.delete()

    async def _promote_bot(
        self,
        chat_id: Union[Chat, int],
    ):
        try:
            await self._client(InviteToChannelRequest(chat_id, [self.inline.bot_username]))
        except Exception:
            logger.debug(f"Unable to invite cleaner to {chat_id}. Maybe he's already there?")

        try:
            await self._client(
                EditAdminRequest(
                    channel=chat_id,
                    user_id=self.inline.bot_username,
                    admin_rights=ChatAdminRights(
                        ban_users=True, delete_messages=True
                    ),
                    rank="Bot",
                )
            )
            return True
        except Exception:
            logger.debug(f"Cleaner promotion in chat {chat_id} failed!")
            return False

    async def _check_inlinebot(
        self,
        chat: Union[Chat, int],
        inline_bot_id: Union[None, int],
        self_id: Union[None, int],
        message: Union[None, Message] = None,
    ):
        chat_id = getattr(chat, 'id', chat)
        if chat_id != self_id:
            try:
                bot_perms = await message.client.get_permissions(chat_id, inline_bot_id)
                if bot_perms.is_admin and bot_perms.ban_users and bot_perms.delete_messages:
                    return True
                if await self._promote_bot(chat_id):
                    return True
                return False
            except UserNotParticipantError:
                return bool(chat.admin_rights.add_admins and await self._promote_bot(chat_id))

    @staticmethod
    async def _is_member(
        chat: Union[Chat, int],
        user: Union[User, int],
        self_id: Union[None, int],
        message: Union[None, Message] = None,
    ):
        if chat != self_id:
            try:
                await message.client.get_permissions(chat, user)
                return True
            except UserNotParticipantError:
                return False

    @staticmethod
    def _get_tag(
        user: Union[User, int],
        WithID: bool = False,
    ):
        if isinstance(user, Channel):
            if WithID:
                return (f"<a href=tg://resolve?domain={user.username}>{user.title}</a> (<code>{str(user.id)}</code>)"
                        if user.username
                        else f"{user.title}(<code>{str(user.id)}</code>)")
            return (f"<a href=tg://resolve?domain={user.username}>{user.title}</a>"
                    if user.username
                    else f"{user.title}")
        if WithID:
            return (f"<a href=tg://resolve?domain={user.username}>{user.first_name}</a> (<code>{str(user.id)}</code>)"
                    if user.username
                    else f"<a href=tg://user?id={str(user.id)}>{user.first_name}</a> (<code>{str(user.id)}</code>)")
        return (f"<a href=tg://resolve?domain={user.username}>{user.first_name}</a>"
                if user.username
                else f"<a href=tg://user?id={str(user.id)}>{user.first_name}</a>")

    @staticmethod
    async def _get_invite_link(
        chat: Union[Chat, int],
        message: Union[None, Message] = None,
    ):
        if chat.username:
            link = f"https://t.me/{chat.username}"
        elif chat.admin_rights.invite_users:
            link = await message.client(GetFullChannelRequest(channel=chat.id))
            link = link.full_chat.exported_invite.link
        else:
            link = ""
        return link

    async def bndcmd(self, message: Message):
        """
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Toggles BlockNonDiscussion for the current chat.
        .bnd notify <true/false>
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Toggles the notification message.
        .bnd mute <minutes/or 0>
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Mutes the user for x minutes. 0 to disable.
        .bnd deltimer <seconds/or 0>
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Deletes the notification message in seconds. 0 to disable.
        .bnd settings
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Shows the current configuration of the chat.
        .bnd db
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Shows the current database.
        .bnd clearall
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Clears the db of BlockNonDiscussion.
        """
        bnd = self.get("bnd", [])
        sets = self.get("bnd_sets", {})
        args = utils.get_args_raw(message).lower()
        args = str(args).split()
        chat = await self._client.get_entity(message.chat)
        chatid = chat.id
        chatid_str = str(chatid)

        if args and args[0] == "clearall":
            self.set("bnd", [])
            self.set("bnd_sets", {})
            return await utils.answer(message, self._strings("bnd_turned_off", utils.get_chat_id(message)))

        if args and args[0] == "db":
            return await utils.answer(message, self._strings("bnd_db_string", utils.get_chat_id(message)).format(str(bnd), str(sets)))

        if message.is_private:
            await utils.answer(message, self._strings("not_dc"))
            return

        if (
            (chat.admin_rights or chat.creator)
            and not chat.admin_rights.delete_messages
            or not chat.admin_rights
            and not chat.creator
        ):
            return await utils.answer(message, self._strings("permerror", utils.get_chat_id(message)))

        if not args:
            if chatid_str not in bnd:
                bnd.append(chatid_str)
                sets.setdefault(chatid_str, {})
                sets[chatid_str].setdefault("notify", True)
                sets[chatid_str].setdefault("mute", 1)
                sets[chatid_str].setdefault("deltimer", 60)
                self.set("bnd", bnd)
                self.set("bnd_sets", sets)
                return await utils.answer(message, self._strings("bnd_start", utils.get_chat_id(message)))
            bnd.remove(chatid_str)
            sets.pop(chatid_str)
            self.set("bnd", bnd)
            self.set("bnd_sets", sets)
            return await utils.answer(message, self._strings("bnd_stopped", utils.get_chat_id(message)))

        if chatid_str in bnd:
            if args[0] == "notify" and args[1] is not None:
                if not isinstance(to_bool(args[1]), bool):
                    return await utils.answer(message, self._strings("error", utils.get_chat_id(message)))
                sets[chatid_str].update({"notify": to_bool(args[1])})
            elif args[0] == "mute" and args[1] is not None and chatid_str in bnd:
                if not represents_int(args[1]):
                    return await utils.answer(message, self._strings("no_int", utils.get_chat_id(message)))
                sets[chatid_str].update({"mute": args[1].capitalize()})
            elif args[0] == "deltimer" and args[1] is not None and chatid_str in bnd:
                if not represents_int(args[1]):
                    return await utils.answer(message, self._strings("no_int", utils.get_chat_id(message)))
                sets[chatid_str].update({"deltimer": args[1]})
            elif args[0] != "settings" and chatid_str in bnd:
                return
            self.set("bnd", bnd)
            self.set("bnd_sets", sets)
            return await utils.answer(message, self._strings("bnd_settings", utils.get_chat_id(message)).format(str(sets[chatid_str])))

    async def bcucmd(self, message: Message):
        """
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Toggles BlockChannelUser for the current chat.
        .bcu notify <true/false>
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Toggles the notification message.
        .bcu ban <true/false>
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Bans the channel.
        .bcu deltimer <seconds/or 0>
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Deletes the notification message in seconds. 0 to disable.
        .bcu settings
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Shows the current configuration of the chat.
        .bcu db
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Shows the current database.
        .bcu clearall
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Clears the db of BlockChannelUser.
        """
        bcu = self.get("bcu", [])
        sets = self.get("bcu_sets", {})
        args = utils.get_args_raw(message).lower()
        args = str(args).split()
        chat = await self._client.get_entity(message.chat)
        chatid = chat.id
        chatid_str = str(chatid)

        if args and args[0] == "clearall":
            self.set("bcu", [])
            self.set("bcu_sets", {})
            return await utils.answer(message, self._strings("bcu_turned_off", utils.get_chat_id(message)))

        if args and args[0] == "db":
            return await utils.answer(message, self._strings("bcu_db_string", utils.get_chat_id(message)).format(str(bcu), str(sets)))

        if message.is_private:
            await utils.answer(message, self._strings("not_dc", utils.get_chat_id(message)))
            return

        if (
            (chat.admin_rights or chat.creator)
            and not chat.admin_rights.delete_messages
            or not chat.admin_rights
            and not chat.creator
        ):
            return await utils.answer(message, self._strings("permerror", utils.get_chat_id(message)))

        if not args:
            if chatid_str not in bcu:
                bcu.append(chatid_str)
                sets.setdefault(chatid_str, {})
                sets[chatid_str].setdefault("notify", True)
                sets[chatid_str].setdefault("ban", True)
                sets[chatid_str].setdefault("deltimer", 60)
                self.set("bcu", bcu)
                self.set("bcu_sets", sets)
                return await utils.answer(message, self._strings("bcu_start", utils.get_chat_id(message)))
            bcu.remove(chatid_str)
            sets.pop(chatid_str)
            self.set("bcu", bcu)
            self.set("bcu_sets", sets)
            return await utils.answer(message, self._strings("bcu_stopped", utils.get_chat_id(message)))

        if chatid_str in bcu:
            if args[0] == "notify" and args[1] is not None:
                if not isinstance(to_bool(args[1]), bool):
                    return await utils.answer(message, self._strings("error", utils.get_chat_id(message)))
                sets[chatid_str].update({"notify": to_bool(args[1])})
            elif args[0] == "ban" and args[1] is not None and chatid_str in bcu:
                if not isinstance(to_bool(args[1]), bool):
                    return await utils.answer(message, self._strings("no_int", utils.get_chat_id(message)))
                sets[chatid_str].update({"ban": to_bool(args[1])})
            elif args[0] == "deltimer" and args[1] is not None and chatid_str in bcu:
                if not represents_int(args[1]):
                    return await utils.answer(message, self._strings("no_int", utils.get_chat_id(message)))
                sets[chatid_str].update({"deltimer": args[1]})
            elif args[0] != "settings" and chatid_str in bcu:
                return
            self.set("bcu", bcu)
            self.set("bcu_sets", sets)
            return await utils.answer(message, self._strings("bcu_settings", utils.get_chat_id(message)).format(str(sets[chatid_str])))

    async def glcmd(self, message: Message):
        """
        <chatid> <logchannelid>
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Logs given groupchat in given channel.
        .gl rem <chatid>
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Removes given chat from watcher.
        .gl db
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Shows the current database.
        .gl settings
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Shows the current configuration of the chat.
        .gl clearall
         ⁭⁫⁪⁫⁬⁭⁫⁪⁭⁫⁪⁫⁬⁭⁫⁪⁫⁬  - Clears the db of Group/Channel Logger.
        """
        gl = self.get("gl", [])
        sets = self.get("gl_sets", {})
        args = utils.get_args_raw(message).lower()
        args = str(args).split()
        chat = await self._client.get_entity(message.chat)
        chatid = chat.id
        chatid_str = str(chatid)

        if not args:
            return await utils.answer(message, self._strings("error", utils.get_chat_id(message)))

        if args[0] == "clearall":
            self.set("gl", [])
            self.set("gl_sets", {})
            return await utils.answer(message, self._strings("gl_turned_off", utils.get_chat_id(message)))
        if args[0] == "db":
            return await utils.answer(message, self._strings("gl_db_string", utils.get_chat_id(message)).format(str(gl), str(sets)))
        if args[0] is not None and represents_tgid(args[0]):
            chatid = args[0]
            chatid_str = str(chatid)
        elif args[0] == "rem":
            chatid = args[1]
            chatid_str = str(chatid)
        elif args[0] == "db":
            return await utils.answer(message, self._strings("gl_db_string", utils.get_chat_id(message)).format(str(sets)))
        elif args[0] not in ["clearall", "settings"]:
            return await utils.answer(message, self._strings("error", utils.get_chat_id(message)))
        elif not args:
            return await utils.answer(message, self._strings("error", utils.get_chat_id(message)))
        if args[0] == "rem" and represents_tgid(args[1]) and chatid_str in gl:
            gl.remove(chatid_str)
            sets.pop(chatid_str)
            self.set("gl", gl)
            self.set("gl_sets", sets)
            return await utils.answer(message, self._strings("gl_stopped", utils.get_chat_id(message)))
        if args[0] == "rem" and (represents_tgid(args[1]) or chatid_str not in gl):
            return await utils.answer(message, self._strings("error", utils.get_chat_id(message)))
        if not represents_tgid(chatid_str):
            return await utils.answer(message, self._strings("error", utils.get_chat_id(message)))
        if chatid_str not in gl:
            if not represents_tgid(args[0]) or not represents_tgid(args[1]):
                return await utils.answer(message, self._strings("no_id", utils.get_chat_id(message)))
            gl.append(chatid_str)
            sets.setdefault(chatid_str, {})
            sets[chatid_str].setdefault("logchannel", args[1])
            self.set("gl", gl)
            self.set("gl_sets", sets)
            return await utils.answer(message, self._strings("gl_start", utils.get_chat_id(message)))
        if len(args) == 2:
            if not represents_tgid(args[0]) or not represents_tgid(args[1]):
                return await utils.answer(message, self._strings("no_id", utils.get_chat_id(message)))
            sets[chatid_str].update({"logchannel": args[1]})
        elif args[0] != "settings" and chatid_str in gl:
            return
        self.set("gl", gl)
        self.set("gl_sets", sets)
        return await utils.answer(message, self._strings("gl_settings", utils.get_chat_id(message)).format(str(sets[chatid_str])))

    async def p__bcu(
        self,
        chat: Union[Chat, int],
        user: Union[User, int],
        message: Union[None, Message] = None,
        bcu: list = None,
        bcu_sets: dict = None,
    ) -> bool:
        chatid_str = str(chat.id)
        if message.is_private or chatid_str not in bcu or not isinstance(user, Channel):
            return
        UseBot = await self._check_inlinebot(chat, self.inline.bot_id, self._tg_id, message)
        if (
            (chat.admin_rights or chat.creator)
            and (not chat.admin_rights.delete_messages
                 or not chat.admin_rights)
        ):
            return
        usertag = self._get_tag(user, True)

        if await is_linkedchannel(user, chat, message):
            return
        await self._delete_message(chat, message, UseBot)
        if bcu_sets[chatid_str].get("ban") is True:
            await self._ban(chat, user, message, UseBot)
        if bcu_sets[chatid_str].get("notify") is True:
            msgs = await utils.answer(message, self._strings("bcu_triggered", utils.get_chat_id(message)).format(usertag))
            if bcu_sets[chatid_str].get("deltimer") != "0":
                DELTIMER = int(bcu_sets[chatid_str].get("deltimer"))
                await asyncio.sleep(DELTIMER)
                await self._delete_message(chat, msgs, UseBot)
        return

    async def p__bnd(
        self,
        chat: Union[Chat, int],
        user: Union[User, int],
        message: Union[None, Message] = None,
        bnd: list = None,
        bnd_sets: dict = None,
    ) -> bool:
        chatid_str = str(chat.id)
        if message.is_private or chatid_str not in bnd or not isinstance(user, User):
            return
        if (
            (chat.admin_rights or chat.creator)
            and (not chat.admin_rights.delete_messages
                 or not chat.admin_rights)
        ):
            return
        usertag = self._get_tag(user, True)
        link = await self._get_invite_link(chat, message)

        if not await self._is_member(chat.id, user.id, self._tg_id, message):
            UseBot = await self._check_inlinebot(chat, self.inline.bot_id, self._tg_id, message)
            await self._delete_message(chat, message, UseBot)
            if (
                chat.admin_rights.ban_users
                and bnd_sets[chatid_str].get("mute") is not None
                and bnd_sets[chatid_str].get("mute") != "0"
            ):
                MUTETIMER = bnd_sets[chatid_str].get("mute")
                await self._mute(chat, user, message, MUTETIMER, UseBot)
            if bnd_sets[chatid_str].get("notify") is True:
                msgs = await utils.answer(message, self._strings("bnd_triggered", utils.get_chat_id(message)).format(usertag, link))
                if bnd_sets[chatid_str].get("deltimer") != "0":
                    DELTIMER = int(bnd_sets[chatid_str].get("deltimer"))
                    await asyncio.sleep(DELTIMER)
                    await self._delete_message(chat, msgs, UseBot)
        return

    async def p__gl(
        self,
        chat: Union[Chat, int],
        user: Union[User, int],
        message: Union[None, Message] = None,
        gl: list = None,
        gl_sets: dict = None,
    ) -> bool:
        chatid_str = str(chat.id)
        if message.is_private or chatid_str not in gl:
            return
        logchan_id = int(gl_sets[chatid_str].get("logchannel"))
        chat_tag = self._get_tag(chat, False)
        user_tag = self._get_tag(user, False)
        link = (
            f"Chat: {chat_tag} | #ID_{chat.id}"
            + f"\nUser: {user_tag} | #ID_{user.id}"
        )
        try:
            await message.forward_to(logchan_id)
            await message.client.send_message(logchan_id, link)
            return
        except Exception as e:
            if "FORWARDS_RESTRICTED" in str(e):
                msgs = await message.client.get_messages(chat.id, ids=message.id)
                await message.client.send_message(logchan_id, message=msgs)
                await message.client.send_message(logchan_id, link)
            return

    async def watcher(self, message: Message):
        self._global_queue += [message]

    async def _global_queue_handler(self):
        while True:
            while self._global_queue:
                await self._global_queue_handler_process(self._global_queue.pop(0))
            await asyncio.sleep(0)

    async def _global_queue_handler_process(self, message: Message):
        if not isinstance(getattr(message, "chat", 0), (Chat, Channel)) or not isinstance(message, Message):
            return
        chat_id = utils.get_chat_id(message)
        try:
            user_id = (
                getattr(message, "sender_id", False)
                or message.action_message.action.users[0]
            )
        except Exception:
            try:
                user_id = message.action_message.action.from_id.user_id
            except Exception:
                try:
                    user_id = message.from_id.user_id
                except Exception:
                    try:
                        user_id = message.action_message.from_id.user_id
                    except Exception:
                        try:
                            user_id = message.action.from_user.id
                        except Exception:
                            try:
                                user_id = (await message.get_user()).id
                            except Exception:
                                logger.debug(f"Can't extract entity from event {type(message)}")
                                return
        user_id = (
            int(str(user_id)[4:]) if str(user_id).startswith("-100") else int(user_id)
        )
        bnd = self.get("bnd", [])
        bnd_sets = self.get("bnd_sets", {})
        bcu = self.get("bcu", [])
        bcu_sets = self.get("bcu_sets", {})
        gl = self.get("gl", [])
        gl_sets = self.get("gl_sets", {})
        if str(chat_id) in bnd or str(chat_id) in bcu or str(chat_id) in gl:
            chat = await self._client.get_entity(chat_id)
            user = await self._client.get_entity(user_id)
            asyncio.get_event_loop().create_task(self.p__gl(chat, user, message, gl, gl_sets))
            asyncio.get_event_loop().create_task(self.p__bnd(chat, user, message, bnd, bnd_sets))
            asyncio.get_event_loop().create_task(self.p__bcu(chat, user, message, bcu, bcu_sets))
        return


class MigratorClass():
    """
    # ▄▀█ █▄ █ █▀█ █▄ █ █▀█ ▀▀█ █▀█ █ █ █▀
    # █▀█ █ ▀█ █▄█ █ ▀█ ▀▀█   █ ▀▀█ ▀▀█ ▄█
    #
    #              © Copyright 2022
    #
    #             developed by @anon97945
    #
    #          https://t.me/apodiktum_modules
    #
    # 🔒 Licensed under the GNU GPLv3
    # 🌐 https://www.gnu.org/licenses/gpl-3.0.html
    """

    strings = {
        "_log_doc_migrated_db": "Migrated {} database of {} -> {}:\n{}",
        "_log_doc_migrated_cfgv_val": "[Dynamic={}] Migrated default config value:\n{} -> {}",
        "_log_doc_no_dynamic_migration": "No module config found. Did not dynamic migrate:\n{{{}: {}}}",
        "_log_doc_migrated_db_not_found": "`{}` database not found. Did not migrate {} -> {}",
    }

    changes = {
    }

    def __init__(self):
        self._ratelimit = []

    async def init(
        self,
        client: "TelegramClient",  # type: ignore
        db: "Database",  # type: ignore
        modules: str,  # type: ignore
        classname: str,  # type: ignore
        name: str,  # type: ignore
        log: bool = False,  # type: ignore
        debug: bool = False,  # type: ignore
    ):
        self._client = client
        self._db = db
        self._classname = classname
        self._name = name
        self.modules = modules
        self.log = log
        self.debug = debug
        self.hashs = []
        self.hashs = self._db.get(self._classname, "hashs", [])
        self._migrate_to = list(self.changes)[-1] if self.changes else None

    async def migrate(self, log: bool = False, debug: bool = False):
        self.log = log
        self.debug = debug
        if self._migrate_to is not None:
            self.hashs = self._db.get(self._classname, "hashs", [])

            migrate = await self.check_new_migration()
            full_migrated = await self.full_migrated()
            if migrate:
                await self._logger(f"Open migrations: {migrate}", self.debug, True)
                if await self._migrator_func():
                    await self._logger("Migration done.", self.debug, True)
                    return True
            elif not full_migrated:
                await self.force_set_hashs()
                await self._logger(f"Open migrations: {migrate} | Forcehash done: {self.hashs}", self.debug, True)
                return False
            else:
                await self._logger(f"Open migrations: {migrate} | Skip migration.", self.debug, True)
                return False
            return False
        await self._logger("No changes in `changes` dictionary found.", self.debug, True)
        return False

    async def auto_migrate_handler(self, auto_migrate: bool = False):
        if self._migrate_to is not None:
            self.hashs = self._db.get(self._classname, "hashs", [])
            migrate = await self.check_new_migration()
            full_migrated = await self.full_migrated()
            if auto_migrate and migrate:
                await self._logger(f"Open migrations: {migrate} | auto_migrate: {auto_migrate}", self.debug, True)
                if await self._migrator_func():
                    await self._logger("Migration done.", self.debug, True)
                    return
            elif not auto_migrate and not full_migrated:
                await self.force_set_hashs()
                await self._logger(f"Open migrations: {migrate} | auto_migrate: {auto_migrate} | Forcehash done: {self.hashs}", self.debug, True)
                return
            else:
                await self._logger(f"Open migrations: {migrate} | auto_migrate: {auto_migrate} | Skip migrate_handler.", self.debug, True)
                return
        await self._logger("No changes in `changes` dictionary found.", self.debug, True)
        return

    async def force_set_hashs(self):
        await self._set_missing_hashs()
        return True

    async def check_new_migration(self):
        chash = hashlib.sha256(self._migrate_to.encode('utf-8')).hexdigest()
        return chash not in self.hashs

    async def full_migrated(self):
        full_migrated = True
        for migration in self.changes:
            chash = hashlib.sha256(migration.encode('utf-8')).hexdigest()
            if chash not in self.hashs:
                full_migrated = False
        return full_migrated

    async def _migrator_func(self):
        for migration in self.changes:
            chash = hashlib.sha256(migration.encode('utf-8')).hexdigest()
            if chash not in self.hashs:
                old_classname, new_classname, old_name, new_name = await self._get_names(migration)
                for category in self.changes[migration]:
                    await self._copy_config_init(migration, old_classname, new_classname, old_name, new_name, category)
                await self._set_hash(chash)
        return True

    async def _copy_config_init(self, migration, old_classname, new_classname, old_name, new_name, category):
        if category == "classname":
            if self._classname != old_classname and (old_classname in self._db.keys() and self._db[old_classname] and old_classname is not None):
                await self._logger(f"{migration} | {category} | old_value: {str(old_classname)} | new_value: {str(new_classname)}", self.debug, True)
                await self._copy_config(category, old_classname, new_classname, new_name)
            else:
                await self._logger(self.strings["_log_doc_migrated_db_not_found"].format(category, old_classname, new_classname))
        elif category == "name":
            await self._logger(f"{migration} | {category} | old_value: {str(old_name)} | new_value: {str(new_name)}", self.debug, True)
            if self._name != old_name and (old_name in self._db.keys() and self._db[old_name] and old_name is not None):
                await self._copy_config(category, old_name, new_name, new_classname)
            else:
                await self._logger(self.strings["_log_doc_migrated_db_not_found"].format(category, old_name, new_name))
        elif category == "config":
            await self._migrate_cfg_values(migration, category, new_name, new_classname)
        return

    async def _get_names(self, migration):
        old_name = None
        old_classname = None
        new_name = None
        new_classname = None
        for category in self.changes[migration]:
            if category == "classname":
                old_classname, new_classname = await self._get_changes(self.changes[migration][category].items())
            elif category == "name":
                old_name, new_name = await self._get_changes(self.changes[migration][category].items())
        if not new_name:
            new_name = self._name
        if not new_classname:
            new_classname = self._classname
        return old_classname, new_classname, old_name, new_name

    @staticmethod
    async def _get_changes(changes):
        old_value = None
        new_value = None
        for state, value in changes:
            if state == "old":
                old_value = value
            elif state == "new":
                new_value = value
        return old_value, new_value

    async def _migrate_cfg_values(self, migration, category, new_name, new_classname):
        if new_classname in self._db.keys() and "__config__" in self._db[new_classname]:
            if configdb := self._db[new_classname]["__config__"]:
                for cnfg_key in self.changes[migration][category]:
                    old_value, new_value = await self._get_changes(self.changes[migration][category][cnfg_key].items())
                    for key, value in configdb.items():
                        await self._logger(f"{migration} | {category} | ({{old_value: {str(old_value)}}} `==` {{new_value: {str(value)}}}) `and` {{key: {key}}} `==` {{cnfg_key: {cnfg_key}}}", self.debug, True)
                        if value == old_value and key == cnfg_key:
                            dynamic = False
                            self._db[new_classname]["__config__"][cnfg_key] = new_value
                            if (
                                self.modules.lookup(new_name)
                                and self.modules.lookup(new_name).config
                                and key in self.modules.lookup(new_name).config
                            ):
                                self.modules.lookup(new_name).config[cnfg_key] = new_value
                                dynamic = True
                            await self._logger(self.strings["_log_doc_migrated_cfgv_val"].format(dynamic, value, new_value))
        return

    async def _copy_config(self, category, old_name, new_name, name):
        if self._db[new_name]:
            temp_db = {new_name: copy.deepcopy(self._db[new_name])}
            self._db[new_name].clear()
            self._db[new_name] = await self._deep_dict_merge(temp_db[new_name], self._db[old_name])
            temp_db.pop(new_name)
        else:
            self._db[new_name] = copy.deepcopy(self._db[old_name])
        self._db.pop(old_name)
        await self._logger(self.strings["_log_doc_migrated_db"].format(category, old_name, new_name, self._db[new_name]))
        if category == "classname":
            await self._make_dynamic_config(name, new_name)
        if category == "name":
            await self._make_dynamic_config(new_name, name)
        return

    async def _deep_dict_merge(self, dct1, dct2, override=True) -> dict:
        merged = copy.deepcopy(dct1)
        for k, v2 in dct2.items():
            if k in merged:
                v1 = merged[k]
                if isinstance(v1, dict) and isinstance(v2, collections.abc.Mapping):
                    merged[k] = await self._deep_dict_merge(v1, v2, override)
                elif isinstance(v1, list) and isinstance(v2, list):
                    merged[k] = v1 + v2
                elif override:
                    merged[k] = copy.deepcopy(v2)
            else:
                merged[k] = copy.deepcopy(v2)
        return merged

    async def _make_dynamic_config(self, new_name, new_classname=None):
        if new_classname is None:
            return
        if "__config__" in self._db[new_classname].keys():
            for key, value in self._db[new_classname]["__config__"].items():
                if (
                    self.modules.lookup(new_name)
                    and self.modules.lookup(new_name).config
                    and key in self.modules.lookup(new_name).config
                ):
                    self.modules.lookup(new_name).config[key] = value
                else:
                    await self._logger(self.strings["_log_doc_no_dynamic_migration"].format(key, value))
        return

    async def _set_hash(self, chash):
        self.hashs.append(chash)
        self._db.set(self._classname, "hashs", self.hashs)
        return

    async def _set_missing_hashs(self):
        for migration in self.changes:
            chash = hashlib.sha256(migration.encode('utf-8')).hexdigest()
            if chash not in self.hashs:
                await self._set_hash(chash)

    async def _logger(self, log_string, debug: bool = False, debug_msg: bool = False):
        if not debug_msg and self.log:
            return logger.info(log_string)
        if debug and debug_msg:
            return logger.info(log_string)
        return logger.debug(log_string)
