import SwiftUI
import AVFoundation

struct ContentView: View {
    @StateObject private var audioManager = AudioManager()
    @StateObject private var webSocketManager = WebSocketManager()
    @StateObject private var aiService = AIService()
    
    @State private var conversationHistory: [ConversationItem] = []
    @State private var showingSettings = false
    @State private var serverURL = "http://localhost:8000"
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Header
                headerView
                
                // Conversation History
                conversationScrollView
                
                Spacer()
                
                // Audio Level Indicator
                audioLevelView
                
                // PTT Button
                pttButton
                
                // Status Information
                statusView
            }
            .padding()
            .navigationTitle("MERE AI")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Settings") {
                        showingSettings = true
                    }
                }
            }
            .sheet(isPresented: $showingSettings) {
                SettingsView(serverURL: $serverURL)
            }
        }
        .onAppear {
            setupServices()
        }
        .alert("권한 필요", isPresented: .constant(audioManager.permissionStatus == .denied)) {
            Button("Settings로 이동") {
                openAppSettings()
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("음성 명령을 사용하려면 마이크 권한이 필요합니다.")
        }
        .alert("오류", isPresented: .constant(audioManager.error != nil || aiService.error != nil)) {
            Button("OK") {
                audioManager.error = nil
                aiService.error = nil
            }
        } message: {
            Text(audioManager.error?.localizedDescription ?? aiService.error?.localizedDescription ?? "")
        }
    }
    
    // MARK: - Header View
    private var headerView: some View {
        VStack {
            HStack {
                Circle()
                    .fill(connectionStatusColor)
                    .frame(width: 12, height: 12)
                
                Text(webSocketManager.connectionState.description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
            }
            
            if aiService.isProcessing {
                HStack {
                    ProgressView()
                        .scaleEffect(0.8)
                    Text("AI 처리 중...")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
    }
    
    // MARK: - Conversation History
    private var conversationScrollView: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 12) {
                ForEach(conversationHistory) { item in
                    ConversationBubble(item: item)
                        .environmentObject(audioManager)
                        .environmentObject(aiService)
                }
            }
            .padding(.horizontal)
        }
        .frame(maxHeight: 300)
    }
    
    // MARK: - Audio Level Indicator
    private var audioLevelView: some View {
        Group {
            if audioManager.isRecording {
                VStack {
                    Text("🎤 녹음 중...")
                        .font(.caption)
                        .foregroundColor(.red)
                    
                    // Audio level bars
                    HStack(spacing: 2) {
                        ForEach(0..<20, id: \.self) { index in
                            Rectangle()
                                .fill(audioLevelColor(for: index))
                                .frame(width: 8, height: CGFloat(12 + index * 2))
                                .animation(.easeInOut(duration: 0.1), value: audioManager.audioLevel)
                        }
                    }
                    
                    Text(String(format: "%.1fs", audioManager.recordingDuration))
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
        }
    }
    
    // MARK: - PTT Button
    private var pttButton: some View {
        Button(action: {}) {
            ZStack {
                Circle()
                    .fill(pttButtonColor)
                    .frame(width: 120, height: 120)
                    .scaleEffect(audioManager.isRecording ? 1.1 : 1.0)
                    .animation(.easeInOut(duration: 0.1), value: audioManager.isRecording)
                
                Image(systemName: audioManager.isRecording ? "stop.circle.fill" : "mic.circle.fill")
                    .font(.system(size: 60))
                    .foregroundColor(.white)
            }
        }
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in
                    if !audioManager.isRecording && audioManager.permissionStatus == .granted {
                        startRecording()
                    }
                }
                .onEnded { _ in
                    if audioManager.isRecording {
                        stopRecording()
                    }
                }
        )
        .disabled(audioManager.permissionStatus != .granted)
    }
    
    // MARK: - Status View
    private var statusView: some View {
        VStack(spacing: 8) {
            Text("길게 눌러서 말하기")
                .font(.caption)
                .foregroundColor(.secondary)
            
            // Audio playback indicator
            if audioManager.isPlaying {
                HStack {
                    Image(systemName: "speaker.wave.2.fill")
                        .foregroundColor(.blue)
                    Text("응답 재생 중...")
                        .font(.caption2)
                        .foregroundColor(.blue)
                }
                .padding(4)
                .background(Color.blue.opacity(0.1))
                .cornerRadius(6)
            }
            
            if let lastResponse = aiService.lastResponse {
                VStack(alignment: .leading, spacing: 4) {
                    Text("STT: \(lastResponse.stt.text)")
                        .font(.caption2)
                    Text("Intent: \(lastResponse.nlu.intent) (\(String(format: "%.0f%%", lastResponse.nlu.confidence * 100)))")
                        .font(.caption2)
                    
                    // Audio indicator
                    if lastResponse.response.hasAudio {
                        HStack {
                            Image(systemName: "speaker.fill")
                                .foregroundColor(.green)
                            Text("TTS 음성 포함")
                                .font(.caption2)
                                .foregroundColor(.green)
                        }
                    } else {
                        HStack {
                            Image(systemName: "speaker.slash")
                                .foregroundColor(.gray)
                            Text("텍스트만")
                                .font(.caption2)
                                .foregroundColor(.gray)
                        }
                    }
                }
                .padding(8)
                .background(Color.gray.opacity(0.1))
                .cornerRadius(8)
            }
        }
    }
    
    // MARK: - Helper Methods
    private func setupServices() {
        // Update AI service URL if changed
        aiService = AIService(baseURL: serverURL)
        
        // Connect to WebSocket
        webSocketManager.connect()
        
        // Request microphone permission if needed
        if audioManager.permissionStatus == .undetermined {
            audioManager.requestPermission()
        }
    }
    
    private func startRecording() {
        audioManager.startRecording()
        
        // Add user message to conversation
        let userMessage = ConversationItem(
            id: UUID(),
            type: .user,
            content: "🎤 녹음 중...",
            timestamp: Date()
        )
        conversationHistory.append(userMessage)
    }
    
    private func stopRecording() {
        guard let recordingURL = audioManager.stopRecording(),
              let audioData = try? Data(contentsOf: recordingURL) else {
            return
        }
        
        // Update the last message to show processing
        if let lastIndex = conversationHistory.lastIndex(where: { $0.type == .user }) {
            conversationHistory[lastIndex].content = "🎤 처리 중..."
        }
        
        // Process the audio
        Task {
            await aiService.processVoiceCommand(audioData: audioData)
            
            if let response = aiService.lastResponse {
                // Update user message with STT result
                if let lastIndex = conversationHistory.lastIndex(where: { $0.type == .user }) {
                    conversationHistory[lastIndex].content = response.stt.text
                }
                
                // Add AI response
                let aiResponse = ConversationItem(
                    id: UUID(),
                    type: .ai,
                    content: response.response.text,
                    timestamp: Date()
                )
                conversationHistory.append(aiResponse)
                
                // Play TTS audio response if available
                audioManager.playAudioFromResponse(response.response)
                
            } else if let error = aiService.error {
                // Update user message with error
                if let lastIndex = conversationHistory.lastIndex(where: { $0.type == .user }) {
                    conversationHistory[lastIndex].content = "❌ \(error.localizedDescription)"
                }
            }
        }
        
        // Cleanup
        audioManager.cleanupTempFiles()
    }
    
    private var connectionStatusColor: Color {
        switch webSocketManager.connectionState {
        case .connected: return .green
        case .connecting: return .orange
        case .disconnected: return .red
        }
    }
    
    private var pttButtonColor: Color {
        if audioManager.permissionStatus != .granted {
            return .gray
        }
        return audioManager.isRecording ? .red : .blue
    }
    
    private func audioLevelColor(for index: Int) -> Color {
        let normalizedLevel = audioManager.audioLevel
        let threshold = Float(index) / 20.0
        
        if normalizedLevel > threshold {
            return index < 10 ? .green : (index < 15 ? .yellow : .red)
        } else {
            return .gray.opacity(0.3)
        }
    }
    
    private func openAppSettings() {
        if let settingsUrl = URL(string: UIApplication.openSettingsURLString) {
            UIApplication.shared.open(settingsUrl)
        }
    }
}

// MARK: - Supporting Views
struct ConversationBubble: View {
    let item: ConversationItem
    @EnvironmentObject private var audioManager: AudioManager
    @EnvironmentObject private var aiService: AIService
    
    var body: some View {
        HStack {
            if item.type == .ai {
                Spacer()
            }
            
            VStack(alignment: item.type == .user ? .trailing : .leading) {
                HStack {
                    Text(item.content)
                        .padding(12)
                        .background(item.type == .user ? Color.blue : Color.gray.opacity(0.2))
                        .foregroundColor(item.type == .user ? .white : .primary)
                        .cornerRadius(16)
                    
                    // Replay audio button for AI messages
                    if item.type == .ai && hasAudioForMessage {
                        Button(action: replayAudio) {
                            Image(systemName: audioManager.isPlaying ? "speaker.wave.2.fill" : "speaker.fill")
                                .foregroundColor(.blue)
                                .font(.caption)
                        }
                        .disabled(audioManager.isPlaying)
                    }
                }
                
                Text(DateFormatter.timeOnly.string(from: item.timestamp))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            if item.type == .user {
                Spacer()
            }
        }
    }
    
    private var hasAudioForMessage: Bool {
        // Check if the latest AI response has audio
        return aiService.lastResponse?.response.hasAudio == true
    }
    
    private func replayAudio() {
        guard let response = aiService.lastResponse else { return }
        audioManager.playAudioFromResponse(response.response)
    }
}

struct SettingsView: View {
    @Binding var serverURL: String
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            Form {
                Section("서버 설정") {
                    TextField("서버 URL", text: $serverURL)
                        .textContentType(.URL)
                        .keyboardType(.URL)
                        .autocapitalization(.none)
                }
                
                Section("앱 정보") {
                    HStack {
                        Text("버전")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("설정")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("완료") {
                        dismiss()
                    }
                }
            }
        }
    }
}

// MARK: - Supporting Types
struct ConversationItem: Identifiable {
    let id: UUID
    let type: MessageType
    var content: String
    let timestamp: Date
    
    enum MessageType {
        case user
        case ai
    }
}

extension DateFormatter {
    static let timeOnly: DateFormatter = {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        return formatter
    }()
}

// MARK: - Preview
struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}