import SwiftUI
import Combine

/// Test view for WebSocket functionality
/// Can be integrated into the main app for testing WebSocket features
struct WebSocketTestView: View {
    @StateObject private var webSocketManager = WebSocketManager()
    @State private var testResults: [TestResult] = []
    @State private var isRunningTests = false
    @State private var currentTest = ""
    @State private var messageLog: [String] = []
    @State private var cancellables = Set<AnyCancellable>()
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Status Section
                statusSection
                
                // Test Controls
                testControlsSection
                
                // Test Results
                testResultsSection
                
                // Message Log
                messageLogSection
                
                Spacer()
            }
            .padding()
            .navigationTitle("WebSocket Test")
            .navigationBarTitleDisplayMode(.large)
            .onAppear {
                setupNotificationObservers()
            }
        }
    }
    
    // MARK: - Status Section
    private var statusSection: some View {
        VStack(spacing: 10) {
            HStack {
                Circle()
                    .fill(connectionStatusColor)
                    .frame(width: 12, height: 12)
                
                Text(webSocketManager.connectionState.description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Button("Connect") {
                    webSocketManager.connect()
                }
                .disabled(webSocketManager.connectionState == .connected)
                
                Button("Disconnect") {
                    webSocketManager.disconnect()
                }
                .disabled(webSocketManager.connectionState == .disconnected)
            }
            
            if let error = webSocketManager.error {
                Text("Error: \(error.localizedDescription)")
                    .font(.caption)
                    .foregroundColor(.red)
                    .multilineTextAlignment(.center)
            }
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(8)
    }
    
    // MARK: - Test Controls
    private var testControlsSection: some View {
        VStack(spacing: 10) {
            Button(action: runAllTests) {
                HStack {
                    if isRunningTests {
                        ProgressView()
                            .scaleEffect(0.8)
                    }
                    Text(isRunningTests ? "Running Tests..." : "Run All Tests")
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.blue)
                .foregroundColor(.white)
                .cornerRadius(8)
            }
            .disabled(isRunningTests || webSocketManager.connectionState != .connected)
            
            HStack(spacing: 10) {
                Button("Ping Test") {
                    runPingTest()
                }
                .buttonStyle(.bordered)
                
                Button("Status Test") {
                    runStatusTest()
                }
                .buttonStyle(.bordered)
                
                Button("Text Test") {
                    runTextTest()
                }
                .buttonStyle(.bordered)
            }
            
            if !currentTest.isEmpty {
                Text("Running: \(currentTest)")
                    .font(.caption)
                    .foregroundColor(.orange)
            }
        }
    }
    
    // MARK: - Test Results
    private var testResultsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Test Results")
                .font(.headline)
            
            if testResults.isEmpty {
                Text("No tests run yet")
                    .font(.caption)
                    .foregroundColor(.secondary)
            } else {
                ForEach(testResults.indices, id: \.self) { index in
                    let result = testResults[index]
                    HStack {
                        Image(systemName: result.passed ? "checkmark.circle.fill" : "xmark.circle.fill")
                            .foregroundColor(result.passed ? .green : .red)
                        
                        Text(result.testName)
                            .font(.body)
                        
                        Spacer()
                        
                        Text(String(format: "%.2fs", result.duration))
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(8)
    }
    
    // MARK: - Message Log
    private var messageLogSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Message Log")
                    .font(.headline)
                
                Spacer()
                
                Button("Clear") {
                    messageLog.removeAll()
                }
                .font(.caption)
            }
            
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 4) {
                    ForEach(Array(messageLog.enumerated()), id: \.offset) { index, message in
                        Text("\(index + 1). \(message)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                .padding(.vertical, 4)
            }
            .frame(maxHeight: 150)
            .background(Color.black.opacity(0.05))
            .cornerRadius(4)
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(8)
    }
    
    // MARK: - Test Functions
    private func runAllTests() {
        guard !isRunningTests else { return }
        
        isRunningTests = true
        testResults.removeAll()
        messageLog.removeAll()
        
        Task {
            await runPingTestAsync()
            await runStatusTestAsync()
            await runTextTestAsync()
            
            await MainActor.run {
                isRunningTests = false
                currentTest = ""
                logMessage("✅ All tests completed")
            }
        }
    }
    
    private func runPingTest() {
        Task {
            await runPingTestAsync()
        }
    }
    
    private func runStatusTest() {
        Task {
            await runStatusTestAsync()
        }
    }
    
    private func runTextTest() {
        Task {
            await runTextTestAsync()
        }
    }
    
    @MainActor
    private func runPingTestAsync() async {
        currentTest = "Ping Test"
        let startTime = Date()
        
        logMessage("📤 Sending ping...")
        webSocketManager.sendPing()
        
        // Wait for pong response (simplified - in real app would use proper async/await)
        try? await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
        
        let duration = Date().timeIntervalSince(startTime)
        let passed = messageLog.contains { $0.contains("Pong received") }
        
        testResults.append(TestResult(
            testName: "Ping-Pong Test",
            passed: passed,
            duration: duration
        ))
        
        logMessage(passed ? "✅ Ping test passed" : "❌ Ping test failed")
    }
    
    @MainActor
    private func runStatusTestAsync() async {
        currentTest = "Status Test"
        let startTime = Date()
        
        logMessage("📤 Requesting server status...")
        webSocketManager.requestServerStatus()
        
        // Wait for status response
        try? await Task.sleep(nanoseconds: 2_000_000_000) // 2 seconds
        
        let duration = Date().timeIntervalSince(startTime)
        let passed = messageLog.contains { $0.contains("Status response") }
        
        testResults.append(TestResult(
            testName: "Status Request Test",
            passed: passed,
            duration: duration
        ))
        
        logMessage(passed ? "✅ Status test passed" : "❌ Status test failed")
    }
    
    @MainActor
    private func runTextTestAsync() async {
        currentTest = "Text Command Test"
        let startTime = Date()
        
        logMessage("📤 Sending text command...")
        webSocketManager.sendTextCommand("내일 우유 사는 거 기억해줘")
        
        // Wait for AI response
        try? await Task.sleep(nanoseconds: 5_000_000_000) // 5 seconds
        
        let duration = Date().timeIntervalSince(startTime)
        let passed = messageLog.contains { $0.contains("Text response") || $0.contains("AI response") }
        
        testResults.append(TestResult(
            testName: "Text Command Test",
            passed: passed,
            duration: duration
        ))
        
        logMessage(passed ? "✅ Text command test passed" : "❌ Text command test failed")
    }
    
    // MARK: - Notification Observers
    private func setupNotificationObservers() {
        NotificationCenter.default.publisher(for: .websocketConnected)
            .sink { notification in
                if let data = notification.object as? [String: Any] {
                    logMessage("✅ Connected: \(data["message"] as? String ?? "Unknown")")
                }
            }
            .store(in: &cancellables)
        
        NotificationCenter.default.publisher(for: .aiResponseReceived)
            .sink { notification in
                if let data = notification.object as? [String: Any] {
                    let responseText = (data["response"] as? [String: Any])?["text"] as? String ?? "No response"
                    logMessage("🤖 AI response: \(responseText)")
                }
            }
            .store(in: &cancellables)
        
        NotificationCenter.default.publisher(for: .textResponseReceived)
            .sink { notification in
                if let data = notification.object as? [String: Any] {
                    let response = data["response"] as? String ?? "No response"
                    logMessage("💬 Text response: \(response)")
                }
            }
            .store(in: &cancellables)
        
        NotificationCenter.default.publisher(for: .processingStatusUpdate)
            .sink { notification in
                if let data = notification.object as? [String: Any] {
                    let message = data["message"] as? String ?? "Processing..."
                    logMessage("⚡ Processing: \(message)")
                }
            }
            .store(in: &cancellables)
        
        NotificationCenter.default.publisher(for: .serverStatusReceived)
            .sink { notification in
                if let data = notification.object as? [String: Any] {
                    logMessage("📊 Status response received")
                }
            }
            .store(in: &cancellables)
        
        NotificationCenter.default.publisher(for: .websocketError)
            .sink { notification in
                if let error = notification.object as? String {
                    logMessage("❌ WebSocket error: \(error)")
                }
            }
            .store(in: &cancellables)
    }
    
    private func logMessage(_ message: String) {
        let timestamp = DateFormatter.timeOnly.string(from: Date())
        messageLog.append("[\(timestamp)] \(message)")
        
        // Keep only last 50 messages
        if messageLog.count > 50 {
            messageLog.removeFirst(messageLog.count - 50)
        }
    }
    
    private var connectionStatusColor: Color {
        switch webSocketManager.connectionState {
        case .connected: return .green
        case .connecting: return .orange
        case .disconnected: return .red
        }
    }
}

// MARK: - Supporting Types
struct TestResult {
    let testName: String
    let passed: Bool
    let duration: TimeInterval
}

// MARK: - Preview
struct WebSocketTestView_Previews: PreviewProvider {
    static var previews: some View {
        WebSocketTestView()
    }
}