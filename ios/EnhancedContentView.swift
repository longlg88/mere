import SwiftUI
import AVFoundation

/// Enhanced ContentView with improved UI/UX for Day 7 completion
/// Key improvements: Better visual feedback, error handling, loading states
struct EnhancedContentView: View {
    @StateObject private var audioManager = AudioManager()
    @StateObject private var webSocketManager = WebSocketManager()
    @StateObject private var aiService = AIService()
    
    @State private var conversationHistory: [ConversationItem] = []
    @State private var showingSettings = false
    @State private var showingHelp = false
    @State private var serverURL = "http://localhost:8000"
    @State private var isFirstLaunch = true
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Enhanced Header with better status indicators
                enhancedHeaderView
                
                // Conversation History with improved scrolling
                conversationScrollView
                
                // Enhanced PTT Section
                pttSectionView
            }
            .navigationTitle("MERE AI")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItemGroup(placement: .navigationBarTrailing) {
                    Button(action: { showingHelp = true }) {
                        Image(systemName: "questionmark.circle")
                    }
                    
                    Button(action: { showingSettings = true }) {
                        Image(systemName: "gearshape")
                    }
                }
            }
            .sheet(isPresented: $showingSettings) {
                EnhancedSettingsView(serverURL: $serverURL)
            }
            .sheet(isPresented: $showingHelp) {
                HelpView()
            }
        }
        .onAppear {
            setupServices()
        }
        .alert("마이크 권한 필요", isPresented: .constant(audioManager.permissionStatus == .denied)) {
            Button("설정으로 이동") { openAppSettings() }
            Button("나중에", role: .cancel) { }
        } message: {
            Text("음성 명령을 사용하려면 마이크 권한을 허용해주세요.")
        }
        .alert("연결 오류", isPresented: .constant(webSocketManager.error != nil && !webSocketManager.connectionState.isConnected)) {
            Button("다시 연결") { webSocketManager.connect() }
            Button("확인", role: .cancel) { }
        } message: {
            Text(webSocketManager.error?.localizedDescription ?? "서버 연결에 실패했습니다.")
        }
        .alert("처리 오류", isPresented: .constant(aiService.error != nil)) {
            Button("확인") { aiService.error = nil }
        } message: {
            Text(aiService.error?.localizedDescription ?? "요청 처리에 실패했습니다.")
        }
    }
    
    // MARK: - Enhanced Header
    private var enhancedHeaderView: some View {
        VStack(spacing: 12) {
            // Connection Status with enhanced visual feedback
            HStack {
                ConnectionIndicator(state: webSocketManager.connectionState)
                
                Spacer()
                
                // Performance indicators
                if let response = aiService.lastResponse {
                    VStack(alignment: .trailing, spacing: 2) {
                        Text("응답시간: \(String(format: "%.1fs", response.processingTime))")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                        
                        Text("정확도: \(Int(response.nlu.confidence * 100))%")
                            .font(.caption2)
                            .foregroundColor(response.nlu.confidence > 0.8 ? .green : .orange)
                    }
                }
            }
            
            // Processing Status with enhanced feedback
            if aiService.isProcessing {
                HStack {
                    ProgressView()
                        .scaleEffect(0.8)
                    
                    VStack(alignment: .leading, spacing: 2) {
                        Text("AI 처리 중...")
                            .font(.caption)
                            .fontWeight(.medium)
                        
                        Text("STT → NLU → 응답 생성")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(Color.blue.opacity(0.1))
                .cornerRadius(8)
            }
            
            // Welcome message for first launch
            if isFirstLaunch && conversationHistory.isEmpty {
                VStack(spacing: 8) {
                    Text("👋 안녕하세요!")
                        .font(.headline)
                        .fontWeight(.semibold)
                    
                    Text("버튼을 길게 눌러서 음성 명령을 시작하세요")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                    
                    Text("예: \"내일 우유 사는 거 기억해줘\"")
                        .font(.caption)
                        .foregroundColor(.blue)
                        .italic()
                }
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(12)
                .onTapGesture {
                    isFirstLaunch = false
                }
            }
        }
        .padding(.horizontal)
        .padding(.top, 8)
    }
    
    // MARK: - Enhanced Conversation View
    private var conversationScrollView: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 16) {
                    ForEach(conversationHistory, id: \.id) { item in
                        EnhancedConversationBubble(item: item)
                            .environmentObject(audioManager)
                            .environmentObject(aiService)
                            .id(item.id)
                    }
                    
                    // Spacing for better visibility
                    Color.clear.frame(height: 20)
                }
                .padding(.horizontal)
            }
            .onChange(of: conversationHistory.count) { _ in
                // Auto-scroll to latest message
                if let lastItem = conversationHistory.last {
                    withAnimation(.easeOut(duration: 0.5)) {
                        proxy.scrollTo(lastItem.id, anchor: .bottom)
                    }
                }
            }
        }
        .frame(maxHeight: .infinity)
    }
    
    // MARK: - Enhanced PTT Section
    private var pttSectionView: some View {
        VStack(spacing: 20) {
            // Audio Level Visualization
            audioVisualizationView
            
            // Enhanced PTT Button
            enhancedPTTButton
            
            // Status and Tips
            statusAndTipsView
        }
        .padding(.horizontal)
        .padding(.bottom, 34) // Safe area padding
        .background(
            LinearGradient(
                gradient: Gradient(colors: [Color.clear, Color(UIColor.systemBackground)]),
                startPoint: .top,
                endPoint: .bottom
            )
        )
    }
    
    private var audioVisualizationView: some View {
        Group {
            if audioManager.isRecording {
                VStack(spacing: 8) {
                    Text("🎤 녹음 중")
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .foregroundColor(.red)
                    
                    // Enhanced audio visualization
                    HStack(spacing: 3) {
                        ForEach(0..<15, id: \.self) { index in
                            RoundedRectangle(cornerRadius: 2)
                                .fill(audioLevelColor(for: index))
                                .frame(width: 6, height: audioBarHeight(for: index))
                                .animation(.easeInOut(duration: 0.1), value: audioManager.audioLevel)
                        }
                    }
                    .frame(height: 40)
                    
                    Text(String(format: "%.1f초", audioManager.recordingDuration))
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            } else {
                // Show tip when not recording
                Text("버튼을 길게 눌러서 말하기")
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .opacity(0.7)
            }
        }
        .frame(height: 80)
    }
    
    private var enhancedPTTButton: some View {
        Button(action: {}) {
            ZStack {
                // Outer ring with pulse effect
                Circle()
                    .stroke(pttButtonColor.opacity(0.3), lineWidth: 4)
                    .frame(width: 140, height: 140)
                    .scaleEffect(audioManager.isRecording ? 1.15 : 1.0)
                    .opacity(audioManager.isRecording ? 0.7 : 1.0)
                    .animation(.easeInOut(duration: 0.6).repeatForever(autoreverses: true), 
                              value: audioManager.isRecording)
                
                // Main button
                Circle()
                    .fill(pttButtonGradient)
                    .frame(width: 120, height: 120)
                    .scaleEffect(audioManager.isRecording ? 1.05 : 1.0)
                    .animation(.easeInOut(duration: 0.1), value: audioManager.isRecording)
                    .shadow(color: pttButtonColor.opacity(0.3), radius: 8, x: 0, y: 4)
                
                // Button icon with animation
                Image(systemName: buttonIcon)
                    .font(.system(size: 50, weight: .medium))
                    .foregroundColor(.white)
                    .scaleEffect(audioManager.isRecording ? 0.9 : 1.0)
                    .animation(.easeInOut(duration: 0.1), value: audioManager.isRecording)
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
        .disabled(audioManager.permissionStatus != .granted || aiService.isProcessing)
        .hapticFeedback(.medium, trigger: audioManager.isRecording)
    }
    
    private var statusAndTipsView: some View {
        VStack(spacing: 8) {
            // Current status
            if audioManager.isPlaying {
                HStack {
                    Image(systemName: "speaker.wave.2.fill")
                        .foregroundColor(.blue)
                    Text("응답 재생 중...")
                        .font(.caption)
                        .foregroundColor(.blue)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 4)
                .background(Color.blue.opacity(0.1))
                .cornerRadius(6)
            }
            
            // Permission status
            if audioManager.permissionStatus != .granted {
                HStack {
                    Image(systemName: "mic.slash")
                        .foregroundColor(.orange)
                    Text("마이크 권한을 허용해주세요")
                        .font(.caption)
                        .foregroundColor(.orange)
                }
            }
            
            // Connection status
            if webSocketManager.connectionState != .connected {
                HStack {
                    Image(systemName: "wifi.slash")
                        .foregroundColor(.red)
                    Text("서버 연결 확인 중...")
                        .font(.caption)
                        .foregroundColor(.red)
                }
            }
        }
    }
    
    // MARK: - Helper Methods
    private func setupServices() {
        aiService.updateBaseURL(serverURL)
        webSocketManager.connect()
        
        if audioManager.permissionStatus == .undetermined {
            audioManager.requestPermission()
        }
        
        // Setup auto-reconnect
        Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { _ in
            if webSocketManager.connectionState == .disconnected {
                webSocketManager.connect()
            }
        }
    }
    
    private func startRecording() {
        isFirstLaunch = false
        
        guard audioManager.permissionStatus == .granted else { return }
        
        audioManager.startRecording()
        
        let userMessage = ConversationItem(
            id: UUID(),
            type: MessageType.user,
            content: "🎤 녹음 중...",
            timestamp: Date(),
            isProcessing: true
        )
        conversationHistory.append(userMessage)
    }
    
    private func stopRecording() {
        guard let recordingURL = audioManager.stopRecording(),
              let audioData = try? Data(contentsOf: recordingURL) else {
            return
        }
        
        // Update user message
        if let lastIndex = conversationHistory.lastIndex(where: { $0.type == .user && $0.isProcessing }) {
            conversationHistory[lastIndex].content = "🎤 처리 중..."
        }
        
        Task {
            let startTime = Date()
            await aiService.processVoiceCommand(audioData: audioData)
            let processingTime = Date().timeIntervalSince(startTime)
            
            await MainActor.run {
                if let response = aiService.lastResponse {
                    // Update user message with STT result
                    if let lastIndex = conversationHistory.lastIndex(where: { $0.type == .user && $0.isProcessing }) {
                        conversationHistory[lastIndex].content = response.stt.text
                        conversationHistory[lastIndex].isProcessing = false
                    }
                    
                    // Add AI response with metadata
                    let aiResponse = ConversationItem(
                        id: UUID(),
                        type: MessageType.ai,
                        content: response.response.text,
                        timestamp: Date(),
                        processingTime: processingTime,
                        confidence: Float(response.nlu.confidence),
                        hasAudio: response.response.hasAudio
                    )
                    conversationHistory.append(aiResponse)
                    
                    // Play TTS audio
                    audioManager.playAudioFromResponse(response.response)
                    
                } else if let error = aiService.error {
                    if let lastIndex = conversationHistory.lastIndex(where: { $0.type == .user && $0.isProcessing }) {
                        conversationHistory[lastIndex].content = "❌ \(error.localizedDescription)"
                        conversationHistory[lastIndex].isProcessing = false
                    }
                }
            }
        }
        
        audioManager.cleanupTempFiles()
    }
    
    // MARK: - Computed Properties
    private var pttButtonColor: Color {
        if audioManager.permissionStatus != .granted { return .gray }
        if aiService.isProcessing { return .orange }
        return audioManager.isRecording ? .red : .blue
    }
    
    private var pttButtonGradient: LinearGradient {
        LinearGradient(
            gradient: Gradient(colors: [pttButtonColor, pttButtonColor.opacity(0.8)]),
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }
    
    private var buttonIcon: String {
        if aiService.isProcessing { return "hourglass" }
        return audioManager.isRecording ? "stop.circle.fill" : "mic.circle.fill"
    }
    
    private func audioLevelColor(for index: Int) -> Color {
        let normalizedLevel = audioManager.audioLevel
        let threshold = Float(index) / 15.0
        
        if normalizedLevel > threshold {
            return index < 5 ? .green : (index < 10 ? .yellow : .red)
        } else {
            return .gray.opacity(0.2)
        }
    }
    
    private func audioBarHeight(for index: Int) -> CGFloat {
        let normalizedLevel = audioManager.audioLevel
        let threshold = Float(index) / 15.0
        let baseHeight: CGFloat = 8
        let maxHeight: CGFloat = 32
        
        if normalizedLevel > threshold {
            return baseHeight + (maxHeight - baseHeight) * CGFloat(normalizedLevel)
        } else {
            return baseHeight
        }
    }
    
    private func openAppSettings() {
        if let url = URL(string: UIApplication.openSettingsURLString) {
            UIApplication.shared.open(url)
        }
    }
}

// MARK: - Enhanced Supporting Views
struct ConnectionIndicator: View {
    let state: ConnectionState
    
    var body: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(statusColor)
                .frame(width: 10, height: 10)
                .animation(.easeInOut(duration: 0.3), value: state)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(state.description)
                    .font(.caption)
                    .fontWeight(.medium)
                
                Text(statusSubtitle)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
    }
    
    private var statusColor: Color {
        switch state {
        case .connected: return .green
        case .connecting: return .orange
        case .disconnected: return .red
        }
    }
    
    private var statusSubtitle: String {
        switch state {
        case .connected: return "서버 연결됨"
        case .connecting: return "연결 중..."
        case .disconnected: return "연결 안됨"
        }
    }
}

struct EnhancedConversationBubble: View {
    let item: ConversationItem
    @EnvironmentObject private var audioManager: AudioManager
    @EnvironmentObject private var aiService: AIService
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            if item.type == MessageType.ai {
                // AI avatar
                Circle()
                    .fill(LinearGradient(
                        gradient: Gradient(colors: [.blue, .purple]),
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ))
                    .frame(width: 32, height: 32)
                    .overlay(
                        Text("🤖")
                            .font(.caption)
                    )
            }
            
            VStack(alignment: item.type == .user ? .trailing : .leading, spacing: 8) {
                // Message bubble
                HStack(alignment: .bottom, spacing: 8) {
                    if item.type == MessageType.ai {
                        VStack(alignment: .leading, spacing: 4) {
                            messageBubble
                            messageMetadata
                        }
                        
                        // Audio replay button
                        if item.hasAudio {
                            Button(action: replayAudio) {
                                Image(systemName: audioManager.isPlaying ? "speaker.wave.2.fill" : "speaker.fill")
                                    .foregroundColor(.blue)
                                    .font(.title3)
                            }
                            .disabled(audioManager.isPlaying)
                        }
                    } else {
                        messageBubble
                    }
                }
                
                // Timestamp
                Text(DateFormatter.conversationTime.string(from: item.timestamp))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            
            if item.type == .user {
                // User avatar
                Circle()
                    .fill(Color.blue)
                    .frame(width: 32, height: 32)
                    .overlay(
                        Text("👤")
                            .font(.caption)
                    )
            }
            
            Spacer()
        }
    }
    
    private var messageBubble: some View {
        HStack {
            if item.isProcessing {
                ProgressView()
                    .scaleEffect(0.8)
            }
            
            Text(item.content)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
        }
        .background(
            RoundedRectangle(cornerRadius: 18)
                .fill(item.type == .user ? 
                      LinearGradient(gradient: Gradient(colors: [.blue, .blue.opacity(0.8)]), 
                                   startPoint: .topLeading, endPoint: .bottomTrailing) :
                      LinearGradient(gradient: Gradient(colors: [.gray.opacity(0.15), .gray.opacity(0.1)]), 
                                   startPoint: .topLeading, endPoint: .bottomTrailing)
                )
        )
        .foregroundColor(item.type == .user ? .white : .primary)
    }
    
    private var messageMetadata: some View {
        Group {
            if item.type == MessageType.ai {
                HStack(spacing: 12) {
                    if let processingTime = item.processingTime {
                        Label("\(String(format: "%.1fs", processingTime))", systemImage: "clock")
                    }
                    
                    if let confidence = item.confidence {
                        Label("\(Int(confidence * 100))%", systemImage: "checkmark.circle")
                            .foregroundColor(confidence > 0.8 ? .green : .orange)
                    }
                    
                    if item.hasAudio {
                        Label("음성", systemImage: "speaker.wave.1")
                            .foregroundColor(.blue)
                    }
                }
                .font(.caption2)
                .foregroundColor(.secondary)
            }
        }
    }
    
    private func replayAudio() {
        guard let response = aiService.lastResponse else { return }
        audioManager.playAudioFromResponse(response.response)
    }
}

// MARK: - Enhanced Settings View
struct EnhancedSettingsView: View {
    @Binding var serverURL: String
    @Environment(\.dismiss) private var dismiss
    @State private var showingAdvanced = false
    
    var body: some View {
        NavigationView {
            Form {
                Section("서버 설정") {
                    HStack {
                        Image(systemName: "server.rack")
                            .foregroundColor(.blue)
                        VStack(alignment: .leading) {
                            Text("서버 URL")
                                .font(.subheadline)
                            TextField("http://localhost:8000", text: $serverURL)
                                .textContentType(.URL)
                                .keyboardType(.URL)
                                .autocapitalization(.none)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                }
                
                Section("성능 정보") {
                    HStack {
                        Image(systemName: "speedometer")
                            .foregroundColor(.green)
                        Text("평균 응답시간")
                        Spacer()
                        Text("1.9초")
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Image(systemName: "checkmark.circle")
                            .foregroundColor(.green)
                        Text("성공률")
                        Spacer()
                        Text("85.7%")
                            .foregroundColor(.secondary)
                    }
                }
                
                Section("앱 정보") {
                    HStack {
                        Image(systemName: "info.circle")
                            .foregroundColor(.blue)
                        Text("버전")
                        Spacer()
                        Text("1.0.0 (Day 7)")
                            .foregroundColor(.secondary)
                    }
                    
                    HStack {
                        Image(systemName: "hammer.circle")
                            .foregroundColor(.orange)
                        Text("빌드")
                        Spacer()
                        Text("Week 1 Complete")
                            .foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("설정")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("완료") { dismiss() }
                }
            }
        }
    }
}

struct HelpView: View {
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    HelpSection(
                        icon: "mic.circle",
                        title: "음성 명령 사용법",
                        content: "파란색 버튼을 길게 눌러서 음성 명령을 시작하세요. 버튼을 놓으면 처리가 시작됩니다."
                    )
                    
                    HelpSection(
                        icon: "list.bullet",
                        title: "지원하는 명령어",
                        content: """
                        • \"내일 우유 사는 거 기억해줘\" - 메모 생성
                        • \"할일로 장보기 추가해줘\" - 할일 생성  
                        • \"메모 뭐 있는지 보여줘\" - 메모 조회
                        • \"할일 목록 보여줘\" - 할일 조회
                        """
                    )
                    
                    HelpSection(
                        icon: "speaker.wave.2",
                        title: "음성 재생",
                        content: "AI 응답에 스피커 아이콘이 있으면 음성으로 들을 수 있습니다. 아이콘을 탭하여 다시 재생할 수 있습니다."
                    )
                    
                    HelpSection(
                        icon: "wifi",
                        title: "연결 상태",
                        content: "화면 상단의 점이 연결 상태를 나타냅니다:\n• 초록색: 연결됨\n• 주황색: 연결 중\n• 빨간색: 연결 안됨"
                    )
                }
                .padding()
            }
            .navigationTitle("도움말")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("닫기") { dismiss() }
                }
            }
        }
    }
}

struct HelpSection: View {
    let icon: String
    let title: String
    let content: String
    
    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.blue)
                .frame(width: 30)
            
            VStack(alignment: .leading, spacing: 8) {
                Text(title)
                    .font(.headline)
                    .fontWeight(.semibold)
                
                Text(content)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }
}

// MARK: - Enhanced Supporting Types

extension ConnectionState {
    var isConnected: Bool {
        self == .connected
    }
}

extension DateFormatter {
    static let conversationTime: DateFormatter = {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        formatter.locale = Locale(identifier: "ko_KR")
        return formatter
    }()
}

// MARK: - Haptic Feedback Modifier
struct HapticFeedback: ViewModifier {
    let style: UIImpactFeedbackGenerator.FeedbackStyle
    let trigger: Bool
    
    func body(content: Content) -> some View {
        content
            .onChange(of: trigger) { _ in
                let impactFeedback = UIImpactFeedbackGenerator(style: style)
                impactFeedback.impactOccurred()
            }
    }
}

extension View {
    func hapticFeedback(_ style: UIImpactFeedbackGenerator.FeedbackStyle, trigger: Bool) -> some View {
        modifier(HapticFeedback(style: style, trigger: trigger))
    }
}

// MARK: - Preview
struct EnhancedContentView_Previews: PreviewProvider {
    static var previews: some View {
        EnhancedContentView()
    }
}