class ContextMonitor {
    constructor() {
        this.currentUsage = 0;
        this.lastUpdateTime = 0;
        this.updateThrottle = 2000;
        this.lastVisualState = null;
        this.avatarContainer = document.getElementById('avatarContainer');
        this.contextActions = document.getElementById('contextActions');
    }
    
    updateContextUsage(usage) {
        const now = Date.now();
        if (now - this.lastUpdateTime < this.updateThrottle) return;
        if (Math.abs(this.currentUsage - usage) < 5) return;
        
        this.currentUsage = usage;
        this.lastUpdateTime = now;
        this.updateVisuals();
    }
    
    updateVisuals() {
        let newVisualState = 'green';
        if (this.currentUsage >= 80) {
            newVisualState = 'red';
        } else if (this.currentUsage >= 60) {
            newVisualState = 'yellow';
        }
        
        if (this.lastVisualState === newVisualState) return;
        
        this.avatarContainer.classList.remove('context-yellow', 'context-red');
        this.contextActions.classList.remove('show');
        
        if (newVisualState === 'red') {
            this.avatarContainer.classList.add('context-red');
            this.contextActions.classList.add('show');
        } else if (newVisualState === 'yellow') {
            this.avatarContainer.classList.add('context-yellow');
        }
        
        this.lastVisualState = newVisualState;
    }
    
    getStatusText() {
        if (this.currentUsage >= 80) return "Context: Critical";
        if (this.currentUsage >= 60) return "Context: Warning";
        return "Context: Good";
    }
}

class AvatarManager {
    constructor() {
        this.currentClip = 'tova_default.mp4';
        this.isPlaying = false;
        this.video = document.getElementById('tovaAvatar');
        this.setupDebugBubble();
        this.setupVideoEvents();
        
        setTimeout(() => this.freezeOnFirstFrame(), 100);
    }
    
    switchAvatar(clipName) {
        if (this.currentClip !== clipName) {
            this.currentClip = clipName;
            this.video.src = `/static/assets/avatar/${clipName}`;
            this.video.load();
            this.freezeOnFirstFrame();
        }
    }
    
    freezeOnFirstFrame() {
        if (this.video) {
            this.video.pause();
            this.video.currentTime = 0;
        }
    }
    
    playDuringResponse() {
        if (!this.video) return;
        
        // Set to loop immediately
        this.video.loop = true;
        
        // If already playing smoothly, don't interrupt
        if (this.isPlaying && !this.video.paused) {
            return;
        }
        
        // Start from current position without resetting to 0
        // This prevents the full loop before streaming
            this.isPlaying = true;
            this.video.play().catch(e => {
                console.error('Video play failed:', e);
                this.isPlaying = false;
            });
    }
    
    stopAfterResponse() {
        this.isPlaying = false;
        // Disable looping when the response finishes
        if (this.video) {
            this.video.loop = false;
        }
        this.freezeOnFirstFrame();
    }
    
    setupDebugBubble() {
        const bubble = document.getElementById('debugBubble');
        if (bubble) {
            bubble.addEventListener('click', () => toggleDebugPanel());
        }
    }
    
    setupVideoEvents() {
        if (!this.video) return;
        
        this.video.addEventListener('ended', () => {
            // If looping is enabled during streaming, do not freeze on end
            if (this.video && this.video.loop) {
                return;
            }
            this.isPlaying = false;
            this.freezeOnFirstFrame();
        });
        
        this.video.addEventListener('error', (e) => {
            console.error('Video error:', e);
            this.isPlaying = false;
        });
    }
}

class TovaInterface {
    constructor() {
        this.ws = null;
        this.wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/chat`;
        this.isConnected = false;
        this.currentConversationId = null;
        this.streamingMessage = null;
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadAndRenderHistory();
        this.connect();
        this.loadSystemData();
        
        setInterval(() => this.refreshSystemData(), 30000);
    }

    setupEventListeners() {
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');

        sendBtn.addEventListener('click', () => this.sendMessage());
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    async loadAndRenderHistory() {
        try {
            // For now, just show welcome message
            // TODO: Implement actual history loading when backend supports it
            const messagesContainer = document.getElementById('chatMessages');
            messagesContainer.innerHTML = '';
            this.addMessage('system', 'TOVA v4 dual-brain system ready! You can now start chatting.');
        } catch (error) {
            console.error("Error loading chat history:", error);
            this.addMessage('system', 'Welcome to TOVA v4! Starting a new session.');
        }
    }

    connect() {
        try {
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = () => {
                this.isConnected = true;
                this.updateConnectionStatus('Connected', true);
                this.enableInput();
            };

            this.ws.onmessage = (event) => {
                console.log('🔍 RAW WebSocket message received:', event.data);
                try {
                    const data = JSON.parse(event.data);
                    // Timing logs: mark when client receives server timestamps
                    if (data.t) {
                        const now = performance.now();
                        console.log(`⏱ client recv type=${data.type} t_server=${data.t.toFixed ? data.t.toFixed(3) : data.t} t_client=${now.toFixed(3)}ms`);
                    }
                    this.handleMessage(data);
                } catch (e) {
                    console.error('Failed to parse message:', e);
                    console.error('Raw data was:', event.data);
                }
            };

            this.ws.onclose = () => {
                this.isConnected = false;
                this.updateConnectionStatus('Disconnected', false);
                this.disableInput();
                setTimeout(() => this.connect(), 3000);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.addMessage('system', 'Connection error. Attempting to reconnect...');
            };

        } catch (error) {
            console.error('Failed to connect:', error);
            this.updateConnectionStatus('Connection Failed', false);
        }
    }

    updateConnectionStatus(text, connected) {
        const statusBlock = document.getElementById('statusBlock');
        const contextStatus = contextMonitor.getStatusText();
        const mood = connected ? 'Engaged' : 'Neutral';
        statusBlock.textContent = `Brains: ${text} • ${contextStatus} • Mood: ${mood}`;
        
        // Update brain status in debug panel
        const mixtralStatus = document.getElementById('mixtralStatus');
        const phiStatus = document.getElementById('phiStatus');
        if (mixtralStatus && phiStatus) {
            mixtralStatus.innerHTML = `🎭 Mixtral: <span class="status-${connected ? 'online' : 'offline'}">${connected ? 'Online' : 'Offline'}</span>`;
            phiStatus.innerHTML = `🔍 Phi: <span class="status-${connected ? 'online' : 'offline'}">${connected ? 'Online' : 'Offline'}</span>`;
        }
    }

    enableInput() {
        document.getElementById('messageInput').disabled = false;
        document.getElementById('sendBtn').disabled = false;
    }

    disableInput() {
        document.getElementById('messageInput').disabled = true;
        document.getElementById('sendBtn').disabled = true;
    }

    sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (!message || !this.isConnected) return;

        console.log('🔍 Sending message:', message);
        this.addMessage('user', message);
        
        // Send to TOVA v4 backend
        const messageData = {
            message: message,
            context: {} // Additional context can be added here
        };
        console.log('🔍 Sending WebSocket data:', messageData);
        this.ws.send(JSON.stringify(messageData));

        input.value = '';
    }

    handleMessage(data) {
        console.log('🔍 HandleMessage called with:', data);
        
        if (data.error) {
            console.log('🔍 Error message:', data.error);
            this.addMessage('system', `Error: ${data.error}`);
            return;
        }

        // Perf init per message
        if (!this._perf) {
            this._perf = { t0: 0, tFirst: 0, chars: 0 };
        }

        // Handle different message types from TOVA v4
        switch (data.type) {
            case 'typing':
                console.log('🔍 Typing indicator:', data.status);
                // init per request
                this._perf.t0 = performance.now();
                this._perf.tFirst = 0;
                this._perf.chars = 0;
                console.info('[TOVA] ▶ request sent');
                // Don't start avatar here - wait for first chunk
                break;
                
            case 'response_chunk':
                console.log('🔍 Response chunk:', data.content);
                // First token timing
                if (!this._perf.tFirst) {
                    this._perf.tFirst = performance.now();
                    console.info(`[TOVA] ⏱ first token: ${(this._perf.tFirst - this._perf.t0).toFixed(1)} ms`);
                }
                if (data.content) this._perf.chars += data.content.length;
                // Start avatar on first chunk if not already playing
                if (!this.streamingMessage) {
                    avatarManager.playDuringResponse();
                }
                this.updateTovaMessage(data.content, data.metadata);
                break;
                
            case 'response_complete':
                console.log('🔍 Response complete:', data.full_response);
                this.finalizeTovaMessage(data.full_response, data.metadata);
                avatarManager.stopAfterResponse();
                // Perf summary
                {
                    const done = performance.now();
                    const elapsed = ((this._perf.tFirst || done) - (this._perf.tFirst || this._perf.t0)) / 1000;
                    const toks = Math.max(1, Math.round(this._perf.chars / 4));
                    const tps = (toks / Math.max(elapsed, 0.001)).toFixed(2);
                    console.info(`[TOVA] ✅ stream complete | est tokens=${toks} | elapsed=${elapsed.toFixed(2)}s | ~${tps} t/s`);
                }
                break;
                
            default:
                console.log('🔍 Unknown message type:', data.type, data);
        }
    }

    addMessage(sender, content, metadata = null) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-bubble ${sender}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'content-div';

        if (sender === 'system') {
            contentDiv.innerHTML = `<strong>System:</strong> ${content}`;
        } else if (sender === 'user') {
            contentDiv.textContent = content;
        } else { // tova
            contentDiv.innerHTML = this.formatTovaMessage(content, metadata);
        }
        
        messageDiv.appendChild(contentDiv);

        // Add delete button for user and tova messages
        if (sender === 'user' || sender === 'tova') {
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-btn';
            deleteBtn.innerHTML = '&times;';
            deleteBtn.onclick = () => this.deleteMessage(messageDiv);
            messageDiv.appendChild(deleteBtn);
        }

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        return messageDiv;
    }

    updateTovaMessage(content, metadata) {
        console.log('🔍 updateTovaMessage called with content:', content);
        console.log('🔍 Current streaming message exists:', !!this.streamingMessage);
        
        const messagesContainer = document.getElementById('chatMessages');
        
        // Mark first render timing
        if (!this._firstChunkRenderedAt) {
            this._firstChunkRenderedAt = performance.now();
            console.log(`⏱ first chunk rendered at t_client=${this._firstChunkRenderedAt.toFixed(3)}ms`);
        }
        
        // Get or create streaming message
        if (!this.streamingMessage) {
            console.log('🔍 Creating new streaming message');
            this.streamingMessage = this.addMessage('tova', content, metadata);
            this.streamingMessage.classList.add('streaming');
        } else {
            console.log('🔍 Updating existing streaming message');
            const contentDiv = this.streamingMessage.querySelector('.content-div');
            const currentContent = contentDiv.innerHTML;
            console.log('🔍 Current content length:', currentContent.length);
            console.log('🔍 Adding chunk:', content);
            
            // Append chunk by concatenating with current content
            contentDiv.innerHTML = this.formatTovaMessage(this._stripHtml(currentContent) + content, metadata);
        }

        // Handle metadata updates
        if (metadata) {
            this.handleMetadata(metadata);
        }

        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Helper: strip HTML to get raw text before re-formatting
    _stripHtml(html) {
        const tmp = document.createElement('div');
        tmp.innerHTML = html;
        return tmp.textContent || tmp.innerText || '';
    }

    finalizeTovaMessage(content, metadata) {
        if (this.streamingMessage) {
            this.streamingMessage.classList.remove('streaming');
            const contentDiv = this.streamingMessage.querySelector('.content-div');
            contentDiv.innerHTML = this.formatTovaMessage(content, metadata);
        } else {
            // No chunks were streamed; still show the final content
            if (content && content.trim().length > 0) {
                this.addMessage('tova', content, metadata);
            }
        }
        
        this.streamingMessage = null;
        this._firstChunkRenderedAt = null;
        
        if (metadata) {
            this.handleMetadata(metadata);
        }
    }

    handleMetadata(metadata) {
        // Update context usage
        if (metadata.context_usage !== undefined) {
            contextMonitor.updateContextUsage(metadata.context_usage);
        }

        // Handle avatar switching
        if (metadata.current_avatar) {
            avatarManager.switchAvatar(metadata.current_avatar);
        }

        // Update debug panel
        if (metadata.debug_info) {
            updateDebugData(metadata.debug_info);
        }

        // Show immersive debug popup
        if (metadata.rag_status) {
            showImmersiveDebug(metadata.rag_status);
        }

        // Update status block
        this.updateStatusFromMetadata(metadata);
    }

    updateStatusFromMetadata(metadata) {
        const statusBlock = document.getElementById('statusBlock');
        const contextStatus = contextMonitor.getStatusText();
        const moduleCount = metadata.active_modules?.length || 0;
        const mood = metadata.current_mood || 'Engaged';
        statusBlock.textContent = `Modules: ${moduleCount} • ${contextStatus} • Mood: ${mood}`;
    }

    formatTovaMessage(content, metadata) {
        let html = content.replace(/\n/g, '<br>');
        
        if (metadata) {
            const metaInfo = [];
            if (metadata.memory_used > 0) metaInfo.push(`Memory: ${metadata.memory_used} entries`);
            if (metadata.processing_time) metaInfo.push(`${Math.round(metadata.processing_time)}ms`);
            if (metadata.active_modules) metaInfo.push(`Modules: ${metadata.active_modules.length}`);
            
            if (metaInfo.length > 0) {
                html += `<div style="font-size: 11px; opacity: 0.7; margin-top: 5px;">${metaInfo.join(' • ')}</div>`;
            }
        }
        
        return html;
    }

    async deleteMessage(messageElement) {
        // For now, just remove from UI
        // TODO: Implement server-side deletion when backend supports it
        if (confirm('Delete this message?')) {
            messageElement.remove();
        }
    }

    async loadSystemData() {
        await this.refreshHealth();
    }

    async refreshSystemData() {
        await this.refreshHealth();
    }

    async refreshHealth() {
        try {
            const response = await fetch('/health');
            const health = await response.json();
            
            if (health) {
                const brainStatus = `${health.brains?.mixtral === 'online' ? 'Online' : 'Offline'}`;
                this.updateConnectionStatus(brainStatus, health.status === 'healthy');
            }
        } catch (error) {
            console.error('Health check failed:', error);
        }
    }
}

// Context action functions
async function compressContext() {
    try {
        const response = await fetch('/api/context/compress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'compress' })
        });
        
        if (response.ok) {
            contextMonitor.updateContextUsage(30);
            tovaInterface.addMessage('system', 'Context compressed - older messages summarized.');
        }
    } catch (error) {
        console.error('Compress failed:', error);
        tovaInterface.addMessage('system', 'Compression failed: ' + error.message);
    }
}

async function resetContext() {
    if (confirm('Reset conversation context? This will clear the conversation history.')) {
        try {
            const response = await fetch('/api/context/reset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'reset' })
            });
            
            if (response.ok) {
                contextMonitor.updateContextUsage(0);
                document.getElementById('chatMessages').innerHTML = '';
                tovaInterface.addMessage('system', 'Context reset - conversation history cleared.');
            }
        } catch (error) {
            console.error('Reset failed:', error);
            tovaInterface.addMessage('system', 'Reset failed: ' + error.message);
        }
    }
}

// Debug panel functionality
let debugData = {
    memory: 0,
    modules: [],
    performance: {},
    context: {}
};

function toggleDebugPanel() {
    const panel = document.getElementById('debugPanel');
    panel.classList.toggle('show');
}

function showImmersiveDebug(message) {
    const popup = document.getElementById('immersive-debug-popup');
    popup.textContent = `💭 ${message}`;
    popup.classList.add('show');

    setTimeout(() => {
        popup.classList.remove('show');
    }, 4000);
}

function updateDebugData(data) {
    if (!data) return;
    
    // Update Memory (RAG) Section
    const memoryEl = document.getElementById('debugMemory');
    if (data.rag_status) {
        memoryEl.textContent = data.rag_status;
    }

    // Update Modules Section
    const modulesEl = document.getElementById('debugModules');
    if (data.active_modules && data.active_modules.length > 0) {
        modulesEl.innerHTML = data.active_modules.map(moduleName => {
            let type = 'function';
            if (moduleName === 'tova_core') type = 'core';
            else if (['focused', 'sleepy', 'excited', 'contemplative'].includes(moduleName)) type = 'mood';
            return `<span class="debug-module ${type}">${moduleName}</span>`;
        }).join('');
    } else {
        modulesEl.innerHTML = '<span class="debug-module core">tova_core</span>';
    }

    // Update Performance Section
    const perfEl = document.getElementById('debugPerformance');
    if (data.performance) {
        perfEl.innerHTML = `Processing: ${Math.round(data.performance.processing_time || 0)}ms<br>Context Length: ${data.performance.context_length || 0} chars<br>Tokens: ${data.performance.tokens_used || 0}`;
    }

    // Update Context Section
    const contextEl = document.getElementById('debugContext');
    if (data.context) {
        const contextUsage = data.context.usage_percent || 0;
        contextEl.innerHTML = `Context window: ${contextUsage}% used<br>Messages: ${data.context.message_count || 0}<br>Current mood: ${data.context.current_mood || 'neutral'}`;
    }
}

// Global instances
let tovaInterface;
let avatarManager;
let contextMonitor;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎭 Initializing TOVA v4 Interface...');
    
    // Initialize managers
    contextMonitor = new ContextMonitor();
    avatarManager = new AvatarManager();
    tovaInterface = new TovaInterface();
    
    // Set initial context usage
    contextMonitor.updateContextUsage(15);
    
    console.log('✅ TOVA v4 Interface ready!');
}); 