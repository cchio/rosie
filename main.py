import os
import json
import logging
from dotenv import dotenv_values
from functools import wraps
from revChatGPT.revChatGPT import Chatbot
from flask import abort, Flask, request, redirect
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse


# Get logger
logger = logging.getLogger('Rosie')
c_handler = logging.StreamHandler()
logger.addHandler(c_handler)
logger.setLevel(logging.DEBUG)


def validate_twilio_request(f):
  """Validates that incoming requests genuinely originated from Twilio"""
  @wraps(f)
  def decorated_function(*args, **kwargs):
    # Create an instance of the RequestValidator class
    validator = RequestValidator(os.environ.get('TWILIO_AUTH_TOKEN'))

    # Validate the request using its URL, POST data,
    # and X-TWILIO-SIGNATURE header
    request_valid = validator.validate(
      request.url,
      request.form,
      request.headers.get('X-TWILIO-SIGNATURE', ''))

    # Continue processing the request if it's valid, return a 403 error if
    # it's not
    if request_valid:
      return f(*args, **kwargs)
    else:
      return abort(403)
  return decorated_function


def setup_chatbot():
  return Chatbot({
    'email': dotenv_values('.env')['CHATGPT_EMAIL'],
    'password': dotenv_values('.env')['CHATGPT_PASSWORD'],
  }, conversation_id=None)


chatbot = setup_chatbot()
app = Flask(__name__)


@app.route('/sms', methods=['POST'])
# @validate_twilio_request
def sms_reply():
  body = request.values.get('Body', None)
  logger.info('Received SMS: \"{}\"'.format(body))

  match body:
    case '$REFRESH':
      chatbot.refresh_session()
      resp_body = 'SESSION REFRESHED'
    case '$ROLLBACK':
      chatbot.rollback_conversation()
      resp_body = 'CONVERSATION ROLLED BACK'
    case '$RESET':
      chatbot.reset_chat()
      resp_body = 'CHAT RESET'
    case _:
      chatbot_resp = chatbot.get_chat_response(body, output='text')
      resp_body = chatbot_resp['message']

  resp = MessagingResponse()
  resp.message(resp_body)
  return str(resp)


if __name__ == '__main__':
  app.run(debug=True)