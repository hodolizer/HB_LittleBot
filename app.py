# -*- coding: utf-8 -*-
"""
A routing layer for the LittleBot built using
[Slack's Events API](https://api.slack.com/events-api) in Python
"""
import os
import json
import bot
from flask import Flask, request, make_response, render_template
from slackclient import SlackClient
import urllib

pyBot = bot.Bot()
slack = pyBot.client

app = Flask(__name__)

SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", None)
BOT_USER_NAME = 'appone'

if SLACK_SIGNING_SECRET is None:
    msg = "You must source a file with SLACK_CLIENT_ID," 
    " SLACK_CLIENT_SECRET, SLACK_SIGNING_SECRET and SLACK_BOT_SCOPE defined"
    raise NameError(msg)

# This is used to detect git commands. 
import re
git_regex = re.compile(r"\bgit\s")
docker_regex = re.compile(r"\bdocker\s")

BOT_USER_ID = pyBot.get_bot_userid(BOT_USER_NAME)
print ("\nbot id is %s\n" % (BOT_USER_ID,))


cmap = pyBot.get_channel_name_map()
for chan, name in cmap.items():
    print ("chan: %s name: %s" % (chan, name))

def _event_handler(event_type, slack_event):
    """
    A helper function that routes events from Slack to our Bot
    by event type and subtype.


    Returns
    ----------
    obj
        Response object with 200 - ok or 500 - No Event Handler error

    """
    team_id = slack_event["team_id"]
    #print ("\nslack_event: %s" % (str(slack_event),))
    if "bot_id" in slack_event["event"]:
        user_id = slack_event["event"].get("bot_id")
    else:
        user_id = slack_event["event"].get("user")

    if "text" in slack_event["event"]:
        incoming_text = slack_event["event"]["text"]
    else:
        incoming_text = ''

    if event_type == "message" \
        and user_id == BOT_USER_ID:
        print ("BAILING!!!!!!!!!!!!!!!!!!!!!!")
        return make_response("", 200, {"X-Slack-No-Retry": 1})

    allowed_event_types = ['message', 'app_mention', 'pin_added', 'reaction_added', 'team_join']
    message_event_types = ['message', 'app_mention']

    if event_type not in allowed_event_types:
        message = "Say what? Here's what you can say to me\n %s" % "\n".join(handled_events)
        return make_response(message, 200,)

    print ("checking for regex in %s" % incoming_text)
    if event_type in ["message", "app_mention"] and git_regex.search(incoming_text):
        print ("regex check True %s" % incoming_text)
    else:
        print ("regex check False %s" % incoming_text)
        

    # ================ Team Join Events =============== #
    # When the user first joins a team, the type of event will be team_join
    #if event_type == "team_join":
    if event_type in message_event_types and incoming_text.lower().find("startitoff") >= 0:
        # Send the onboarding message
        pyBot.onboarding_message(team_id, user_id)
        return make_response("Onboarding Message Sent", 200,)

    elif event_type in message_event_types \
        and (incoming_text.find("echo") >= 0 
        or incoming_text.find("hunka hunka") >= 0) \
        and user_id != BOT_USER_ID:

        # Send the onboarding message
        pyBot.echo_message(team_id, user_id, incoming_text)
        return make_response("Echo Message Sent", 200,)

    elif event_type in message_event_types and git_regex.search(incoming_text):

        # Call the bot git handler
        print ("Calling git_handler")
        ret = pyBot.git_handler(team_id, user_id, incoming_text)
        print ("After git_handler")
        return make_response("Status Mesage Sent", 200,)

    elif event_type in message_event_types and docker_regex.search(incoming_text):
        # Call the bot git handler
        print ("Calling docker_handler")
        ret = pyBot.docker_handler(team_id, user_id, incoming_text)
        print ("After docker_handler")
        return make_response("Status Mesage Sent", 200,)

    # ============== Share Message Events ============= #

    # ============== Share Message Events ============= #
    # If the user has shared the message, the event type will be
    # message. We'll also need to check that this is a message that has been
    # shared by looking into the attachments for "is_shared".
    elif event_type in message_event_types and slack_event["event"].get("attachments"):
        if slack_event["event"]["attachments"][0].get("is_share"):
            # Update the onboarding message and check off "Share this Message"
            pyBot.update_share(team_id, user_id)
            return make_response("Welcome message updates with shared message",
                                 200,)

    # ============= Reaction Added Events ============= #
    # If the user has added an emoji reaction to the onboarding message
    elif event_type == "reaction_added":
        # Update the onboarding message
        pyBot.update_emoji(team_id, user_id)
        return make_response("Welcome message updates with reactji", 200,)

    # =============== Pin Added Events ================ #
    # If the user has added an emoji reaction to the onboarding message
    elif event_type == "pin_added":
        # Update the onboarding message
        pyBot.update_pin(team_id, user_id)
        return make_response("Welcome message updates with pin", 200,)

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    elif event_type in message_event_types: # no other message type found
        git_supported = "|".join(bot.GIT_SUPPORTED)
        handled_events = ["startitoff", "echo", "git %s" % (git_supported,)]
        message = "Say what? Here's what you can say to me\n%s" % "\n".join(handled_events)
        print ("writing msg: %s" % message)
        send_message(team_id, user_id, message)
        # Return a helpful error message
        return make_response(message, 200, {"X-Slack-No-Retry": 1})

    else:
        raise RuntimeError("%s" % str(slack_event))


@app.route("/install", methods=["GET"])
def pre_install():
    """This route renders the installation page with 'Add to Slack' button."""
    # Since we've set the client ID and scope on our Bot object, we can change
    # them more easily while we're developing our app.
    client_id = pyBot.oauth["client_id"]
    scope = pyBot.oauth["scope"]
    # Our template is using the Jinja templating language to dynamically pass
    # our client id and scope
    return render_template("install.html", client_id=client_id, scope=scope)


@app.route("/thanks", methods=["GET", "POST"])
def thanks():
    """
    This route is called by Slack after the user installs our app. It will
    exchange the temporary authorization code Slack sends for an OAuth token
    which we'll save on the bot object to use later.
    To let the user know what's happened it will also render a thank you page.
    """
    # Let's grab that temporary authorization code Slack's sent us from
    # the request's parameters.
    code_arg = request.args.get('code')
    # The bot's auth method to handles exchanging the code for an OAuth token
    pyBot.auth(code_arg)
    return render_template("thanks.html")


@app.route("/listening", methods=["GET", "POST"])
def hears():
    """
    This route listens for incoming events from Slack and uses the event
    handler helper function to route events to our Bot.
    """
    slack_event = json.loads(request.data)
    if "event" in slack_event:
        if "bot_id" in slack_event:
            return make_response("", 200, {"content_type":
                                             "application/json"
                                             })
        

    # ============= Slack URL Verification ============ #
    # In order to verify the url of our endpoint, Slack will send a challenge
    # token in a request and check for this token in the response our endpoint
    # sends back.
    #       For more info: https://api.slack.com/events/url_verification
    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                             })

    # ============ Slack Token Verification =========== #
    # We can verify the request is coming from Slack by checking that the
    # verification token in the request matches our app's settings
    if SLACK_SIGNING_SECRET != slack_event.get("token"):
        message = "Invalid Slack verification token: %s \npyBot has: \
                   %s\n\n" % (slack_event["token"], SLACK_SIGNING_SECRET)
        # By adding "X-Slack-No-Retry" : 1 to our response headers, we turn off
        # Slack's automatic retries during development.
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    # ====== Process Incoming Events from Slack ======= #
    # If the incoming request is an Event we've subcribed to
    # print ("Process Incoming slack event: %s" % str(slack_event))
    #if "event" in slack_event and slack_event["username"] != user_id: 
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        # Then handle the event by event_type and have your bot respond
        return _event_handler(event_type, slack_event)
    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


if __name__ == '__main__':
    app.run(debug=True)
