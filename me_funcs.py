'''
these functions define responses which play back only
when the bot is spoken to
'''
from chatresponder import ChatResponder
import datetime
import random
import re
import settings
import yaml


responder = ChatResponder()


#this bitch needs an off switch
@responder(r'^(be )?quiet\b')
def start_silence(bot, m, text, user):
    bot.silent = True
    return 'sorry. i\'ll put a lid on it.'


#and an on switch
@responder(r'^okay,?')
def end_silence(bot, m, text, user):
    bot.silent = False
    bot.timeout = None
    return 'thanks, %s' % user.lower()


#let's also support a timeout
@responder(r'\b(that\'?s )?enough\b|\btake a break\b|\bhush\b')
def set_timeout(bot, m, text, user):
    bot.timeout = datetime.datetime.now() + datetime.timedelta(minutes=10)
    return 'i\'m gonna stay quiet for a bit.'


#learn new things...
#   "chatbot, learn: a = b"
@responder(r'\w+[,\.]*\s+learn:\s*([^=]+)\s*=\s*(.+)')
def learn(bot, m, text, user):
    exp = str(m.group(1)).strip()
    resp = str(m.group(2)).strip()
    bot.learning = (exp, resp)
    return 'okay, got it.'


#save what you've learned
#   "keep it, chatbot"
@responder(r'keep it')
def keep_learned(bot, m, text, user):
    if bot.learning:
        bot.chat_responds.append(bot.learning)
        bot.learning = None
        f = open('generic_responds.yaml', 'w')
        f.write(yaml.dump(bot.chat_responds))
        f.close()
        return 'committed to memory.'
    else:
        return 'i\'m not learning anything.'


#erase the last thing you learned
#    "forget it, chatbot"
@responder(r'forget it')
def forget_learned(bot, m, text, user):
    if bot.learning:
        bot.learning = None
        return 'forgotten.'
    else:
        return 'i\'m not learning anything.'


#a little moral support
@responder(r'\bback me up\b,?\s({0})|(?:do|would)n\'t you (?:say|agree),?\s({0})|isn\'?t that right,?\s{0}'.format('|'.join(settings.my_names)))
def moral_support(bot, m, text, user):
    return [
            '{0} is right.',
            'I agree with {0}.',
            'Damn straigh, {0}.',
            'Hell yeah, {0}, I\'m with you.',
        ][random.randint(0, 2)].format(user.title())


#chinese telephone
@responder(r'^(%s)[,\:]?\s(ask)\s+([\w]+)\s*(if|[\.,\:])?(.+)' % '|'.join(settings.my_names),
        r'^(%s)[\,\:]?\s(tell)\s+([\w]+)\s*(that|[\.,\:])?(.+)' % '|'.join(settings.my_names))
def chinese_telephone(bot, m, text, user):
    ''' pass a private message via groupchat '''
    target = m.group(3).strip()
    if target not in settings.aliases.keys():
        return "Sorry, I don't know who %s is." % target

    print m.groups()

    target = settings.aliases[target]
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
    bot.send_private_message(recipient=target, message=payload)
    if m.group(2) == 'tell':
        return 'telling %s, "%s"' % (target, payload)
    else:
        return 'asking %s, "%s"' % (target, payload)


#TODO maybe add swapwords?   [x=y]
