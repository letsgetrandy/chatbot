'''
chat responder
'''
import re


class ChatResponder(list):

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
