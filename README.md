chatbot
=======
a chatbot for jabber multi-user chatrooms


SETUP
-----
Use pip to install requirements.txt

Edit settings.py

Enjoy!


CUSTOMIZATION
-------------
For simple responses, chatbot can learn on the fly.
Just type "chatbot, learn: {expression} = {response}"
where {expression} is a regex-compatible search string,
and {response} is the text chatbot should use to reply.

When you like something chatbot has learned, you can
say "keep it, chatbot" and that expression/response pair
will be added to the .yaml file and saved forever.

For more complicated responses that requires some 
programming (anything more than a simple response)
just define a new function in the appropriate responds.py
file, following the example of functions that are
already defined.

The decorator specifies one or more regex patterns to
match against. If a match is found, the function will
be run. If it returns text, that text is written to the
chatroom. Otherwise, processing continues.

