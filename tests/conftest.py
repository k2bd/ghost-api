import boto3
import pytest

from ghost_api.constants import GAMES_TABLE_NAME, LOCAL_DYNAMODB_ENDPOINT
from ghost_api.service import GhostService


@pytest.fixture
def dynamodb_client():
    assert LOCAL_DYNAMODB_ENDPOINT is not None
    return boto3.client("dynamodb", endpoint_url=LOCAL_DYNAMODB_ENDPOINT)


@pytest.fixture
def games_table(dynamodb_client):
    """
    Create a temporary clean games table, tearing it down after the test.

    Uses waiters to ensure the table is properly created and destroyed before
    moving on.
    """
    table = dynamodb_client.create_table(
        TableName=GAMES_TABLE_NAME,
        KeySchema=[
            {
                "AttributeName": "room_code",
                "KeyType": "HASH",
            },
        ],
        AttributeDefinitions=[
            {
                "AttributeName": "room_code",
                "AttributeType": "S",
            },
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 100,
            "WriteCapacityUnits": 100,
        },
    )

    exists_waiter = dynamodb_client.get_waiter("table_exists")
    not_exists_waiter = dynamodb_client.get_waiter("table_not_exists")

    exists_waiter.wait(TableName=GAMES_TABLE_NAME)

    try:
        yield table
    finally:
        dynamodb_client.delete_table(TableName=GAMES_TABLE_NAME)
        not_exists_waiter.wait(TableName=GAMES_TABLE_NAME)


@pytest.fixture
def service(games_table) -> GhostService:
    """
    Return a service that can interact with a temporary games table
    """
    return GhostService()
