# iOS MEREApp Setup Instructions

## Xcode Project Creation
Since iOS projects are best created through Xcode GUI, please follow these steps:

### 1. Create New Xcode Project
1. Open Xcode
2. File > New > Project
3. Choose "iOS" > "App"
4. Fill in the following details:
   - Product Name: `MEREApp`
   - Interface: `SwiftUI`
   - Language: `Swift`
   - Use Core Data: `No` (we'll add it later)
   - Include Tests: `Yes`

### 2. Project Location
- Save the project in: `/Users/eden.jang/Work/eden/mere/ios/`
- Final path should be: `/Users/eden.jang/Work/eden/mere/ios/MEREApp.xcodeproj`

### 3. Required Permissions (Info.plist)
Add these permissions to Info.plist:

```xml
<key>NSMicrophoneUsageDescription</key>
<string>MERE needs microphone access for voice commands</string>

<key>NSLocalNetworkUsageDescription</key>
<string>MERE needs network access to communicate with AI backend</string>
```

### 4. Basic Dependencies
No external dependencies needed initially - we'll use native iOS frameworks:
- `AVFoundation` (for audio recording/playback)
- `Network` (for WebSocket communication)
- `Combine` (for reactive programming)

### 5. Target Settings
- iOS Deployment Target: `16.0`
- Supported Device Orientations: `Portrait`

## Swift Files Implementation

The following Swift files have been created and should be added to your Xcode project:

### Core Components
- `ContentView.swift` - Main UI with PTT button and conversation history
- `AudioManager.swift` - Audio recording/playback with AVFoundation
- `WebSocketManager.swift` - Real-time server communication
- `AIService.swift` - STT/NLU/TTS integration with backend API

### Key Features Implemented
1. **Press-and-Hold PTT Button**: Long press to record, release to process
2. **Real-time Audio Level**: Visual feedback during recording
3. **Conversation History**: Scrollable chat-like interface
4. **TTS Audio Playback**: Automatic playback of AI responses with Base64 audio
5. **Audio Replay**: Manual replay button for AI messages with audio
6. **WebSocket Integration**: Real-time communication with backend
7. **Error Handling**: Comprehensive error handling and user feedback
8. **Permissions**: Automatic microphone permission requests

### File Integration Steps
1. Create the Xcode project as described above
2. Replace the default `ContentView.swift` with the provided one
3. Add the other `.swift` files to your project:
   - Drag and drop into Xcode
   - Or use File > Add Files to "MEREApp"
4. Ensure all files are added to the MEREApp target

### Backend Integration
The iOS app is configured to connect to:
- **HTTP API**: `http://localhost:8000` for audio processing
- **WebSocket**: `ws://localhost:8000/ws/ios-user` for real-time communication

Make sure the backend server is running before testing the app.

### Testing Prerequisites
Before running the iOS app, verify backend readiness:
```bash
python test_ios_integration.py
```

This will test:
- Backend health check
- STT service functionality  
- Full voice processing pipeline
- WebSocket connectivity