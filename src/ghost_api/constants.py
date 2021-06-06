import os
from typing import Optional


#: Name of the games table in DynamoDB
GAMES_TABLE_NAME: str = os.environ["GHOST_GAMES_TABLE_NAME"]

#: AWS region for connecting to AWS resources
AWS_REGION: Optional[str] = os.environ.get("AWS_REGION")

#: Optional endpoint for a local DynamoDB instance, taking precedence over AWS_REGION
LOCAL_DYNAMODB_ENDPOINT: Optional[str] = os.environ.get("LOCAL_DYNAMODB_ENDPOINT")
