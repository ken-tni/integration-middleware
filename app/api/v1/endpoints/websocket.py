from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Any, List
import json
from app.utils.logging import get_logger
from app.core.authentication import auth_manager
from app.core.middleware.websocket_service import websocket_service
from app.utils.json_utils import deep_serialize, dumps

logger = get_logger("api.websocket")
router = APIRouter()

# Store active connections
active_connections: List[WebSocket] = []

async def get_token(websocket: WebSocket):
    # You can customize authentication as needed
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return None
    # Validate token logic here
    return token

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Receive JSON data
            data = await websocket.receive_text()
            
            try:
                # Parse the received JSON
                json_data = json.loads(data)
                
                # Handle different action types
                action = json_data.get("action")
                if not action:
                    await websocket.send_json({
                        "status": "error",
                        "message": "Missing 'action' field in request"
                    })
                    continue
                
                # Process different actions
                if action == "ping":
                    # Manually serialize with our custom serializer then send
                    response = {
                        "status": "success", 
                        "action": "pong"
                    }
                    await websocket.send_text(dumps(response))
                
                elif action == "call_endpoint":
                    # Access endpoints through the WebSocket service
                    endpoint = json_data.get("endpoint")
                    params = json_data.get("params", {})
                    
                    if not endpoint:
                        await websocket.send_json({
                            "status": "error",
                            "message": "Missing 'endpoint' field in request"
                        })
                        continue
                    
                    # Process the request using our service
                    response_data = await websocket_service.handle_request(endpoint, params)
                    # Manually serialize with our custom serializer then send
                    await websocket.send_text(dumps(response_data))
                
                else:
                    await websocket.send_json({
                        "status": "error",
                        "message": f"Unknown action: {action}"
                    })
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "status": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                error_response = {
                    "status": "error",
                    "message": f"Error processing request: {str(e)}"
                }
                # Manually serialize with our custom serializer then send
                await websocket.send_text(dumps(error_response))
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("WebSocket client disconnected") 