# -*- coding: utf-8 -*-
"""
Python Slack Message class for use with the pythOnBoarding bot
Courtesy Shannon Burns
https://github.com/slackapi/Slack-Python-Onboarding-Tutorial/blob/master/LICENSE
"""
# TODO: Fix hack with yaml library for handling unicode encoding issues
import yaml


class Message(object):
    """
    Instanciates a Message object to create and manage
    Slack messages.
    Mainly just a placeholder for later DB backed message handling
    """
    def __init__(self,message_type=None):
        super(Message, self).__init__()
        self.channel = ""
        self.timestamp = ""
        if not message_type:
            self.text = ("Welcome to LittleBot! We're so glad you're here.")
            self.emoji_attachment = {}
            self.pin_attachment = {}
            self.share_attachment = {}
            self.attachments = [self.emoji_attachment,
                                self.pin_attachment,
                            self.share_attachment]
        #elif message_type != 'echo':
        else:
            self.text = ("")
            self.emoji_attachment = {}
            self.pin_attachment = {}
            self.share_attachment = {}
            self.attachments = []


    def create_attachments(self):
        """
        Open JSON message attachments file and create attachments for
        onboarding message. Saves a dictionary of formatted attachments on
        the bot object.
        """
        with open('welcome.json') as json_file:
            json_dict = yaml.safe_load(json_file)
            json_attachments = json_dict["attachments"]
            [self.attachments[i].update(json_attachments[i]) for i
             in range(len(json_attachments))]
