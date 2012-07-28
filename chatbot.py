#!/usr/bin/python
# coding=utf-8

'''
requires:
    python-twitter
    PyYAML
    xmpppy
    (or, use requirements.txt)

description:
    this is a base class. it won't work by itself.
    to make a chatbot, extend this class,
    specifying username, password, chatroom, and
    screen_name as properties of your object.
'''

import datetime
import re
import smtplib
import sys
import twitter
import xmpp
import yaml


class ChatResponder(list):
    '''
    Used to parse a list of regular expressions
    and match text to which to respond.
    '''
    def __call__(self, *expr):
        ''' response decorator '''
        def decorator(func):
            func.expressions = expr
            func.data = None
            self.append(func)
            return func
        return decorator

    def get_response(self, bot, text, user):
        ''' iterate the list of responses and search for a match '''
        for response in self:
            #a response can have multiple regexes
            for exp in response.expressions:
                m = re.search(exp, text, re.M)
                if m:
                    #only return if the match gave back text
                    r = response(bot, m, text, user)
                    if r:
                        return r
        return None


responder = ChatResponder()
me_responder = ChatResponder()


class ChatBot():
    my_names = []
    ignore_from = []
    aliases = {}

    prev_message = ''
    curr_message = ''
    pile_on = ''
    learning = None

    timeout = None
    silent = False

    def __init__(self, chatroom=None):
        if chatroom:
            self.chatroom = chatroom

        jid = xmpp.protocol.JID(self.username)
        self.jid = jid
        if jid.getDomain() == 'gmail.com':
            self.chat_domain = 'groupchat.google.com'
        else:
            self.chat_domain = 'conference.%s' % jid.getDomain()

        self.full_chatroom = '%s@%s/%s' % (
                self.chatroom, self.chat_domain, self.screen_name)

        self.client = xmpp.Client(jid.getDomain(), debug=[])
        print "connecting to %s..." % self.chat_domain  # jid.getDomain()
        if not self.client.connect():
            print "unable to connect."
            return
        print "authorizing..."
        if not self.client.auth(jid.getNode(), self.password):
            print "unable to authorize."
            return
        print 'Joining chatroom...'
        self.client.sendInitPresence()
        self.client.RegisterHandler('message', self.message_callback)
        self.client.RegisterHandler('presence', self.presence_callback)
        self.client.send(xmpp.Presence(to=self.full_chatroom))

        self.stop = False
        while not self.stop:
            self.startup = datetime.datetime.now() + datetime.timedelta(minutes=1)

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
        if msgfrom.lower() in self.ignore_from:
            return

        #log what we're seeing. why not, it could help...
        print str("%s: %s" % (msgfrom, msgtext))

        #first, respond when spoke to...
        if re.search(r'\b(%s)\b' % '|'.join(self.my_names), msgtext):

            #process responses in me_funcs.py
            out = me_responder.get_response(self, msgtext, nicefrom)
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
        out = responder.get_response(self, msgtext, nicefrom)
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
            for key, val in self.aliases.iteritems():
                if val == fromname:
                    fromname = key
                    break
            self.send_to_chat('%s says, "%s"' % (fromname, msgtext))
        except:
            print "error handling private message:"
        return

    def send_to_chat(self, message):
        ''' dump a message to the chatroom '''
        msg = xmpp.Message(
                to='%s@%s' % (self.chatroom, self.chat_domain),
                typ='groupchat',
                body=message)
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

    #helper, to get twitter status
    def get_last_tweet(self, twitter_handle):
        try:
            api = twitter.Api()
            timeline = api.GetUserTimeline(twitter_handle)
            tweet = timeline[0]
            return tweet
        except:
            return None

    def send_email(self, recipient, message):
        ''' if we want to send emails '''
        mail = "Subject: SMTP to SMS test\n\n%s" % message
        try:
            smtp = smtplib.SMTP(self.smtp_hostname, self.smtp_port)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(self.smtp_username, self.smtp_password)
            smtp.mail(self.smtp_username)
            smtp.rcpt(recipient)
            smtp.data(mail)
            smtp.close()
            return True
        except:
            return False

    #this bitch needs an off switch
    @me_responder(r'^(be )?quiet\b')
    def start_silence(self, m, text, user):
        self.silent = True
        return 'sorry. i\'ll put a lid on it.'

    #and an on switch
    @me_responder(r'^okay,?')
    def end_silence(self, m, text, user):
        self.silent = False
        self.timeout = None
        return 'thanks, %s' % user.lower()

    #let's also support a timeout
    @me_responder(r'\b(that\'?s )?enough\b|\btake a break\b|\bhush\b')
    def set_timeout(self, m, text, user):
        self.timeout = datetime.datetime.now() + datetime.timedelta(minutes=10)
        return 'i\'m gonna stay quiet for a bit.'

    #learn new things...
    #   "chatbot, learn: a = b"
    @me_responder(r'\w+[,\.]*\s+learn:\s*([^=]+)\s*=\s*(.+)')
    def learn(self, m, text, user):
        exp = str(m.group(1)).strip()
        resp = str(m.group(2)).strip()
        self.learning = (exp, resp)
        return 'okay, got it.'

    #save what you've learned
    #   "keep it, chatbot"
    @me_responder(r'keep it')
    def keep_learned(self, m, text, user):
        if self.learning:
            self.chat_responds.append(self.learning)
            self.learning = None
            f = open('generic_responds.yaml', 'w')
            f.write(yaml.dump(self.chat_responds))
            f.close()
            return 'committed to memory.'
        else:
            return 'i\'m not learning anything.'

    #erase the last thing you learned
    #    "forget it, chatbot"
    @me_responder(r'forget it')
    def forget_learned(self, m, text, user):
        if self.learning:
            self.learning = None
            return 'forgotten.'
        else:
            return 'i\'m not learning anything.'

    #fetch a tweet
    @responder(r'^last tweet from \@(\S+)')
    def twitter_status(self, m, text, user):
        t = self.get_last_tweet(m.group(1))
        if t:
            return 'last tweet from @%s: %s' % (m.group(1), t.text)


def main():
    ''' release the kraken... '''
    if len(sys.argv) > 1:
        ChatBot(chatroom=sys.argv[1])
    else:
        ChatBot()

if __name__ == '__main__':
    main()
