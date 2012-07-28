#!/usr/bin/python
# coding=utf-8

'''
requires:
    python-twitter
    pyyaml
    xmpppy

when testing, specify a chatroom name on the command line.
eg:
    python chatbot.py {test-chatroom}

    to open the chatroom test-chatroom
'''

import chat_funcs
import me_funcs

import datetime
import re
import smtplib
import sys
import xmpp
import yaml

import settings


class ChatBot():
    prev_message = ''
    curr_message = ''
    pile_on = ''
    learning = None

    timeout = None
    silent = False

    def __init__(self, chatroom=settings.chatroom):
        self.chatroom = chatroom

        jid = xmpp.protocol.JID(settings.username)
        self.client = xmpp.Client(jid.getDomain(), debug=[])
        self.client.connect()
        self.client.auth(jid.getNode(), settings.password)
        self.client.sendInitPresence()
        self.client.RegisterHandler('message', self.message_callback)
        self.client.RegisterHandler('presence', self.presence_callback)
        self.client.send(xmpp.Presence(to='%s/%s' %
            (chatroom, settings.screen_name)))

        self.stop = False
        while not self.stop:
            self.startup = datetime.datetime.now() + datetime.timedelta(minutes=1)
            reload(settings)

            #load responses when spoken to
            with open('me_responds.yaml') as fh:
                self.me_responds = yaml.load(fh)
                fh.close()

            #load generic chat responses
            with open('generic_responds.yaml') as fh:
                self.chat_responds = yaml.load(fh)
                fh.close()

            while self.step():
                pass
            if not self.stop:
                print 'reloading'
                self.client.reconnectAndReauth()

        self.send_to_chat('brb')

    def step(self):
        try:
            return self.client.Process(1)
        except KeyboardInterrupt:
            self.stop = True
            return False
        #return True

    def presence_callback(self, conn, msg):
        ''' handles presence messages '''
        if msg.getType() == 'groupchat':
            usr = msg.getFrom().getResource()
            print '%s is %s' % (usr, msg.getShow())
        #else:
        #    print msg

    def message_callback(self, conn, msg):
        ''' process an incoming chat message '''

        #groupchat messages
        if msg.getType() == "groupchat":
            self.handle_groupchat_message(msg)

        #private message
        if msg.getType() == "chat":
            self.handle_private_message(msg)

    def handle_groupchat_message(self, message):
        ''' most of the fun happens here, in groupchat '''

        #handle a 1-minute startup delay, to prevent the last-50 nuissance
        if self.startup:
            if self.startup > datetime.datetime.now():
                return
            else:
                self.startup = None

        #if we have any trouble handling the incoming message, just ignore it
        try:
            msgbody = str(message.getBody().decode('utf-8'))
        except:
            return

        msgfrom = message.getFrom().getResource()
        nicefrom = re.sub(r'\s.*$', '', msgfrom)
        msgtext = msgbody.lower()

        self.curr_message = msgtext

        #ignore some people
        if msgfrom.lower() in settings.ignore_from:
            return

        #log what we're seeing. why not, it could help...
        print str("%s: %s" % (msgfrom, msgtext))

        #first, respond when spoke to...
        if re.search(r'\b(%s)\b' % '|'.join(settings.my_names), msgtext):

            #process responses in me_funcs.py
            out = me_funcs.responder.get_response(self, msgtext, nicefrom)
            if out:
                return self.send_to_chat(out)

            if self.silent:
                return self.update_message_state()

            #look through the predefined responses...
            for expression, response in self.me_responds:
                if re.search(expression, msgtext):
                    return self.send_to_chat(response.format(nicefrom))

            #don't know what to do with my name?
            #return self.send_to_chat('I heard my name...')

        #if chatbot is being quiet
        if self.silent:
            return self.update_message_state()

        #if chatbot is taking a timeout
        if self.timeout:
            print 'timeout expires: %s' % str(self.timeout)
            if self.timeout > datetime.datetime.now():
                return self.update_message_state()
            else:
                self.timeout = None

        # okay...
        # now that the official business is taken care of,
        # let's have some fun...

        #process commands in chat_funcs.py
        out = chat_funcs.responder.get_response(self, msgtext, nicefrom)
        if out:
            return self.send_to_chat(out)

        #otherwise, look through the predefined responses...
        for expression, response in self.chat_responds:
            if re.search(expression, msgtext):
                return self.send_to_chat(response.format(nicefrom))

        #if chatbot is learning a new phrase, it's not in the array yet
        if self.learning:
            if re.search(self.learning[0], msgtext):
                return self.send_to_chat(self.learning[1].format(nicefrom))

        #pile on when people repeat each other
        if msgtext.lower() == self.prev_message.lower():
            if self.pile_on != self.prev_message:
                self.pile_on = self.prev_message
                return self.send_to_chat(self.prev_message)
            #otherwise, don't be obnoxious, just let it go
            return self.update_message_state()

        #otherwise, do nothing
        self.update_message_state()

    def handle_private_message(self, message):
        ''' we can also handle private chat messages '''
        try:
            fromname = message.getFrom().getStripped()
            msgtext = message.getBody()
            for key, val in settings.aliases.iteritems():
                if val == fromname:
                    fromname = key
                    break
            self.send_to_chat('%s says, "%s"' % (fromname, msgtext))
        except:
            print "error handling private message:"
        return

    def send_to_chat(self, message):
        ''' dump a message to the chatroom '''
        msg = xmpp.Message(to=self.chatroom, typ='groupchat', body=message)
        self.client.send(msg)
        self.update_message_state()

    def send_private_message(self, recipient, message):
        ''' send a private message to a user '''
        msg = xmpp.Message(to=recipient, body=message)
        self.client.send(msg)

    def update_message_state(self):
        ''' some housekeeping '''
        if self.curr_message:
            self.prev_message = self.curr_message
            self.curr_message = None

    def send_email(self, recipient, message):
        ''' if we want to send emails '''
        mail = "Subject: SMTP to SMS test\n\n%s" % message
        try:
            smtp = smtplib.SMTP(settings.smtp_hostname, settings.smtp_port)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.mail(settings.smtp_username)
            smtp.rcpt(recipient)
            smtp.data(mail)
            smtp.close()
            return True
        except:
            return False


def main():
    ''' release the kraken... '''
    if len(sys.argv) > 1:
        domain = xmpp.protocol.JID(settings.chatroom).getDomain()
        print 'Joining room: %s@%s ' % (sys.argv[1], domain)
        ChatBot(chatroom='%s@%s' % (sys.argv[1], domain))
    else:
        print 'Joining %s' % settings.chatroom
        ChatBot()

if __name__ == '__main__':
    main()
