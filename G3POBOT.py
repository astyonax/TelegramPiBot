#!/usr/bin/env python

import telegram
import os
from string import atoi
import subprocess
import cPickle
import logging

# handle shutdown term-signals
import signal
def signal_term_handler(signal, frame):
    raise KeyboardInterrupt

#ZERO CONFIGURATION
MYNAME="G3POBOT"
ADMIN0="WRITEHEREYOURIDASINT"
LOGLVL=logging.DEBUG

class Commands(object):
    def __init__(self,bot,cfgfile,logger=None):
        self.registered_commands={
        '/shutdown':self.shutdown,
        '/reboot':self.reboot,
        '/date':self.date,
        '/APclients':self.APclients,
        '/APinfo':self.APinfo,
        '/help':self.helpcmd,
        '/list':self.listcmd,
        '/myID':self.myID}
        self.cfgfile=cfgfile
        self.bot=bot
        self.parse_cfg()
        if not logger:
            self.logger=make_logger('Commands')
        else:
            self.logger=make_logger(logger)


    def parse_cfg(self):
        try:
            with open(self.cfgfile,"rb") as fin:
                cfgdata=cPickle.load(fin)
        except IOError:
            cfgdata={'admn_ch':{ADMIN0:[]}}
        self.admin_list=cfgdata['admn_ch'].keys()
        self.admn_chats=cfgdata['admn_ch']

    def isadmin(self,update):
        # print dir(update)
        ID=update.from_user.id

        yesno=ID in self.admin_list
        # update the admin chats to be able to broadcast message to admins
        if yesno and update.chat_id not in self.admn_chats[ID]:
            self.admn_chats[ID].append(update.chat_id)
        return yesno

    def sendtoadm(self,txt):
        for admin in self.admin_list:
            for chat_id in self.admn_chats[admin]:
                try:
                    self.bot.sendMessage(chat_id=chat_id,text=txt)
                except telegram.error.TelegramError,msg:
                    logger.error(msg)

        return self

    def __enter__(self):

        txt="AP and BOT alive!!"
        self.sendtoadm(txt)
        self.logger.debug("Entering: Commands")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        dataout={'admn_ch':self.admn_chats}
        with open(self.cfgfile,"wb") as fout:
            cPickle.dump(dataout,fout)
        txt="Bye Bye"
        self.sendtoadm(txt)
        self.logger.debug("Exiting: Commands")

    def sendTXT(self,update,txt):
        chat_id=update.chat_id
        try:
            self.bot.sendMessage(chat_id=chat_id,text=txt)
        except telegram.error.TelegramError,msg:
            logger.error(msg)
            #Would be nice to be able to queue the failed deliveries and to try again every n-sec to deliver

    def helpcmd(self,update):
        admin=self.isadmin(update)
        if admin:
            admin="You have the PI power!"
        else:
            admin=""
        msg="""
        Hi {0:s},
            This is a Telegram bot to admin a RaspberryPi access point.
            {1:s}
            Here follow a list of available commands. Not all are implemented yet!
        """.format(update.from_user.first_name,admin)
        self.sendTXT(update, msg)
        self.listcmd(update)

    def listcmd(self,update):
        """
         Returns a list of available commands
        """
        self.sendTXT(update,'\n'.join(sorted(self.registered_commands.keys())))

    def myID(self,update):
        """
        Returns the user Telegram ID
        """
        self.sendTXT(update,'{0:d}'.format(update.from_user.id))

    def parse_upd(self,update):
        # chat_id = update.message.chat_id
        # msg_id= update.message.message_id
        message=update.message
        message.text  = update.message.text.encode('utf-8')
        # uFN=update.message.from_user.first_name
        # uLN=update.message.from_user.last_name
        # uID=update.message.from_user.id
        return update.message

    def describe(self,update,func):
        doc=func.__doc__
        if not doc:
            doc="To be written. I'm sorry. Complain to my author!"
        self.sendTXT(update,doc)

    def me(self,update):
        msg1=subprocess.check_output(['uname','-a'],)
        msg2=subprocess.check_output(['uptime'],)
        self.sendTXT(update,msg1+"\n"+msg2)

    def not_command(self,update):
        return
    ################################33
    ## Custom functions
    ################################33
    def shutdown(self,update):
        if self.isadmin(update):
            self.me(update)
            # self.APclients(update)
            self.sendTXT(update,"Shutting down now!")
            os.system("shutdown -h now&")
            # os.system("sleep 30&")
            raise KeyboardInterrupt
        else:
            self.sendTXT(update,"You are not admin")

    def reboot(self,update):
        if update.from_user.id in self.admin_list:
            self.me(update)
            self.sendTXT(update,"Rebooting! See u soon")
            os.system("shutdown -r now&")
            raise KeyboardInterrupt
        else:
            self.sendTXT(update,"You are not admin")

    def date(self,update):
        self.sendTXT(update, "Not Implemented")

    def APinfo(self,update):
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
        self.sendTXT(update,msg)

    def APclients(self,update):
        """
        Returns a list of connected clients via "arp -a"
        """
        self.bot.sendChatAction(update.chat_id, 'typing')
        msg=subprocess.check_output(['arp','-a'],)
        N=len(msg.strip().split('\n'))
        msg="{0:d} clients conneted\n".format(N)+msg
        self.sendTXT(update,msg)
    ################################
    ## End of Custom functions
    ################################

    def __call__(self,update):
        try:  # wathever happens, do not crash and report the error!
            # Here you find only the parsing of the input text,
            # no response is  generated by this function
            # This function dispatches the response-duty to the commands functions
            data=self.parse_upd(update)
            textmsg=data.text
            try:
                if not textmsg[0]=='/': #this intercept empty and not '/'-beginning strings
                    raise IndexError
                cmd=textmsg.split()[0].strip()
                if not cmd in self.registered_commands.keys(): #this intercepts invalid commands
                    raise IndexError
            except IndexError:
                self.not_command(update)
                return
            # IF we are here, cmd is a valid command in the list of commands
            # and deserves attention
            try:
                helpme="?" in textmsg.split()[1].strip()
            except IndexError:
                helpme=False

            if helpme:
                # if the user is using the syntax <command> ?, then provide the online __doc__ string
                self.describe(data,self.registered_commands[cmd])
            else:
                # else, we finally can execute the code
                self.registered_commands[cmd](data)
            return
        except Exception, msg:
            err="EE: {0:s}".format(msg.message)
            self.sendtoadm(err)
            self.logger(err)

def make_logger(name='',fname=''):
    if not name:
        FORMAT = '%(asctime)-15s  %(message)s'
        if fname:
            logging.basicConfig(format=FORMAT,filename=fname)
        else:
            logging.basicConfig(format=FORMAT)

    logger=logging.getLogger(name)
    logger.setLevel(LOGLVL)
    return logger

if __name__=='__main__':
    import sys
    if '-i' in sys.argv:
        """ Install and exit -- tha means write the rc.local file
        """
        with open('/etc/rc.local','rw') as rclcl:
            lines=rclcl.readlines()
            me=__file__
            python='/usr/bin/python'
            string='sudo -u root {0:s} {1:s} &'.format(python,me)
            print string
            exit(0)
    signal.signal(signal.SIGTERM, signal_term_handler)

    # 1. SET UP LOGGIN
    # this enable the Telegram liberary logging facility that is quite expansive :D
    home = os.path.expanduser("~")
    print home
    cfgdir=home+'/'+".config/{0:s}/".format(MYNAME)


    logger = make_logger('',fname=cfgdir+'/run.log')

    # 2. LOAD CONFIGURATION
    logger.debug("loading config")

    if not os.path.exists(cfgdir):
        os.mkdir(cfgdir)

    try:
        with open(cfgdir+'/LAST_UPDATE_ID','r') as fin:
            LAST_UPDATE_ID=atoi(fin.readline())
    except (IOError,ValueError):
        LAST_UPDATE_ID=None
    try:
        with open(cfgdir+'/token','r') as token:
            token=token.read().strip()
            token[0]

    except (IOError,IndexError):
        print "A bot token has to be provided:"
        print "follow instructions @ https://core.telegram.org/bots and "
        exit(1)
    #DONE WITH LOADING


    # RUN THE BOT -- YES. this is messy
    bot = telegram.Bot(token)
    with Commands(bot,cfgdir+"/commands_cfg") as process_update:
        try:
            while True:
                try:
                    for update in bot.getUpdates(offset=LAST_UPDATE_ID, timeout=10):
                        LAST_UPDATE_ID=update.update_id
                        LAST_UPDATE_ID+=1
                        process_update(update)
                except telegram.error.TelegramError,msg:
                    logger.error(msg)
        except:
            logger.debug("Saving LAST_UPDATE_ID")
            with open(cfgdir+'/LAST_UPDATE_ID','w') as fout:
                fout.write("{0:d}".format(LAST_UPDATE_ID))
    logger.debug("Last line.")
