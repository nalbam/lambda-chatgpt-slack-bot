# lambda-chatgpt-slack-bot

* <https://pypi.org/project/revChatGPT/>

## Save Slack Token

```bash
$ cp .env.example .env

$ source .env

SLACK_BOT_TOKEN="xxxx"
SLACK_SIGNING_SECRET="xxxx"

CHATGPT_ACCESS_TOKEN="xxxx"

aws ssm put-parameter --name $SLACK_BOT_TOKEN_KEY --value $SLACK_BOT_TOKEN --type SecureString --overwrite --region $AWS_REGION
aws ssm put-parameter --name $SLACK_SIGNING_SECRET_KEY --value $SLACK_SIGNING_SECRET --type SecureString --overwrite --region $AWS_REGION

aws ssm put-parameter --name $CHATGPT_ACCESS_TOKEN_KEY --value $CHATGPT_ACCESS_TOKEN --type SecureString --overwrite --region $AWS_REGION
```

## Install

```bash
$ brew install python@3.9

$ npm install -g serverless

$ sls plugin install -n serverless-python-requirements
$ sls plugin install -n serverless-dotenv-plugin

$ pip3 install --upgrade -r requirements.txt
```

## Setup

Setup a Slack app by following the guide at https://slack.dev/bolt-js/tutorial/getting-started

Set scopes to Bot Token Scopes in OAuth & Permission:

```
app_mentions:read
channels:join
chat:write
```

Set scopes in Event Subscriptions - Subscribe to bot events

```
app_mention
```

## Deployment

In order to deploy the example, you need to run the following command:

```bash
$ sls deploy
```

## Slack Test

```bash
curl -X POST -H "Content-Type: application/json" \
-d " \
{ \
    \"token\": \"Jhj5dZrVaK7ZwHHjRyZWjbDl\", \
    \"challenge\": \"3eZbrw1aBm2rZgRNFdxV2595E9CY3gmdALWMmHkvFXO7tYXAYM8P\", \
    \"type\": \"url_verification\" \
}" \
https://xxxx.execute-api.us-east-1.amazonaws.com/dev/slack/events
```
