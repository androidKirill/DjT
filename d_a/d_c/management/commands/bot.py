from django.core.management.base import BaseCommand
from django.conf import settings
from telegram import Bot
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater
from telegram.utils.request import Request

from d_c.models import Profile, Message


def log_errors(f):
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(f"I'm afraid there's a mistake: {e}.")
            raise e

    return inner


@log_errors
def do_echo(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    text = update.message.text

    p, _ = Profile.objects.get_or_create(
        external_id=chat_id,
        defaults={"name": update.message.from_user.username}
    )

    m = Message(profile=p, text=text)
    m.save()

    reply_text = f"Your ID = {chat_id}\n\nMessage ID = {m.pk}\n{text}"
    update.message.reply_text(text=reply_text)


@log_errors
def do_count(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    p, _ = Profile.objects.get_or_create(
        external_id=chat_id,
        defaults={"name": update.message.from_user.username}
    )

    count = Message.objects.filter(profile=p).count()

    update.message.reply_text(text=f"You have {count} messages")


class Command(BaseCommand):
    help = "Telegram-bot"

    def handle(self, *args, **options):
        # 1 - правильное подключение
        request = Request(connect_timeout=0.5, read_timeout=1.0)
        bot = Bot(request=request, token=settings.TOKEN, base_url=settings.PROXY_URL)
        print(bot.get_me())

        # 2 - обработчик
        updater = Updater(bot=bot, use_context=True)

        updater.dispatcher.add_handler(CommandHandler("count", do_count))

        message_handler = MessageHandler(Filters.text, do_echo)
        updater.dispatcher.add_handler(message_handler)

        # 3 - запуск бесконечной обработки входящих сообщений
        updater.start_polling()
        updater.idle()
