#!/usr/bin/env python

import telegram
import os
from string import atoi
import subprocess
import cPickle
TOIM="to implement"

class Commands(object):
    def __init__(self,bot,cfgfile):
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

    def parse_cfg(self):
        try:
            with open(self.cfgfile,"rb") as fin:
                cfgdata=cPickle.load(fin)
        except IOError:
            cfgdata={'admn_ch':{WRITEHEREYOURIDASINT:[]}}
        self.admin_list=cfgdata['admn_ch'].keys()
        self.admn_chats=cfgdata['admn_ch']

    def isadmin(self,update):
        print dir(update)
        ID=update.from_user.id

        yesno=ID in self.admin_list
        # update the admin chats to be able to broadcast message to admins
        if yesno and update.chat_id not in self.admn_chats[ID]:
            self.admn_chats[ID].append(update.chat_id)
        return yesno

    def sendtoadm(self,txt):
        for admin in self.admin_list:
            for chat_id in self.admn_chats[admin]:
                self.bot.sendMessage(chat_id=chat_id,text=txt)
        return self

    def __enter__(self):
        txt="AP and BOT alive!!"
        self.sendtoadm(txt)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        dataout={'admn_ch':self.admn_chats}
        with open(self.cfgfile,"wb") as fout:
            cPickle.dump(dataout,fout)
        txt="Bye Bye"
        self.sendtoadm(txt)

    def sendTXT(self,update,txt):
        chat_id=update.chat_id
        self.bot.sendMessage(chat_id=chat_id,text=txt)

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
    ################################33
    ## Custom functions
    ################################33
    def shutdown(self,update):
        if self.isadmin(update):
            self.me(update)
            # self.APclients(update)
            self.sendTXT(update,"Shutting down now!")
            os.system("shutdown -h now&")
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
        self.sendTXT(update, TOIM)

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
    ################################33
    ## End of Custom functions
    ################################33

    def __call__(self,update):
        # here is only the logic of commands handling.
        # no response is actually generated from this function
        data=self.parse_upd(update)
        try:
            textmsg=data.text
            if textmsg:
                if (textmsg[0] == '/'):
                    # this is a command
                    cmd=textmsg.split()[0].strip()
                    if cmd in self.registered_commands.keys():
                        # is the user asking for help?
                        try:
                            helpme="?" in textmsg.split()[1].strip()
                        except IndexError:
                            helpme=False
                        if helpme:
                            self.describe(data,self.registered_commands[cmd])
                        else:
                            self.registered_commands[cmd](data)
            else:
                self.registered_commands['/help'](data)
        except Exception, msg:
            if data.from_user.id in self.admin_list:
                #self.sendTXT(data,)
                self.sendTXT(data, "EE: {0:s}".format(msg.message))


if __name__=='__main__':
    home = os.path.expanduser("~")
    cfgdir=home+'/'+".config/G3POBOT/"

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
        print "A bot token has to be provided."
        print "Go to https://core.telegram.org/bots and follow instructions"
        exit(1)


    # make the Bot with its token and some parameters
    bot = telegram.Bot(token)
    with Commands(bot,cfgdir+"/commands_cfg") as process_update:
        try:
            while True:
                for update in bot.getUpdates(offset=LAST_UPDATE_ID, timeout=10):
                    LAST_UPDATE_ID=update.update_id
                    LAST_UPDATE_ID+=1
                    process_update(update)
        except:
            print "Closing.."

        with open(cfgdir+'/LAST_UPDATE_ID','w') as fout:
            fout.write("{0:d}".format(LAST_UPDATE_ID))
