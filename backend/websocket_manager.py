import asyncio
import json
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str, user_id: Optional[int] = None):
        await websocket.accept()
        
        # Add to connection tracking
        if connection_id not in self.active_connections:
            self.active_connections[connection_id] = set()
        self.active_connections[connection_id].add(websocket)
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, connection_id: str, user_id: Optional[int] = None):
        # Remove from connection tracking
        if connection_id in self.active_connections:
            self.active_connections[connection_id].discard(websocket)
            if not self.active_connections[connection_id]:
                del self.active_connections[connection_id]
        
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Error sending message: {e}")
    
    async def broadcast_to_connection(self, message: dict, connection_id: str):
        if connection_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[connection_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    print(f"Error broadcasting to connection {connection_id}: {e}")
                    disconnected.add(websocket)
            
            # Clean up disconnected websockets
            for websocket in disconnected:
                self.active_connections[connection_id].discard(websocket)
    
    async def broadcast_to_user(self, message: dict, user_id: int):
        if user_id in self.user_connections:
            disconnected = set()
            for websocket in self.user_connections[user_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    print(f"Error broadcasting to user {user_id}: {e}")
                    disconnected.add(websocket)
            
            # Clean up disconnected websockets
            for websocket in disconnected:
                self.user_connections[user_id].discard(websocket)

# Global connection manager instance
manager = ConnectionManager()

class ProgressTracker:
    def __init__(self):
        self.progress_data: Dict[str, Dict] = {}
    
    def update_progress(self, task_id: str, progress: int, status: str, message: str = "", data: Optional[Dict] = None):
        """Update progress for a specific task"""
        self.progress_data[task_id] = {
            "task_id": task_id,
            "progress": progress,
            "status": status,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Broadcast progress update
        asyncio.create_task(self._broadcast_progress(task_id))
    
    def get_progress(self, task_id: str) -> Optional[Dict]:
        """Get current progress for a task"""
        return self.progress_data.get(task_id)
    
    async def _broadcast_progress(self, task_id: str):
        """Broadcast progress update to all connections for this task"""
        progress = self.progress_data.get(task_id)
        if progress:
            await manager.broadcast_to_connection({
                "type": "progress_update",
                "data": progress
            }, task_id)
    
    def complete_task(self, task_id: str, result: Optional[Dict] = None):
        """Mark a task as completed"""
        self.update_progress(
            task_id=task_id,
            progress=100,
            status="completed",
            message="Task completed successfully",
            data=result or {}
        )
    
    def fail_task(self, task_id: str, error: str):
        """Mark a task as failed"""
        self.update_progress(
            task_id=task_id,
            progress=0,
            status="failed",
            message=f"Task failed: {error}",
            data={"error": error}
        )

# Global progress tracker instance
progress_tracker = ProgressTracker()

async def websocket_endpoint(websocket: WebSocket, connection_id: str, user_id: Optional[int] = None):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket, connection_id, user_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "subscribe_task":
                task_id = message.get("task_id")
                if task_id:
                    # Send current progress if available
                    current_progress = progress_tracker.get_progress(task_id)
                    if current_progress:
                        await manager.send_personal_message({
                            "type": "progress_update",
                            "data": current_progress
                        }, websocket)
            
            elif message.get("type") == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, connection_id, user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, connection_id, user_id) 