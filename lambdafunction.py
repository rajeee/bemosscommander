"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
import urllib2
import urllib
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
bemossTable = dynamodb.Table('bemossIPs')

BEMOSS_IP = 'http://38.68.237.187:12346'
BEMOSS_PORT = '12346'

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_bemoss_name_and_ip_and_auth(session):
    
    if 'attributes' in session and 'bemoss_ip' in session['attributes'] and 'bemoss_name' in session['attributes'] and 'authentication_pin' in session['attributes']:
        return (session['attributes']['bemoss_ip'],session['attributes']['bemoss_name'],session['attributes']['authentication_pin'])
    else:
        result = bemossTable.query(KeyConditionExpression=Key('userid').eq(session['user']['userId']))
        for item in result['Items']:
            bemoss_ip=item['IP']
            bemoss_name = item['bemoss_name']
            authentication_pin = item.get('authentication_pin','')
            return (bemoss_ip,bemoss_name, authentication_pin)
        else:
            return None
            
        

def get_welcome_response(session):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    result = get_bemoss_name_and_ip_and_auth(session)
    if result:
        bemoss_ip=result[0]
        bemoss_name = result[1]
        authentication_pin = result[2]
        session_attributes = {'bemoss_ip':bemoss_ip,'bemoss_name':bemoss_name, 'authentication_pin': authentication_pin }
        speech_output = "Welcome to " + bemoss_name + " at " + bemoss_ip 
        #TODO also allow for choosing any of the available BEMOSS system
    else:
        speech_output = "No IP found in Table, first give me an IP first" 
        session_attributes = {}
    should_end_session = False
    card_title = "Welcome"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for using the bemoss alexa commander " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def set_bemoss_ip(intent,session):
    """ Sets IP address of a particular bemoss deployement
    """
    card_title = intent['name']
    should_end_session = False
    # if session.get('attributes', {}) and "bemoss_ip" in session.get('attributes', {}):
    # bemoss_ip = session['attributes']['bemoss_ip']
    session_attributes = {}
    print(session)
    userID = session['user']['userId']
    if 'bemossname' in intent['slots'] and 'ipa' in intent['slots'] and 'ipb' in intent['slots'] and 'ipc' in intent['slots'] and 'ipd' in intent['slots']:
        bemoss_name = intent['slots']['bemossname']['value']
        bemoss_ip = 'http://'+'.'.join((intent['slots']['ipa']['value'],intent['slots']['ipb']['value'],intent['slots']['ipc']['value'],intent['slots']['ipd']['value']))+':'+BEMOSS_PORT
        bemossTable.put_item(Item={'userid':userID,'bemoss_name':bemoss_name,'IP':bemoss_ip})
        session_attributes = {'bemoss_ip':bemoss_ip,'bemoss_name':bemoss_name}
        speech_output = "The bemoss name and IP has been successfully set."
    else:
        speech_output = "The bemoss name and IP could not be set."
    
    return build_response(session_attributes, build_speechlet_response(
    card_title, speech_output, None, should_end_session))
    
def set_bemoss_authentication(intent,session):
    """ Sets IP address of a particular bemoss deployement
    """
    card_title = intent['name']
    should_end_session = False
    
    result = get_bemoss_name_and_ip_and_auth(session)
    if result:
        bemoss_ip=result[0]
        bemoss_name = result[1]
        speech_output = "Welcome to " + bemoss_name + " at " + bemoss_ip 
        #TODO also allow for choosing any of the available BEMOSS system
    else:
        speech_output = "No IP found in Table, first give me an IP first" 
        session_attributes = {}
        return build_response(session_attributes, build_speechlet_response(
    card_title, speech_output, None, should_end_session))
    
    # if session.get('attributes', {}) and "bemoss_ip" in session.get('attributes', {}):
    # bemoss_ip = session['attributes']['bemoss_ip']
    session_attributes = {}
    print(session)
    userID = session['user']['userId']
    if 'bemossname' in intent['slots'] and 'authenticationpin' in intent['slots']:
        bemoss_name = intent['slots']['bemossname']['value']
        authentication_pin = intent['slots']['authenticationpin']['value']
        bemossTable.put_item(Item={'userid':userID,'bemoss_name':bemoss_name,'authentication_pin':authentication_pin,'IP':bemoss_ip})
        session_attributes = {'bemoss_ip':bemoss_ip,'bemoss_name':bemoss_name,'authentication_pin':authentication_pin}
        speech_output = "The bemoss authentication pin has been successfully set."
    else:
        speech_output = "The bemoss authentication pin could not be set."
    
    return build_response(session_attributes, build_speechlet_response(
    card_title, speech_output, None, should_end_session))
 
def set_device_variable(intent, session):
    """ Sets device variable to specific value in the session
    """
    session_attributes = {} 
    result = get_bemoss_name_and_ip_and_auth(session)
    if not result:
        speech_output = "There is no known BEMOSS. Try setting BEMOSS IP."
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, None, should_end_session))
    else:
        bemoss_ip=result[0]
        bemoss_name = result[1]
        authentication_pin = result[2]
        session_attributes = {'bemoss_ip':bemoss_ip,'bemoss_name':bemoss_name, 'authentication_pin': authentication_pin}
        card_title = intent['name']
        should_end_session = False
        # if session.get('attributes', {}) and "bemoss_ip" in session.get('attributes', {}):
        # bemoss_ip = session['attributes']['bemoss_ip']
       
        if 'nickname' in intent['slots'] and 'variable' in intent['slots'] and 'value' in intent['slots']:
            nickname = intent['slots']['nickname'].get('value','')
            variable = intent['slots']['variable'].get('value','')
            value = intent['slots']['value'].get('value','')
            query_dict = {
                "nickname": nickname,
                "variable": {variable:value}
            }
        elif 'nickname' in intent['slots'] and 'turnonoff' in intent['slots']:   
            nickname = intent['slots']['nickname']['value']
            variable = 'status'
            value = 1 if intent['slots']['turnonoff'] == 'on' else 'off'
            query_dict = {
                "nickname": nickname,
                "variable": {variable:value}
            }
        else:
            speech_output = "I'm not sure what your command is, please repeat your"\
                            "command in the correct pattern. " 
            return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, None, should_end_session))
            
        url = "/".join([bemoss_ip, "alexa", "control"])
        req = urllib2.Request(url,urllib.urlencode({'dumps':json.dumps(query_dict),'auth':authentication_pin}))
        r = urllib2.urlopen(req)
        
        if r.code == 200:
            reply = json.loads(r.read())
            if reply['success'] == 1:
                speech_output = nickname + "'s " + variable + " has been updated to " + str(value) 
            else:
                cause = reply['cause'] 
                speech_output = "Control of " + nickname + " 's " + variable + " failed because " + cause 
        else:
            speech_output = "There is some communication problem with bemoss," \
                            "please check your network setting."
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, None, should_end_session))

def get_device_variable(intent, session):
    session_attributes = {} 
    result = get_bemoss_name_and_ip_and_auth(session)
    if not result:
        speech_output = "There is no known BEMOSS. Try setting BEMOSS IP."
        return build_response(session_attributes, build_speechlet_response(
            card_title, speech_output, None, should_end_session))
    else:
        print(result)
        bemoss_ip=result[0]
        bemoss_name = result[1]
        authentication_pin = result[2]
        session_attributes = {'bemoss_ip':bemoss_ip,'bemoss_name':bemoss_name,'authentication_pin':authentication_pin}
        card_title = intent['name']
        should_end_session = False
        # if session.get('attributes', {}) and "bemoss_ip" in session.get('attributes', {}):
        # bemoss_ip = session['attributes']['bemoss_ip']
        if 'nickname' in intent['slots'] and 'variable' in intent['slots']:
            nickname = intent['slots']['nickname'].get('value','')
            variable = intent['slots']['variable'].get('value','')
            query_dict = {
                'nickname': nickname,
                'variable': variable
            }
        else:
            speech_output = "I'm not sure what your command is, please repeat your"\
                            "command in the correct pattern. " 
            return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, None, should_end_session))
                
        url = "/".join([bemoss_ip, "alexa", "query","current"])
        print(url)
        req = urllib2.Request(url,urllib.urlencode({'dumps':json.dumps(query_dict),'auth':authentication_pin}))
        r = urllib2.urlopen(req)
        if r.code == 200:
            reply = json.loads(r.read())
            if reply['success'] == 1:
                value = reply['value'] 
                speech_output = "The " + variable + " of " + nickname + " is " + str(value) 
            else:
                cause = reply['cause'] 
                speech_output = "Value retrieving of " + nickname + " 's " + variable + " failed because " + cause 
        else:
            speech_output = "There is some communication problem with bemoss," \
                            "please check your network setting."
        return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, None, should_end_session))

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response(session)


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "Control":
        return set_device_variable(intent, session)
    elif intent_name == "Switch":
        return set_device_variable(intent, session)
    elif intent_name == "gettingip":
        return set_bemoss_ip(intent,session)
    elif intent_name == "gettingauthentication":
        return set_bemoss_authentication(intent,session)
    elif intent_name == "Query":
        return get_device_variable(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response(session)
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
