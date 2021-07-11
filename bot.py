#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import os
PORT = int(os.environ.get('PORT', 8443))

token = os.environ.get('TOKEN')

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
import redis
r = redis.from_url(os.environ.get('REDIS_URL'))

from mwt import MWT

@MWT(timeout=60*60)
def get_admin_ids(bot, chat_id):
    """Returns a list of admin IDs for a given chat. Results are cached for 1 hour."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]

"""
Check Permission of user is Admin
"""
def checkPermission(update, context):
    if not update.effective_user.id in get_admin_ids(context.bot, update.message.chat_id):
        update.message.reply_text(f"你唔係院長/副院長！唔俾用🤪")
        return False
    return True

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')
    
def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')

"""
Adjust a user's points
"""
def adjustPoints(update, context):
    if not checkPermission(update, context):
        return
    
    user_name_str = [str(i) for i in context.args[:-1]]
    user_name = "cls:" + str(" ".join(user_name_str))

    while True:
        try:
            points = int(context.args[-1])
            break
        except ValueError:
            update.message.reply_text(f"唔改輸入一個有效嘅數字\n指令參考：/change username 100")
            return

    if r.exists(user_name):
        # update the current points
        cur_points = int(r.get(user_name).decode('utf-8'))
        new_points = cur_points + points
        r.set(user_name, new_points)

    else:
        r.set(user_name, points)
    
    user_name_str = " ".join(user_name_str)

    if points < 0:
        update.message.reply_text(f"扣咗 {user_name_str} {-points}分！\n佢而家嘅CLS分數係 {r.get(user_name).decode('utf-8')}分！")
    else:
        update.message.reply_text(f"加咗 {user_name_str} {points}分！\n佢而家嘅CLS分數係 {r.get(user_name).decode('utf-8')}分！")


"""
Get a user's points
"""
def showPoints(update, context):
    if not context.args:
        update.message.reply_text("唔該輸入正確嘅指令：/show username")
        return
    user_name_str = [str(i) for i in context.args]
    user_name = "cls:" + str(" ".join(user_name_str))
    
    # points = context.user_data.get(user_name, 0)
    if r.exists(user_name):
        points = r.get(user_name).decode('utf-8')
    else:
        update.message.reply_text("冇呢個人喎...一係你打錯名，一係呢個人未有分")
        return

    update.message.reply_text(f"\"{' '.join(user_name_str)}\" 嘅CLS分數係：{points}")

"""
Reset a user's points to 0
"""
def resetPoints(update, context):
    if not checkPermission(update, context):
        return
    if not context.args:
        update.message.reply_text("唔該輸入正確嘅指令：/reset username")
        return
    
    user_name_str = [str(i) for i in context.args]
    user_name = "cls:" + str(" ".join(user_name_str))
    r.set(user_name, 0)
    update.message.reply_text(f"\"{' '.join(user_name_str)}\" 嘅分數已經歸零喇！多謝院長😊🙏！")
    
"""
Points by rank
"""
def rank(update, context):
    ranks = {}
    for key in r.scan_iter("cls:*"):
        ranks[key] = r.get(key).decode('utf-8')

    ranks = dict(sorted(ranks.items(), key=lambda item: -int(item[1])))

    positive = []
    positive.append("CLS分數龍虎榜 TOP 5：\n")
    for idx, (user_name, points) in enumerate(ranks.items()):
        if idx > 4 or int(points) <= 0:
            break
        user_name = user_name[4:]
        positive.append(f"{idx+1}: {user_name.decode('utf-8')} | {points}\n")
    if len(positive) == 1:
        positive.append("冇人上榜~\n")
    
    ranks = dict(sorted(ranks.items(), key=lambda item: int(item[1])))
    negative = []
    negative.append("\n\nCLS分數龍虎榜 負TOP 5：\n")
    for idx, (user_name, points) in enumerate(ranks.items()):
        if idx > 4 or int(points) >= 0:
            break
        user_name = user_name[4:]
        negative.append(f"{idx+1}: {user_name.decode('utf-8')} | {points}\n")
    if len(negative) == 1:
        negative.append("冇人上榜~\n")

    result = positive + negative

    update.message.reply_text("".join(result))

"""
Delete key from redis
"""
def delete(update, context):
    if not checkPermission(update, context):
        return
    if not context.args:
        update.message.reply_text("唔該輸入正確嘅指令：/delete username")
        return

    user_name_str = [str(i) for i in context.args]
    user_name = "cls:" + str(" ".join(user_name_str))
    
    if not r.exists(user_name):
        update.message.reply_text("未adjust呢個人嘅分數！麻煩adjust咗先再delete！")
        return

    r.delete(user_name)
    update.message.reply_text(f"剷咗\"{' '.join(user_name_str)}\"")
"""
transfer point from user A to B in redis
"""
def transfer(update, context):
  if not checkPermission(update, context):
    return
   
"""
Check existing users in redis
"""
def users(update, context):
    if not checkPermission(update, context):
        return

    result = []
    for key in r.scan_iter("cls:*"):
        key = key[4:]
        result.append(f"{key.decode('utf-8')}\n")

    update.message.reply_text("".join(result))

def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(token, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler('adjust', adjustPoints))
    dp.add_handler(CommandHandler('show', showPoints))
    dp.add_handler(CommandHandler('reset', resetPoints))
    dp.add_handler(CommandHandler('rank', rank))
    dp.add_handler(CommandHandler('delete', delete))
    dp.add_handler(CommandHandler('users', users))

    # on noncommand i.e message - echo the message on Telegram
    # dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=token,
                          webhook_url=os.environ.get('WEBHOOK_URL') + token)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
