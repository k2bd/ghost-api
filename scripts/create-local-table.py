from ghost_api.constants import GAMES_TABLE_NAME, LOCAL_DYNAMODB_ENDPOINT
import boto3


def games_table():
    """
    Create a temporary clean games table, tearing it down after the test.

    Uses waiters to ensure the table is properly created and destroyed before
    moving on.
    """
    if not LOCAL_DYNAMODB_ENDPOINT:
        raise EnvironmentError("Please set LOCAL_DYNAMODB_ENDPOINT")

    dynamodb_client = boto3.client("dynamodb", endpoint_url=LOCAL_DYNAMODB_ENDPOINT)
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

    exists_waiter.wait(TableName=GAMES_TABLE_NAME)


if __name__ == "__main__":
    games_table()
