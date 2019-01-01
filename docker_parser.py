# -*- coding: utf-8 -*-
"""
Python Slack Bot docker parser class for use with the HB Bot
"""
import os
import re
DOCKER_SUPPORTED = ["image", "container"]
SUBCOMMAND_SUPPORTED = ["ls",]

def docker_usage_message():

    return ("I'm sorry. I don't understand your docker command." 
       "I understand docker [%s] if you would like to try one of those." % "|".join(DOCKER_SUPPORTED))

def parse_command(incoming_text):
    """
        incoming_text: A text string to parse for docker commands
        returns: a fully validated docker command
    """

    docker_action = ''

    parse1 = re.compile(r"(?<=\bdocker\s)(\w+)")
    match_obj = parse1.search(incoming_text)
    if match_obj:
        docker_action = match_obj.group()
    if docker_action and docker_action in DOCKER_SUPPORTED:
        parse2 = re.compile(r"(?<=\b%s\s)(\w+)" % docker_action)
        match_obj = parse2.search(incoming_text)
        if match_obj:
            docker_subcommand = match_obj.group()
            if docker_subcommand in SUBCOMMAND_SUPPORTED:
                return "docker %s %s" % (docker_action, docker_subcommand)

    return docker_usage_message()
