# coding=utf-8
'''
settings for the chatbot
'''

chat_domain = 'chat.google.com'

#chat settings
chatroom = 'bbq@conference.%s' % chat_domain
username = 'test_username___@google.com'
password = 'test_password'
screen_name = 'The Chat Bot!'

#settings for sending emails
smtp_username = 'chatbot@mail.google.com'
smtp_password = 'examplePW1'
smtp_hostname = 'smtp.gmail.com'
smtp_port = 587

#ignore messages from these users
ignore_from = [
        screen_name,
        screen_name.lower(),
        'chatbot',
        username.lower,
    ]

#TODO names i should respond to
my_names = [
        'chatbot',
    ]

#people i should know about
aliases = {
        #tech
    }
