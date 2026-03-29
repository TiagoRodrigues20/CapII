import azure.functions as func
import json
import os
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
    }

    cosmos_url = os.environ.get("COSMOS_URL", "MISSING")
    cosmos_key = os.environ.get("COSMOS_KEY", "MISSING")

    if cosmos_url == "MISSING" or cosmos_key == "MISSING":
        return func.HttpResponse(
            json.dumps({"error": "Missing COSMOS_URL or COSMOS_KEY"}),
            status_code=500,
            headers=headers
        )

    try:
        from azure.cosmos import CosmosClient, exceptions
        client = CosmosClient(cosmos_url, cosmos_key)
        db = client.get_database_client("pantry")
        container = db.get_container_client("tasktracker")
    except Exception as e:
        logging.error(f"Cosmos connection error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Cosmos connection failed: {str(e)}"}),
            status_code=500,
            headers=headers
        )

    if req.method == "GET":
        try:
            item = container.read_item(item="tasktracker_state", partition_key="tasktracker_state")
            return func.HttpResponse(json.dumps(item), status_code=200, headers=headers)
        except exceptions.CosmosResourceNotFoundError:
            empty = {"id": "tasktracker_state", "tasks": [], "streams": []}
            container.upsert_item(empty)
            return func.HttpResponse(json.dumps(empty), status_code=200, headers=headers)
        except Exception as e:
            logging.error(f"GET error: {str(e)}")
            return func.HttpResponse(
                json.dumps({"error": f"GET failed: {str(e)}"}),
                status_code=500,
                headers=headers
            )

    if req.method == "POST":
        try:
            body = req.get_json()
            body["id"] = "tasktracker_state"
            container.upsert_item(body)
            return func.HttpResponse(json.dumps({"ok": True}), status_code=200, headers=headers)
        except Exception as e:
            logging.error(f"POST error: {str(e)}")
            return func.HttpResponse(
                json.dumps({"error": f"POST failed: {str(e)}"}),
                status_code=500,
                headers=headers
            )

    return func.HttpResponse(
        json.dumps({"error": "Method not allowed"}),
        status_code=405,
        headers=headers
    )
