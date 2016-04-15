#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Example Bot to show some of the functionality of the library
# This program is dedicated to the public domain under the CC0 license.

"""
This Bot uses the Updater class to handle the bot.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and the CLI-Loop is entered, where all text inputs are
inserted into the update queue for the bot to handle.

Usage:
Repeats messages with a delay.
Reply to last chat from the command line by typing "/reply <text>"
Type 'stop' on the command line to stop the bot.
"""

from telegram.ext import Updater
from telegram.ext.dispatcher import run_async
from time import sleep
import logging

import os
import cPickle
import subprocess

# Enable Logging
logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

logger = logging.getLogger(__name__)

# We use this var to save the last chat id, so we can reply to it
last_chat_id = 0
MYNAME="G3POBOT"


# Define a few (command) handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """ Answer in Telegram """
    bot.sendMessage(update.message.chat_id, text='Hi!')


def help(bot, update):
    """ Answer in Telegram """
    bot.sendMessage(update.message.chat_id, text='Help!')


def any_message(bot, update):
    """ Print to console """

    # Save last chat_id to use in reply handler
    global last_chat_id
    last_chat_id = update.message.chat_id

    logger.info("New message\nFrom: %s\nchat_id: %d\nText: %s" %
                (update.message.from_user,
                 update.message.chat_id,
                 update.message.text))


def unknown_command(bot, update):
    """ Answer in Telegram """
    bot.sendMessage(update.message.chat_id, text='Command not recognized!')


@run_async
def message(bot, update, **kwargs):
    """
    Example for an asynchronous handler. It's not guaranteed that replies will
    be in order when using @run_async. Also, you have to include **kwargs in
    your parameter list. The kwargs contain all optional parameters that are
    """

    sleep(2)  # IO-heavy operation here
    bot.sendMessage(update.message.chat_id, text='Echo: %s' %
                                                 update.message.text)

@run_async
def APclients(bot,update,**kwargs):
    """
    Returns a list of connected clients via "arp -a"
    """
    bot.sendChatAction(update.message.chat_id, 'typing')
    msg=subprocess.check_output(['arp','-a'],)
    N=len(msg.strip().split('\n'))
    msg="{0:d} clients conneted\n".format(N)+msg
    permits.replyifadmin(bot,msg)
    # bot.sendMessage(update.message.chat_id,text=msg)

def me(bot,update,**kwargs):
    msg1=subprocess.check_output(['uname','-a'],)
    msg2=subprocess.check_output(['uptime'],)
    permits.replyifadmin(bot,msg1+"\n"+msg2)

@run_async
def APinfo(bot,update,**kwargs):
    """
    Returns SSID and PW of the AP
    """
    fin="/etc/hostapd/hostapd.conf"
    with open(fin,"r") as fin:
        data=fin.readlines()
    ssid=[j for j in data if 'ssid' in j.lower()][0].split("=")[1].strip()
    pw=[j for j in data if 'passphrase' in j.lower()][0].split("=")[1].strip()

    msg="""
    SSID: {0:s}
    PW: {1:s}
    """.format(ssid,pw)
    permits.replyifadmin(bot,msg)


# Comands to handle the bot software and machine
def shutdown(bot,update):
    if permits.isadmin(update):

        # self.APclients(update)
        permits.sendtoadm("Shutting down now!")
        os.system("shutdown -h now&")
    else:
        bot.sendMessage(update.message.chat_id,"You are not admin")

def quit(bot,update):
    if permits.isadmin(update):
        permits.sendtoadm("Bot quitting upon request")
        import sys
        sys.exit(2)
        raise KeyboardInterrupt

# These handlers are for updates of type str. We use them to react to inputs
# on the command line interface
def cli_reply(bot, update, args):
    """
    For any update of type telegram.Update or str that contains a command, you
    can get the argument list by appending args to the function parameters.
    Here, we reply to the last active chat with the text after the command.
    """
    if last_chat_id is not 0:
        bot.sendMessage(chat_id=last_chat_id, text=' '.join(args))


def cli_noncommand(bot, update, update_queue):
    """
    You can also get the update queue as an argument in any handler by
    appending it to the argument list. Be careful with this though.
    Here, we put the input string back into the queue, but as a command.

    To learn more about those optional handler parameters, read:
    http://python-telegram-bot.readthedocs.org/en/latest/telegram.dispatcher.html
    """
    update_queue.put('/%s' % update)


def unknown_cli_command(bot, update):
    logger.warn("Command not found: %s" % update)


def error(bot, update, error):
    """ Print error to console """
    logger.warn('Update %s caused error %s' % (update, error))

def parse_cfg(fname):
    try:
        with open(fname,"rb") as fin:
            cfgdata=cPickle.load(fin)
    except IOError:
        cfgdata={'admn_ch':{ADMIN0:[]}}
    admin_list=cfgdata['admn_ch'].keys()
    admin_chats=cfgdata['admn_ch']
    return  admin_list,admin_chats

################################################################################
## Permissions handler
##
class Permissions(object):
    def __init__(self,bot,admin_list,admin_chats):
        self.bot=bot
        self.admin_list=admin_list
        self.admin_chats=admin_chats

    def isadmin(self,update):
        # print dir(update)
        # print update.message.from_user['id']

        ID=update.message.from_user['id']

        yesno=ID in self.admin_list
        # update the admin chats to be able to broadcast message to admins
        if yesno and update.message.chat_id not in self.admin_chats[ID]:
            self.admin_chats[ID].append(update.chat_id)
        return yesno

    def replyifadmin(self,update,msg):
        if self.isadmin(update):
            self.bot.sendMessage(update.message.chat_id,text=msg)
        else:
            msg='You are not authorized to receive this output'
            self.bot.sendMessage(update.message.chat_id,text=msg)

    def sendtoadm(self,txt):
        for admin in self.admin_list:
            for chat_id in self.admin_chats[admin]:
                try:
                    self.bot.sendMessage(chat_id=chat_id,text=txt)
                except telegram.error.TelegramError,msg:
                    logger.error(msg)

        return self

##
################################################################################
permits=0

def main():
    global permits

    home = os.path.expanduser("~")
    cfgdir=home+'/'+".config/{0:s}/".format(MYNAME)
    with open(cfgdir+'/token','r') as token:
        token=token.read().strip()
    admin_list,admin_chats=parse_cfg(cfgdir+"/commands_cfg")

    # Create the EventHandler and pass it your bot's token.

    updater = Updater(token, workers=10)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Set up permissions and admin communication channels
    permits=Permissions(dp.bot,admin_list,admin_chats)

    # Advertise our online-status
    permits.sendtoadm('I am online')

    # This is how we add handlers for Telegram messages
    dp.addTelegramCommandHandler("start", start)
    dp.addTelegramCommandHandler("help", help)
    dp.addTelegramCommandHandler("APclients", APclients)
    dp.addTelegramCommandHandler("APinfo", APinfo)
    dp.addTelegramCommandHandler("me", me)
    dp.addTelegramCommandHandler("quit", quit)
    dp.addTelegramCommandHandler("shutdown", shutdown)
    dp.addUnknownTelegramCommandHandler(unknown_command)
    # Message handlers only receive updates that don't contain commands
    dp.addTelegramMessageHandler(message)
    # Regex handlers will receive all updates on which their regex matches
    dp.addTelegramRegexHandler('.*', any_message)

    # String handlers work pretty much the same
    dp.addStringCommandHandler('reply', cli_reply)
    dp.addUnknownStringCommandHandler(unknown_cli_command)
    dp.addStringRegexHandler('[^/].*', cli_noncommand)

    # All TelegramErrors are caught for you and delivered to the error
    # handler(s). Other types of Errors are not caught.
    dp.addErrorHandler(error)

    # Start the Bot and store the update Queue, so we can insert updates
    update_queue = updater.start_polling(poll_interval=0.1, timeout=10)

    '''
    # Alternatively, run with webhook:
    updater.bot.setWebhook(webhook_url='https://example.com/%s' % token,
                           certificate=open('cert.pem', 'rb'))

    update_queue = updater.start_webhook('0.0.0.0',
                                         443,
                                         url_path=token,
                                         cert='cert.pem',
                                         key='key.key')

    # Or, if SSL is handled by a reverse proxy, the webhook URL is already set
    # and the reverse proxy is configured to deliver directly to port 6000:

    update_queue = updater.start_webhook('0.0.0.0',
                                         6000)
    '''

    # Start CLI-Loop
    while True:
        try:
            text = raw_input()
        except NameError:
            text = input()

        # Gracefully stop the event handler
        if text == 'stop':
            updater.stop()
            break

        # else, put the text into the update queue to be handled by our handlers
        elif len(text) > 0:
            update_queue.put(text)
    # Advertise our online-status
    permits.sendtoadm('I am offline')

if __name__ == '__main__':
    main()
