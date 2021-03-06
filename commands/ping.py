# -*- coding: utf-8 -*-
"""
Created on Thu Jan 11 21:19:47 2018

@author: 14flash
"""

from commands import command
import re

class PingCommand(command.DirectOnlyCommand, command.BenchmarkableCommand):
    '''PingCommand is a command that responds to the word "ping" as a quick way
    of checking that the bot is working correctly.'''

    def matches(self, message):
        # match objects have a boolean value, so we can just return
        return re.search(r'\bping\b', message.content, re.IGNORECASE)

    def action(self, message, send_func):
        yield from send_func(message.channel, "PONG.")
