# TOVA v4 Frontend Implementation

## Overview

The TOVA v4 frontend provides a modern, responsive chat interface that connects to the dual-brain AI system through WebSocket communication.

## Key Features

### 🎭 Enhanced Chat Interface
- **Real-time streaming**: Messages stream token-by-token from the dual-brain system
- **Avatar integration**: Video avatar that responds during conversations
- **Context monitoring**: Visual indicators for context usage and system status
- **Debug panel**: Comprehensive system information and monitoring
- **Console perf logs**: First-token latency and estimated tokens/sec are printed in the browser console

### 🧠 Dual-Brain Status
- **Mixtral status**: Primary brain (conversation handling)
- **Phi status**: Background brain (analysis and processing)
- **Health monitoring**: Real-time connectivity status

### 🎯 Context Management
- **Visual indicators**: Color-coded context usage (green/yellow/red)
- **Context actions**: Compress and reset functionality
- **Usage tracking**: Real-time context window monitoring

### 🔍 Debug Panel
- **Memory (RAG)**: Retrieval Augmented Generation status
- **Active modules**: Currently loaded personality and mood modules
- **Performance metrics**: Processing time, context length, token usage
- **System context**: Current mood, message count, usage percentage

## File Structure

```
frontend/
├── chat/
│   ├── index.html          # Main chat interface
│   ├── chat.css            # Enhanced styling with modern design
│   └── chat.js             # Real-time chat functionality
├── assets/
│   └── avatar/
│       └── tova_default.mp4 # Avatar video placeholder
└── admin/                  # Admin interface (future)
```

## Implementation Details

### Frontend Components

#### 1. Chat Interface (`index.html`)
- **Topbar**: Navigation with admin links
- **Chat pane**: Message display with custom scrollbar
- **Right pane**: Avatar container and debug panel
- **Input area**: Message input with send button

#### 2. Styling (`chat.css`)
- **Modern design**: Dark theme with purple accent colors
- **Responsive layout**: Mobile-friendly design
- **Custom scrollbar**: Gradient scrollbar with hover effects
- **Animations**: Smooth transitions and pulse effects

#### 3. JavaScript (`chat.js`)
- **WebSocket communication**: Real-time chat functionality
- **Context monitoring**: Visual context usage tracking
- **Avatar management**: Video playback coordination
- **Debug panel**: System information display
- **Console performance metrics**: First token latency and estimated tokens/sec via `console.info`

### Backend Integration

#### WebSocket Endpoints
- **`/chat`**: Main chat WebSocket endpoint
- **`/health`**: System health check endpoint
- **`/`**: Chat interface serving
- **`/admin`**: Admin interface serving

#### Message Types
- **`typing`**: Typing indicator
- **`response_chunk`**: Streaming response chunks
- **`response_complete`**: Response completion signal
- **`error`**: Error messages

### Configuration

#### Personality System
- **Core personality**: Base TOVA personality traits
- **Mood system**: Dynamic mood-based responses
- **Function system**: Task-specific behaviors

#### YAML Configuration
```yaml
# config/personalities/tova_core.yaml
name: "TOVA Core Personality"
description: "Base personality - always active"
prompt: |
  You are TOVA, a highly intelligent AI companion...
```

## Usage

### Starting the System
1. **Start the backend**: `./scripts/start/start_all.sh`
2. **Access the interface**: Navigate to `http://localhost:8002`
3. **Begin chatting**: Start a conversation with TOVA

### Debug Features
- **Debug panel**: Click the 💭 bubble in the avatar container
- **Context monitoring**: Watch for color changes in the avatar border
- **System status**: Monitor the status block for real-time information
- **Browser console**: Observe `[TOVA]` logs for first-token timing and estimated tokens/sec

### Mobile Support
- **Responsive design**: Automatically adapts to mobile screens
- **Touch-friendly**: Optimized for touch interactions
- **Full-screen avatar**: Avatar takes full screen on mobile

## Development

### Testing
Run the frontend test suite:
```bash
python test/test_frontend.py
```

### Customization
- **Styling**: Modify `frontend/chat/chat.css` for design changes
- **Functionality**: Update `frontend/chat/chat.js` for new features
- **Configuration**: Edit YAML files in `config/` for personality changes

### Adding New Features
1. **Frontend**: Add UI components in `index.html`
2. **Styling**: Add CSS rules in `chat.css`
3. **Functionality**: Implement JavaScript in `chat.js`
4. **Backend**: Add corresponding WebSocket handlers

## Future Enhancements

### Planned Features
- **Voice interaction**: Speech-to-text and text-to-speech
- **File uploads**: Document and image processing
- **Plugin system**: Extensible functionality
- **Advanced RAG**: Enhanced memory and retrieval
- **Multi-user support**: User authentication and sessions

### Technical Improvements
- **Performance optimization**: Reduced latency and improved responsiveness
- **Accessibility**: WCAG compliance and screen reader support
- **Internationalization**: Multi-language support
- **Offline mode**: Local processing capabilities

## Troubleshooting

### Common Issues
1. **WebSocket connection failed**: Check if backend services are running
2. **Avatar not loading**: Verify video file exists in assets directory
3. **Styling issues**: Clear browser cache and reload
4. **Performance problems**: Check system resources and network connectivity

### Debug Information
- **Browser console**: Check for JavaScript errors and performance logs
- **Network tab**: Monitor WebSocket connections
- **Debug panel**: View real-time system status
- **Logs**: Check backend logs for errors

## Contributing

When contributing to the frontend:
1. **Follow the design system**: Use existing CSS variables and classes
2. **Test responsiveness**: Ensure mobile compatibility
3. **Maintain accessibility**: Follow WCAG guidelines
4. **Update documentation**: Keep this file current
5. **Run tests**: Verify functionality before submitting

---

*This frontend implementation provides a modern, feature-rich interface for the TOVA v4 dual-brain AI system, enabling seamless human-AI interaction with real-time streaming, context awareness, and comprehensive system monitoring.* 