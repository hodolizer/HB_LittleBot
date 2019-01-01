"""
Courtesy Shannon Burns
https://github.com/slackapi/Slack-Python-Onboarding-Tutorial/blob/master/LICENSE
"""
import os
from flask import Flask, request
from flask import copy_current_request_context
from slackclient import SlackClient

client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]
oauth_scope = os.environ["SLACK_BOT_SCOPE"]

app = Flask(__name__)


@app.route("/begin_auth", methods=["GET"])
def pre_install():
  return '''
      <a href="https://slack.com/oauth/authorize?scope={0}&client_id={1}">
          Add to Slack
      </a>
 '''.format(oauth_scope, client_id)

@app.route("/finish_auth", methods=["GET", "POST"])
@copy_current_request_context
def post_install():

  # Retrieve the auth code from the request params
  auth_code = request.args['code']

  # An empty string is a valid token for this request
  sc = SlackClient("")

  # Request the auth tokens from Slack
  auth_response = sc.api_call(
    "oauth.access",
    client_id=client_id,
    client_secret=client_secret,
    code=auth_code
  )
  print ("auth_response: %s" % str(auth_response))

print ("call pre_install")
pre_install()
print ("call post_install")
post_install()

app.run(debug=True)
