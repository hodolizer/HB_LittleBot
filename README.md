# python HB_DEVOPS Bot
## Building a simple bot using [Slack's Events API](https://api.slack.com/events-api) in Python
This bot is for managing a github repository along with Circle CI builds, Docker depoloyments and ?


#### Technical Requirements

This example uses [Python](https://www.python.org/downloads/), specifically version 2.7 so you'll need to make sure you are using the correct version of Python. We'll also use a number of python packages you can install through [pip.](https://pip.pypa.io/en/stable/installing/)

###### Here's a list of what we'll need:

- **[Python](https://www.python.org/downloads/)**, the programming language we're
going to use.
- **[Pip](https://pip.pypa.io/en/stable/installing/)**, the Python package manager
we'll use for installing packages we need.
- **[Virtualenv](https://virtualenv.pypa.io/en/latest/installation/)** or another
tool to manage a virtual environment

Once you've installed Python, pip and virtualenv, you can install all additional
dependent libraries using pip and the `requirements.txt` file included in this
project, including [Flask](http://flask.pocoo.org/), a web development micro
framework for Python and [python-slackclient](http://python-slackclient.readthedocs.io/en/latest/), a
Slack client for Python. :snake:

After you've cloned this repository locally, you'll want to create a virtual
environment to keep the dependencies for this project isolated from any other
project you may be working on.

If you're using `virtualenv` run the following commands from the root of your
project directory:

```bash
virtualenv env
```

Then activate your new virtual environment:

```bash
source env/bin/activate
```

After that, you can install all the Python packages this project will need with
this command:

```bash
pip install -r requirements.txt
```

###### Server Requirements

Slack will be delivering events to your app's server so your server needs to be able to receive incoming HTTPS traffic from Slack.

If you are running this project locally, you'll need to set up tunnels for Slack to connect to your endpoints. [Serveo](https://serveo.net/) is an easy to use tunneling tool that supports HTTPS, which is required by Slack.
ssh -o ServerAliveInterval=60 -R <your subdomain>:80:localhost:5000 serveo.net


You'll likely want to test events coming to your server without going through the actions on your Slack team.  [Postman](https://www.getpostman.com/) is a useful tool you can use to recreate requests sent from Slack to your server. This is especially helpful for events like user join, where the workflow to recreate the event requires quite a bit of set up.

## Let's get started :tada:
* **[Section 1: Build This Bot](docs/Section-1.md)** :point_left:  
* [Section 2: Create a Slack App and Bot User](docs/Section-2.md)  
* [Section 3: Subscribe to Events](docs/Section-3.md)  
* [Section 4: App Credentials](docs/Section-4.md)
* [Section 5: Make it Go](docs/Section-5.md)

## Further Reading and Getting Help

### Documentation

##### Slack Documentation
* [Getting started with Slack apps](https://api.slack.com/slack-apps)  
* [Slack Events API documentation](https://api.slack.com/events)  
* [Slack Web API documentation](https://api.slack.com/web)

##### Documentation for Tools
* [virtualenv](https://virtualenv.pypa.io/en/latest/userguide/)
* [flask](http://flask.pocoo.org/)
* [python-slackclient](http://python-slackclient.readthedocs.io/en/latest/)
* [ngrok](https://ngrok.com/docs)
* [postman](https://www.getpostman.com/docs/)

### Where to Find Help

Wondering what to do if you can't get this app to work for you?
The Slack Developer community is an awesome place to get help when you're confused
or stuck. We have an excellent 'search first' culture and Slack is committed to
improving our tutorials and documentation based on your feedback. If you've
checked the [Slack API documentation](https://api.slack.com/), reached the end
of your google patience and found [StackOverflow](http://stackoverflow.com/questions/tagged/slack-api)
to be unhelpful, try asking for help in the [Dev4Slack](http://dev4slack.xoxco.com/)
Slack team.

### Feedback
Reach out to me through [Github](https://github.com/hodolizer)
