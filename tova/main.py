"""TOVA v4 FastAPI Application"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import logging
import asyncio
from pathlib import Path
import uuid
import time

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
    
    # Initialize orchestrator (but don't fail if brains aren't available)
    try:
        if await orchestrator.initialize():
            logger.info("✅ TOVA v4 online and ready!")
        else:
            logger.warning("⚠️  TOVA v4 started in degraded mode - brain servers not available")
            logger.info("✅ TOVA v4 online (degraded mode) - frontend will work but AI features disabled")
    except Exception as e:
        logger.warning(f"⚠️  Failed to initialize brains: {e}")
        logger.info("✅ TOVA v4 online (degraded mode) - frontend will work but AI features disabled")

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
    
    # Initialize conversation for this connection
    user_id = "default_user"  # TODO: Implement user authentication
    conversation_id = await orchestrator.start_conversation(user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")
            context = data.get("context", {})
            recv_t = time.perf_counter()
            logger.info(f"🔍 Received message at t={recv_t:.6f}: {message}")
            
            if not message.strip():
                continue
            
            # Send typing indicator
            typing_t = time.perf_counter()
            await websocket.send_json({
                "type": "typing",
                "status": "started",
                "t": typing_t
            })
            logger.info(f"🔍 Sent typing at t={typing_t:.6f} (Δrecv→typing={(typing_t - recv_t)*1000:.1f}ms)")
            
            response_chunks = []
            first_chunk_emitted = False
            logger.info("🔍 Starting message processing...")
            
            try:
                async for chunk_data in orchestrator.process_user_message_with_persistence(
                    conversation_id=conversation_id,
                    message=message,
                    user_context=context
                ):
                    if isinstance(chunk_data, dict):
                        content = chunk_data.get("content", "")
                        metadata = chunk_data.get("metadata", {})
                        if content:
                            response_chunks.append(content)
                            now_t = time.perf_counter()
                            if not first_chunk_emitted:
                                first_chunk_emitted = True
                                logger.info(
                                    f"🔍 First backend chunk ready at t={now_t:.6f} (Δtyping→first={(now_t - typing_t)*1000:.1f}ms, Δrecv→first={(now_t - recv_t)*1000:.1f}ms)"
                                )
                            payload = {
                                "type": "response_chunk",
                                "content": content,
                                "metadata": metadata,
                                "t": now_t
                            }
                            await websocket.send_json(payload)
                    else:
                        content = chunk_data
                        if content:
                            response_chunks.append(content)
                            now_t = time.perf_counter()
                            if not first_chunk_emitted:
                                first_chunk_emitted = True
                                logger.info(
                                    f"🔍 First backend chunk ready at t={now_t:.6f} (Δtyping→first={(now_t - typing_t)*1000:.1f}ms, Δrecv→first={(now_t - recv_t)*1000:.1f}ms)"
                                )
                            payload = {
                                "type": "response_chunk",
                                "content": content,
                                "t": now_t
                            }
                            await websocket.send_json(payload)
                
                logger.info(f"🔍 Finished processing, got {len(response_chunks)} chunks")
                
            except Exception as e:
                logger.error(f"🔍 Error during message processing: {e}")
                import traceback
                logger.error(f"🔍 Traceback: {traceback.format_exc()}")
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
                except Exception:
                    # Client already disconnected; stop processing this loop
                    break
                continue
            
            # Send completion signal
            full_response = "".join(response_chunks)
            completion_t = time.perf_counter()
            completion_payload = {
                "type": "response_complete",
                "full_response": full_response,
                "conversation_id": conversation_id,
                "t": completion_t
            }
            logger.info(f"🔍 Sending completion at t={completion_t:.6f} (Δrecv→complete={(completion_t - recv_t)*1000:.1f}ms)")
            try:
                await websocket.send_json(completion_payload)
                logger.info(f"🔍 Sent completion signal with response: {full_response[:50]}...")
            except Exception as se:
                logger.warning(f"🔍 Could not send completion (client disconnected): {se}")
                break
    
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