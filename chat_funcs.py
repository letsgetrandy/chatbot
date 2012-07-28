from chatresponder import ChatResponder
import datetime
import random
import re
'''
these functions define responses that can go to anyone
as long as the bot is not in silent mode
'''
import twitter


responder = ChatResponder()


#helper, to get twitter status
def get_last_tweet(twitter_handle):
    try:
        api = twitter.Api()
        timeline = api.GetUserTimeline(twitter_handle)
        tweet = timeline[0]
        return tweet
    except:
        return None


#find-replace shenanigans
@responder(r'^s/([^/]+)/([^/]+)')
def find_replace(bot, m, text, user):
    #don't update the prev_message
    bot.curr_message = None
    return re.sub(m.group(1), m.group(2), bot.prev_message)


#fetch a tweet
@responder(r'^last tweet from \@(\S+)')
def cupcake_status(bot, m, text, user):
    t = get_last_tweet(m.group(1))
    if t:
        return 'last tweet from %s: %s' % (m.group(1), t)


#swear warnings
@responder(r'\bjesus h|fuck|shit')
def swear_warnings(bot, m, text, user):
    return [
            'watch it with the language, bub',
            'hey, watch the language, {0}!',
            'ease up on the word choice, eh?',
        ][random.randint(0, 2)].format(user.lower())


#join in the laughter
@responder(r'haha')
def join_laughter(bot, m, text, user):
    #only join once in a 5-minute period
    if not join_laughter.data or (
            join_laughter.data + datetime.timedelta(minutes=5) < datetime.datetime.now()):
        join_laughter.data = datetime.datetime.now()
        return '%s%s' % (
                'ha' * random.randint(2, 5),
                '!' * random.randint(1, 4)
            )


#join the back-slapping
@responder(r'^(w00t|yay|awesome|holla|kick[ -]?ass)\!*$')
def high_five(bot, m, text, user):
    #only join once in a 5-minute period
    if not high_five.data or (
            high_five.data + datetime.timedelta(minutes=5) < datetime.datetime.now()):
        high_five.data = datetime.datetime.now()
        return [
            'yeah!', 'yay!', 'awesome!', 'solid!', 'w00t!', 'hellz yeah!'
            ][random.randint(0, 5)]


#find palindromes
@responder(r'.{6,}')
def find_palindrome(bot, m, text, user):
    nopunc = re.sub(r'\W+', '', text.lower())
    if nopunc == nopunc[::-1]:
        return 'Wow, {0}! That was a palindrome!'.format(user)
