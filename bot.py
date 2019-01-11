# -*- coding: utf-8 -*-
"""
Python Slack Bot class for use with the pythOnBoarding app
Original code structure Courtesy Shannon Burns
https://github.com/slackapi/Slack-Python-Onboarding-Tutorial/blob/master/LICENSE
"""
import os
import message
import re
import subprocess
import docker_parser

from circleclient import circleclient
from slackclient import SlackClient

# To remember which teams have authorized your app and what tokens are
# associated with each team, we can store this information in memory on
# as a global object. When your bot is out of development, it's best to
# save this in a more persistant memory store.
authed_teams = {}
GIT_SUPPORTED = ["status", "add", "commit"]

# Enable/Disable printing debug
DPRINT=True

def dprint(msg):
    """
    Debug print. Set DPRINT=True to enable debug printing
    """
    if DPRINT:
        print(msg)

class Bot(object):
    """ Instanciates a Bot object to handle Slack onboarding interactions."""
    def __init__(self):
        super(Bot, self).__init__()
        self.name = "appone"
        self.emoji = ":robot_face:"
        # When we instantiate a new bot object, we can access the app
        # credentials we set earlier in our local development environment.
        # Scopes provide and limit permissions to what our app
        # can access. It's important to use the most restricted
        # scope that your app will need.
        self.oauth = {"client_id": os.environ.get("SLACK_CLIENT_ID"),
                      "client_secret": os.environ.get("SLACK_CLIENT_SECRET"),
                      "scope": os.environ.get("SLACK_BOT_SCOPE","bot")}
        self.user_name_map = {}
        self.channel_data_map = {}

        # NOTE: Python-slack requires a client connection to generate
        # an oauth token. We can connect to the client without authenticating
        # by passing an empty string as a token and then reinstantiating the
        # client with a valid OAuth token once we have one.
 
        bot_oauth_default="xoxb-445512136161-446113431922-MbaetJ62o8U1mr4u91BTauSq"
        bot_oauth_token = os.environ.get("SLACK_BOT_OAUTH_ACCESS",bot_oauth_default)
        #dprint ("calling SlackClient with token %s" % (bot_oauth_token,))
        self.client = SlackClient(bot_oauth_token)

        self.circleci_user_token = os.environ['CIRCLECI_HODOLIZER_TOKEN']
        self.circleci_project_token = os.environ['CIRCLECI_HB_LITTLEBOT_TOKEN']
        self.circleci_client = circleclient.CircleClient(self.circleci_user_token)
        self.circleci_repo_list = []

        # We'll use this dictionary to store the state of each message object.
        # In a production envrionment you'll likely want to store this more
        # persistantly in  a database.
        self.messages = {}

    def get_all_users_map(self):
        """
        Get all users for which we have visibility and create a dictionary map 
        by user 'id' to user information. 
        """

        slack_client = self.client

        api_call = slack_client.api_call("users.list")
        users = api_call.get('members')
        if api_call.get('ok'):
            for user in users:
                self.user_name_map[user['id']] = user
        return self.user_name_map

    def get_all_channel_data_map(self):
        """
        Get all channels for which we have visibility and create a dictionary map 
        by channels 'id' to channels information. 
        """

        slack_client = self.client

        api_call = slack_client.api_call("channels.list")
        channels = api_call.get('channels')
        if api_call.get('ok'):
            for chan in channels:
                self.channel_data_map[chan['id']] = chan
        return self.channel_data_map

    def get_channel_name_map(self):
        """
            Use the self.channel_name_map created by get_all_channel_map()
            to return a map with just id:name mappings
        """
        channel_id_name_map = {}
        all_channel_map = self.get_all_channel_data_map()
        if all_channel_map:
            for id, data in all_channel_map.items():
                channel_id_name_map[data["name"]] = id
            return channel_id_name_map
        else:
            dprint ("No channel mappings could be found")
            
    def get_bot_userid(self, bot_name):
        # Courtesy of Twilio
        # https://www.twilio.com/blog/2016/05/add-phone-calling-slack-python.html

        # retrieve all users so we can find our bot
        users = self.get_all_users_map()
        if users:
            for uid, udata in users.items():
                u_name = udata["profile"].get("display_name")
                if not u_name:
                    u_name = udata["profile"].get("real_name")
                #dprint ("got user: %s \t id: %s" % (u_name, uid))
                    
                #dprint ("%s" % str(udata))
            for user in users:
                if 'name' in users[user] and users[user].get('name') == bot_name:
                    bot_id = users[user]["profile"].get('bot_id', user)
                    #dprint("Bot ID for '" + users[user]['name'] + "' is " + bot_id)
                    #dprint("Bot Record: %s" % str(users[user]))
                    return bot_id
        dprint("could not find bot user with the name " + bot_name)
        return ''

    def auth(self, code):
        """
        Authenticate with OAuth and assign correct scopes.
        Save a dictionary of authed team information in memory on the bot
        object.

        Parameters
        ----------
        code : str
            temporary authorization code sent by Slack to be exchanged for an
            OAuth token

        """
        # After the user has authorized this app for use in their Slack team,
        # Slack returns a temporary authorization code that we'll exchange for
        # an OAuth token using the oauth.access endpoint
        dprint ("\ncalling auth client.api_call\n")
        auth_response = self.client.api_call(
                                "oauth.access",
                                client_id=self.oauth["client_id"],
                                client_secret=self.oauth["client_secret"],
                                code=code
                                )
        dprint ("\ncclient.api_call returns %s\n" % (str(auth_response),))
        # To keep track of authorized teams and their associated OAuth tokens,
        # we will save the team ID and bot tokens to the global
        # authed_teams object
        team_id = auth_response["team_id"]
        authed_teams[team_id] = {"bot_token":
                                 auth_response["bot"]["bot_access_token"]}
        # Then we'll reconnect to the Slack Client with the correct team's
        # bot token
        self.client = SlackClient(authed_teams[team_id]["bot_token"])

        

    def open_dm(self, user_id):
        """
        Open a DM to send a welcome message when a 'team_join' event is
        recieved from Slack.

        Parameters
        ----------
        user_id : str
            id of the Slack user associated with the 'team_join' event

        Returns
        ----------
        dm_id : str
            id of the DM channel opened by this method
        """
        new_dm = self.client.api_call("im.open",
                                      user=user_id)
        dprint("\nOpen DM to user %s channel %s\n" % (user_id, str(new_dm["channel"])))
        #dprint ("\nnew_dm: %s\n" % str(new_dm))
        dm_id = new_dm["channel"]["id"]
        return dm_id

    def get_message_object(self, team_id, user_id, message_type=None):

        # We've imported a Message class from `message.py` that we can use
        # to create message objects for each onboarding message we send to a
        # user. We can use these objects to keep track of the progress each
        # user on each team has made getting through our onboarding tutorial.

        # First, we'll check to see if there's already messages our bot knows
        # of for the team id we've got.
        if self.messages.get(team_id):
            # Then we'll update the message dictionary with a key for the
            # user id we've recieved and a value of a new message object
            self.messages[team_id].update({user_id: message.Message(message_type=message_type)})
        else:
            # If there aren't any message for that team, we'll add a dictionary
            # of messages for that team id on our Bot's messages attribute
            # and we'll add the first message object to the dictionary with
            # the user's id as a key for easy access later.
            self.messages[team_id] = {user_id: message.Message(message_type=message_type)}
        message_obj = self.messages[team_id][user_id]
        # Then we'll set that message object's channel attribute to the DM
        # of the user we'll communicate with
        message_obj.channel = self.open_dm(user_id)
        return message_obj

    def help_message(self, team_id, user_id, message_text):
        """
        Create and send an onboarding welcome message to new users. Save the
        time stamp of this message on the message object for updating in the
        future.

        Parameters
        ----------
        team_id : str
            id of the Slack team associated with the incoming event
        user_id : str
            id of the Slack user associated with the incoming event

        """
        message_type = "helpmsg"
        message_obj = self.get_message_object(team_id, user_id, message_type=message_type)
        message_obj.text = message_text
        post_message = self.client.api_call("chat.postMessage",
                                            channel=message_obj.channel,
                                            username=self.name,
                                            icon_emoji=self.emoji,
                                            text=message_obj.text,
                                            )
        timestamp = post_message["ts"]
        # We'll save the timestamp of the message we've just posted on the
        # message object which we'll use to update the message after a user
        # has completed an onboarding task.
        message_obj.timestamp = timestamp

    def git_usage_message(self):

        return ("""I'm sorry. I don't understand your git command.
I understand git [%s] if you would like to try one of those.
Commit also requires a -m commit_message""" % "|".join(GIT_SUPPORTED))

    def git_handler(self, team_id, user_id, incoming_text):
        """
        Get the git status of this project. 

        Parameters
        ----------
        team_id : str
            id of the Slack team associated with the incoming event
        user_id : str
            id of the Slack user associated with the incoming event
        incoming_text: str
            The git request string

        """

        message_type = "git_handler"
        message_obj = self.get_message_object(team_id, user_id, message_type)

        # Find the action immediately following the git command.
        # git status, git add, git commit are curently supported. 
        p2 = re.compile(r"(?<=\bgit\s)(\w+)")
        match_obj = p2.search(incoming_text)
        if match_obj:
            git_action = match_obj.group()
        bad_command = False
        if git_action and git_action in ['status', 'add', 'commit']:
            arg_string = ''
            if git_action == 'commit':
                # We need a commit message flagged with -m
                flag_pos = incoming_text.find("-m")
                if flag_pos >= 0:
                    arg_string = '-m "%s"' % incoming_text[flag_pos + len("-m"):]
                else:
                    # Can't do a commit without a commit message
                    bad_command = True
            elif git_action == 'add':
                # We only commit the whole directory
                arg_string = " ."
            if not bad_command:
                p = subprocess.Popen('git %s %s' % (git_action, arg_string), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                for line in p.stdout.readlines():
                    message_obj.text += "%s" % line
                retval = p.wait()
            else: # git_action undefined. 
                message_obj.text = self.git_usage_message()
                retval = 1
        else:
            retval = 1

        post_message = self.client.api_call("chat.postMessage",
                                            channel=message_obj.channel,
                                            username=self.name,
                                            icon_emoji=self.emoji,
                                            text=message_obj.text,
                                            )
        if "ts" in post_message:
            timestamp = post_message["ts"]
            message_obj.timestamp = timestamp
        else:
            dprint ("post_message: %s" % str(post_message))
        return retval

    def docker_handler(self, team_id, user_id, incoming_text):
        """
        Get the docker command and handle it. 

        Parameters
        ----------
        team_id : str
            id of the Slack team associated with the incoming event
        user_id : str
            id of the Slack user associated with the incoming event
        incoming_text: str
            The docker request string

        """

        message_type = "docker_handler"
        message_obj = self.get_message_object(team_id, user_id, message_type)

        # Find the action immediately following the docker command.
        # docker container ls, docker image ls are curently supported. 
        docker_action = docker_parser.parse_command(incoming_text)
        dprint ("Got docker_action: %s from incoming text: %s" % (docker_action, incoming_text))
        if docker_action[:len('docker')] == 'docker':
            dprint ("running docker action: %s" % (docker_action))
            p = subprocess.Popen('%s' % docker_action, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in p.stdout.readlines():
                message_obj.text += "%s" % line
            retval = p.wait()
        else:
            message_obj.text = docker_action # The usage message
            retval = 0

        post_message = self.client.api_call("chat.postMessage",
                                            channel=message_obj.channel,
                                            username=self.name,
                                            icon_emoji=self.emoji,
                                            text=message_obj.text,
                                            )
        timestamp = post_message["ts"]
        return retval

    def get_circleci_repos(self):
        """
        Get the circleci repositories that the bot user is following
        returns a list of repo names
        """
        project_info_list = self.circleci_client.projects.list_projects()
        for project_dict in project_info_list:
            self.circleci_repo_list.append(project_dict["reponame"])

    def circleci_build_info(self, raw_results):
        """
        Returns selected circleci information about the last build.

        Input is raw_results from a call to circleci build.recent
        """
        if not isinstance(raw_results, dict):
            dprint ("build info: Not a dict: %s" % (str(raw_results),))
            return None
        else:
            rr = raw_results

            build_version = rr["platform"]
            build_url = rr["build_url"]
            commit_date = rr["committer_date"]
            author_name = rr["author_name"]
            build_num = rr["build_num"]
            outcome = rr["outcome"] 

            committer_names = []
            commit_urls = []
            commit_subjects = []
            commit_dates = []

            for commit_detail in rr.get("all_commit_detail",[]):
                committer_names.append(rr.get("committer_name", "Not found"))
                commit_urls.append(rr.get("commit_url", "Not found"))
                commit_subjects.append(rr.get("subject", "Not found"))
                commit_dates.append(rr.get("committer_date", "Not found"))

            # Should html'ify this for return
            results_string = """
Build Version: %(build_version)s\n
Build URL: %(build_url)s\n
Commit Date: %(commit_date)s\n
Author Name: %(author_name)s\n
Build Number: %(build_num)s\n """ % locals()

            for commit_subject, commiter_name, commit_url, commiter_date in list(zip(commit_subjects,
                committer_names, 
                commit_urls,
                commit_dates)):
                results_string = results_string + """
Commit Subject: %s\n
Committer Name: %s\n
Commit Date: %s\n
Commit URL: %s\n """ % (commit_subject, commier_name, commiter_date, commit_url)

            return results_string
            
            
    def circleci_handler(self, team_id, user_id, incoming_text):

        #my_repo_name = "HB_Littlebot" 
        self.get_circleci_repos()
        repo_name = ''
        outgoing_text = "Sorry, I could not determine which repo you wanted.\n" \
                        "I know about these: %s" % (str(", ".join(self.circleci_repo_list),))
        message_type = "helpmsg"

        if self.circleci_repo_list:

            # Retrieve User data
            user_info = self.circleci_client.user.info()
            dprint ("\nUSER info: %s\n" % (str(user_info),))
            user_name = user_info['login']

            incoming_text = incoming_text.lower()

            for repo in self.circleci_repo_list:
                if incoming_text.find(repo.lower()) >= 0:
                        repo_name = repo
            if repo_name:
                if incoming_text.find("last build") >= 0:
                    last_build = self.circleci_client.build.recent(user_name, repo_name, branch='master')
                    if last_build:
                        outgoing_text = self.circleci_build_info(last_build[0])
                        print("build_info: %s" % (str(last_build),))
                        message_type = "circleci_last_build"
                    else:
                        message_type = "circleci_handler"
                        outgoing_text = "Sorry, I could not get that information.\n" \
                                        "I know about these repos: %s" % (str(", ".join(self.circleci_repo_list),))
                        message_type = "helpmsg"

        dprint ("circleci_handler returning %s" % outgoing_text)
        message_obj = self.get_message_object(team_id, user_id, message_type=message_type)
        message_obj.text = outgoing_text

        post_message = self.client.api_call("chat.postMessage",
            channel=message_obj.channel,
            username=self.name,
            icon_emoji=self.emoji,
            text=message_obj.text,
            )
        timestamp = post_message["ts"]
        # We'll save the timestamp of the message we've just posted on the
        # message object which we'll use to update the message after a user
        # has completed an onboarding task.
        message_obj.timestamp = timestamp
            
                
        """
        # Retrieve information about projects
        project_info_list = self.circleci_client.projects.list_projects()
        #dprint ("\nPROJECT info: %s\n" % (str(project_info),))
        for project_dict in project_info_list:
            my_repo_name = "HB_Littlebot"
            if project_dict["reponame"] == my_repo_name:
                dprint ("\nPROJECT info: %s\n" % (str(project_dict),))
            repo_name = project_dict["reponame"]
        dprint ("searching for %s" % repo_name)

        # Retrieve last 10 builds of branch master
        recent_builds = self.circleci_client.build.recent(user_name, repo_name, branch='master')
        for key, val in recent_builds[0].items():
            dprint ("key:%s\n\t%s" % (key,val))
        """

    def echo_message(self, team_id, user_id, incoming_text):
        """
        Create and send an onboarding welcome message to new users. Save the
        time stamp of this message on the message object for updating in the
        future.

        Parameters
        ----------
        team_id : str
            id of the Slack team associated with the incoming event
        user_id : str
            id of the Slack user associated with the incoming event

        """

        message_type = "echo_message"
        message_obj = self.get_message_object(team_id, user_id, message_type)
        # We'll use the message object's method to create the attachments that
        # we'll want to add to our Slack message. This method will also save
        # the attachments on the message object which we're accessing in the
        # API call below through the message object's `attachments` attribute.
        message_obj.create_attachments()

        user_name = self.user_name_map[user_id]['profile']['display_name']

        dprint ("IN Echo handler with message: %s" % (incoming_text,))
        outgoing_text = "Hi %s. You said %s." %  (user_name,incoming_text)
        if incoming_text.lower().find("hunka hunka") >= 0:
            outgoing_text += " Yes, I have a burning love for bots too."
        dprint ("Looking in %s for id %s" % (self.user_name_map[user_id]['profile'], user_id))
        message_obj.text  = outgoing_text
        post_message = self.client.api_call("chat.postMessage",
                                            channel=message_obj.channel,
                                            username=self.name,
                                            icon_emoji=self.emoji,
                                            text=message_obj.text,
                                            )
        timestamp = post_message["ts"]
        # We'll save the timestamp of the message we've just posted on the
        # message object which we'll use to update the message after a user
        # has completed an onboarding task.
        message_obj.timestamp = timestamp

    def update_pin(self, team_id, user_id):
        """
        Update onboarding welcome message after recieving a "pin_added"
        event from Slack. Update timestamp for welcome message.

        Parameters
        ----------
        team_id : str
            id of the Slack team associated with the incoming event
        user_id : str
            id of the Slack user associated with the incoming event

        """
        # These updated attachments use markdown and emoji to mark the
        # onboarding task as complete
        completed_attachments = {"text": ":white_check_mark: "
                                         "~*Pin this message*~ "
                                         ":round_pushpin:",
                                 "color": "#439FE0"}
        # Grab the message object we want to update by team id and user id
        #message_obj = self.messages[team_id].get(user_id)
        # Grab the message object we want to update by team id and user id
        if team_id in self.messages and user_id in self.messages[team_id]:
            message_obj = self.messages[team_id].get(user_id)
        else:
            message_type = "update_pin"
            message_obj = self.get_message_object(team_id, user_id, message_type)
        # Update the message's attachments by switching in incomplete
        # attachment with the completed one above.
        message_obj.pin_attachment.update(completed_attachments)
        # Update the message in Slack
        post_message = self.client.api_call("chat.update",
                                            channel=message_obj.channel,
                                            ts=message_obj.timestamp,
                                            text=message_obj.text,
                                            attachments=message_obj.attachments
                                            )
        # Update the timestamp saved on the message object
        message_obj.timestamp = post_message["ts"]

    def update_share(self, team_id, user_id):
        """
        Update onboarding welcome message after recieving a "message" event
        with an "is_share" attachment from Slack. Update timestamp for
        welcome message.

        Parameters
        ----------
        team_id : str
            id of the Slack team associated with the incoming event
        user_id : str
            id of the Slack user associated with the incoming event

        """
        # These updated attachments use markdown and emoji to mark the
        # onboarding task as complete
        completed_attachments = {"text": ":white_check_mark: "
                                         "~*Share this Message*~ "
                                         ":mailbox_with_mail:",
                                 "color": "#439FE0"}
        # Grab the message object we want to update by team id and user id
        #message_obj = self.messages[team_id].get(user_id)
        # Grab the message object we want to update by team id and user id
        if team_id in self.messages and user_id in self.messages[team_id]:
            message_obj = self.messages[team_id].get(user_id)
        else:
            message_type = "update_share"
            message_obj = self.get_message_object(team_id, user_id, message_type)
        # Update the message's attachments by switching in incomplete
        # attachment with the completed one above.
        message_obj.share_attachment.update(completed_attachments)
        # Update the message in Slack
        post_message = self.client.api_call("chat.update",
                                            channel=message_obj.channel,
                                            ts=message_obj.timestamp,
                                            text=message_obj.text,
                                            attachments=message_obj.attachments
                                            )
        # Update the timestamp saved on the message object
        message_obj.timestamp = post_message["ts"]

    def send_message(self, team_id, user_id, message_text):
        """
        Send a message on the part of the app for something that doesn't have
        explicit handling.

        Parameters
        ----------
        team_id : str
            id of the Slack team associated with the incoming event
        user_id : str
            id of the Slack user associated with the incoming event
        message : A text message to send to the caller. 
        """
    
        # Grab the message object we want to update by team id and user id
        #message_obj = self.messages[team_id].get(user_id)
        # Grab the message object we want to update by team id and user id
        if team_id in self.messages and user_id in self.messages[team_id]:
            message_obj = self.messages[team_id].get(user_id)
        else:
            message_type = "send_message"
            message_obj = self.get_message_object(team_id, user_id, message_type)
        # Update the message in Slack
        message_obj.text = message_text
        post_message = self.client.api_call("chat.update",
                                            channel=message_obj.channel,
                                            ts=message_obj.timestamp,
                                            text=message_obj.text,
                                            )
        # Update the timestamp saved on the message object
        message_obj.timestamp = post_message["ts"]
