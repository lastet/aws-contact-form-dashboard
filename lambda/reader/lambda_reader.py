import json
import os
import boto3
from decimal import Decimal

def json_safe(obj):
    """Convert DynamoDB Decimals into JSON-friendly types."""
    if isinstance(obj, list):
        return [json_safe(x) for x in obj]
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj

def resp(status, payload):
    return {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(json_safe(payload)),
    }

def lambda_handler(event, context):
    table_name = os.environ["TABLE_NAME"]
    table = boto3.resource("dynamodb").Table(table_name)

    qs = event.get("queryStringParameters") or {}
    try:
        limit = int(qs.get("limit", "20"))
        limit = max(1, min(limit, 100))
    except Exception:
        limit = 20

    try:
        r = table.scan(Limit=limit)
        items = r.get("Items", [])

        # сортируем по createdAt (миллисекунды), новые сверху
        items.sort(key=lambda x: int(x.get("createdAt", 0)), reverse=True)

        payload = {"count": len(items), "items": items}
        return resp(200, payload)

    except Exception as e:
        print("Reader error:", str(e))
        return resp(500, {"error": "Internal server error"})
