"""TOVA v4 FastAPI Application"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import logging
import asyncio
from pathlib import Path

from .core.orchestrator import TovaOrchestrator
from .api.websocket import WebSocketManager
from .config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TOVA v4",
    description="Dual-Brain AI Companion System",
    version="4.0.0"
)

# Global orchestrator instance
orchestrator = TovaOrchestrator()
ws_manager = WebSocketManager()

@app.on_event("startup")
async def startup_event():
    """Initialize TOVA system on startup"""
    logger.info("🎪 Starting TOVA v4...")
    
    # Initialize orchestrator
    if await orchestrator.initialize():
        logger.info("✅ TOVA v4 online and ready!")
    else:
        logger.error("❌ TOVA v4 failed to initialize")
        raise RuntimeError("Failed to initialize TOVA orchestrator")

@app.on_event("shutdown") 
async def shutdown_event():
    """Clean shutdown"""
    logger.info("🛑 Shutting down TOVA v4...")
    await orchestrator.shutdown()
    logger.info("✅ TOVA v4 shutdown complete")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    mixtral_ok = await orchestrator.mixtral.health_check()
    phi_ok = await orchestrator.phi.health_check()
    
    return {
        "status": "healthy" if (mixtral_ok and phi_ok) else "degraded",
        "brains": {
            "mixtral": "online" if mixtral_ok else "offline", 
            "phi": "online" if phi_ok else "offline"
        }
    }

@app.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    """Main chat WebSocket endpoint"""
    await ws_manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")
            context = data.get("context", {})
            
            if not message.strip():
                continue
            
            # Send typing indicator
            await websocket.send_json({
                "type": "typing",
                "status": "started"
            })
            
            # Process message through orchestrator
            response_chunks = []
            async for chunk in orchestrator.process_user_message(message, context):
                if chunk:
                    response_chunks.append(chunk)
                    # Stream each chunk to client
                    await websocket.send_json({
                        "type": "response_chunk",
                        "content": chunk
                    })
            
            # Send completion signal
            await websocket.send_json({
                "type": "response_complete",
                "full_response": "".join(response_chunks)
            })
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("Client disconnected from chat")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

# Mount static files for frontend
frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def serve_chat_interface():
    """Serve the main chat interface"""
    chat_html = frontend_path / "chat" / "index.html"
    if chat_html.exists():
        with open(chat_html, 'r') as f:
            return HTMLResponse(f.read())
    else:
        return HTMLResponse("<h1>TOVA v4</h1><p>Chat interface not found</p>")

@app.get("/admin")
async def serve_admin_interface():
    """Serve the admin interface"""
    admin_html = frontend_path / "admin" / "index.html"
    if admin_html.exists():
        with open(admin_html, 'r') as f:
            return HTMLResponse(f.read())
    else:
        return HTMLResponse("<h1>TOVA v4 Admin</h1><p>Admin interface not found</p>") 