from chatbot import ChatBot, responder, me_responder
import datetime
import random
import re
import sys


class Examplebot(ChatBot):

    username = 'exampleuser@gmail.com'
    password = 'examplepass'
    chatroom = 'private-chat-463D4483-BC3C-43F9-988A-DFAAAD1A0BD0'

    smtp_username = ''
    smtp_password = ''
    smtp_hostname = ''
    smtp_port = ''

    screen_name = 'Examplebot'

    ignore_from = [
            screen_name,
            screen_name.lower(),
            'chatbot',
            username.lower,
        ]

    my_names = [
            'chatbot',
            'examplebot',
        ]

    aliases = {
        #tech
    }

    #a little moral support
    @responder(r'\bback me up\b,?\s({0})|(?:do|would)n\'t you (?:say|agree),?\s({0})|isn\'?t that right,?\s{0}'.format('|'.join(my_names)))
    def moral_support(self, m, text, user):
        return [
                '{0} is right.',
                'I agree with {0}.',
                'Damn straight, {0}.',
                'Hell yeah, {0}, I\'m with you.',
            ][random.randint(0, 2)].format(user.title())

    #chinese telephone
    @responder(r'^(%s)[,\:]?\s(ask)\s+([\w]+)\s*(if|[\.,\:])?(.+)' % '|'.join(my_names),
            r'^(%s)[\,\:]?\s(tell)\s+([\w]+)\s*(that|[\.,\:])?(.+)' % '|'.join(my_names))
    def chinese_telephone(self, m, text, user):
        ''' pass a private message via groupchat '''
        target = m.group(3).strip()
        if target not in self.aliases.keys():
            return "Sorry, I don't know who %s is." % target

        print m.groups()

        target = self.aliases[target]
        payload = m.group(5).strip()

        if m.group(2) == 'ask':
            if m.group(4) == 'if':
                payload = re.sub(r'^s?he(\'s| is)', "are you", payload)
                payload = re.sub(r'^(his|her|the)\s*(\w)(\'s| is)', "is \1", payload)
            if payload[-1] != '?':
                payload += '?'

        payload = re.sub(r'\b(his|her)\b', "your", payload)
        payload = re.sub(r'\bs?he\'s\b', "you're", payload)
        payload = re.sub(r'\bs?he\b', "you", payload)

        #still debugging
        self.send_private_message(recipient=target, message=payload)
        if m.group(2) == 'tell':
            return 'telling %s, "%s"' % (target, payload)
        else:
            return 'asking %s, "%s"' % (target, payload)

    #find-replace shenanigans
    @responder(r'^s/([^/]+)/([^/]+)')
    def find_replace(self, m, text, user):
        #don't update the prev_message
        self.curr_message = None
        return re.sub(m.group(1), m.group(2), self.prev_message)

    #where are the cupcakes?
    @responder(r'^where(\'s| is| are) th(os)?e cupcake', '^what\'?s the word on the cupcake')
    def cupcake_status(self, m, text, user):
        t = self.get_last_tweet('courageouscakes')
        if t:
            return 'last tweet: %s' % t

    #swear warnings
    @responder(r'\bjesus h|fuck|shit')
    def swear_warnings(self, m, text, user):
        return [
                'watch it with the language, bub',
                'hey, watch the language, {0}!',
                'ease up on the word choice, eh?',
            ][random.randint(0, 2)].format(user.lower())

    #join in the laughter
    @responder(r'haha')
    def join_laughter(self, m, text, user):
        #only join once in a 5-minute period
        if not self.join_laughter.data or (
                self.join_laughter.data + datetime.timedelta(minutes=5) < datetime.datetime.now()):
            self.join_laughter.data = datetime.datetime.now()
            return '%s%s' % (
                    'ha' * random.randint(2, 5),
                    '!' * random.randint(1, 4)
                )

    #join the back-slapping
    @responder(r'^(w00t|yay|awesome|holla|kick[ -]?ass)\!*$')
    def high_five(self, m, text, user):
        #only join once in a 5-minute period
        if not self.high_five.data or (
                self.high_five.data + datetime.timedelta(minutes=5) < datetime.datetime.now()):
            self.high_five.data = datetime.datetime.now()
            return [
                'yeah!', 'yay!', 'awesome!', 'solid!', 'w00t!', 'hellz yeah!'
                ][random.randint(0, 5)]

    #find palindromes
    @responder(r'.{6,}')
    def find_palindrome(bot, m, text, user):
        nopunc = re.sub(r'\W+', '', text.lower())
        if nopunc == nopunc[::-1]:
            return 'Wow, {0}! That was a palindrome!'.format(user)

    @responder(r'^help\b')
    def show_help(self, matches, text, user):
        return "there is no help."

    @me_responder(r'^help\b')
    def show_chatbot_help(self, matches, text, user):
        return "I'll see what I can do."


#=======================
def main():
    ''' release the kraken... '''
    if len(sys.argv) > 1:
        Examplebot(chatroom=sys.argv[1])
    else:
        Examplebot()

if __name__ == '__main__':
    main()
