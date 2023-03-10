import boto3
import json
import os
import time

from revChatGPT.V1 import Chatbot

from slack_bolt import App, Say
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

BOT_CURSOR = os.environ.get("BOT_CURSOR", ":robot_face:")

# Keep track of conversation history by thread
DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME", "chatgpt-slack-bot-context")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

# Set up Slack API credentials
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

# Initialize Slack app
app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET,
    process_before_response=True,
)

# Set up ChatGPT API credentials
CHATGPT_ACCESS_TOKEN = os.environ["CHATGPT_ACCESS_TOKEN"]


# Get the context from DynamoDB
def get_context(id):
    item = table.get_item(Key={"id": id}).get("Item")
    return (item["conversation_id"], item["parent_id"], item["prompt"]) if item else ("", "", "")


# Put the context in DynamoDB
def put_context(id, conversation_id="", parent_id="", prompt=""):
    current_time = int(time.time())
    expire_at = current_time + (86400 * 10)

    table.put_item(
        Item={
            "id": id,
            "conversation_id": conversation_id,
            "parent_id": parent_id,
            "prompt": prompt,
            "expire_at": expire_at,
        }
    )


# Update the message in Slack
def chat_update(channel, message, latest_ts):
    print("chat_update: {}".format(message))
    app.client.chat_update(
        channel=channel,
        text=message,
        ts=latest_ts,
    )


# Handle the chatgpt conversation
def chatbot_ask(prompt, conversation_id, parent_id, channel, latest_ts, thread_ts):
    # Initialize ChatGPT
    # chatbot = Chatbot(config={"access_token": CHATGPT_ACCESS_TOKEN}, conversation_id=conversation_id, parent_id=parent_id)
    chatbot = Chatbot(config={"access_token": CHATGPT_ACCESS_TOKEN})

    # Send the prompt to ChatGPT
    counter = 0
    message = ""
    for response in chatbot.ask(prompt, conversation_id, parent_id):
        message = response["message"]

        conversation_id, parent_id = (
            response["conversation_id"],
            response["parent_id"],
        )

        if counter % 32 == 1:
            chat_update(channel, message + " " + BOT_CURSOR, latest_ts)
            # put_context(thread_ts, conversation_id, parent_id)

        counter = counter + 1

    chat_update(channel, message, latest_ts)
    put_context(thread_ts, conversation_id, parent_id)

    return message


# Handle the chatgpt conversation
def conversation(thread_ts, prompt, channel, say: Say):
    print(thread_ts, prompt)

    # Keep track of the latest message timestamp
    result = say(text=BOT_CURSOR, thread_ts=thread_ts)
    latest_ts = result["ts"]

    conversation_id, parent_id, _ = get_context(thread_ts)

    try:
        chatbot_ask(prompt, conversation_id, parent_id, channel, latest_ts, thread_ts)

    except Exception as e:
        print(thread_ts, "Error handling message: {}".format(e))
        message = "Sorry, I could not process your request.\nhttps://status.openai.com"

        say(text=message, thread_ts=thread_ts)


# Handle the app_mention event
@app.event("app_mention")
def handle_app_mentions(body: dict, say: Say):
    print("handle_app_mentions: {}".format(body))

    event = body["event"]

    thread_ts = event["thread_ts"] if "thread_ts" in event else event["ts"]
    prompt = event["text"].split("<@")[1].split(">")[1].strip()

    # # Check if this is a message from the bot itself, or if it doesn't mention the bot
    # if "bot_id" in event or f"<@{app.client.users_info(user=SLACK_BOT_TOKEN)['user']['id']}>" not in text:
    #     return

    conversation(thread_ts, prompt, event["channel"], say)


# Handle the message event
def lambda_handler(event, context):
    body = json.loads(event["body"])

    if "challenge" in body:
        # Respond to the Slack Event Subscription Challenge
        return {
            "statusCode": 200,
            "headers": {"Content-type": "application/json"},
            "body": json.dumps({"challenge": body["challenge"]}),
        }

    print("lambda_handler: {}".format(body))

    # Duplicate execution prevention
    token = body["event"]["client_msg_id"]
    _, _, prompt = get_context(token)
    if prompt == "":
        put_context(token, "", "", body["event"]["text"])
    else:
        return {
            "statusCode": 200,
            "headers": {"Content-type": "application/json"},
            "body": json.dumps({"status": "Success"}),
        }

    # Handle the event
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)
