import Foundation
import Network
import Combine

/// WebSocket manager for communication with MERE backend
@MainActor
class WebSocketManager: NSObject, ObservableObject {
    
    // MARK: - Published Properties
    @Published var connectionState: ConnectionState = .disconnected
    @Published var lastMessage: String?
    @Published var error: WebSocketError?
    
    // MARK: - Private Properties
    private var webSocketTask: URLSessionWebSocketTask?
    private var urlSession: URLSession?
    private var reconnectTimer: Timer?
    private let baseURL: String
    private let userID: String
    private var reconnectAttempts = 0
    private let maxReconnectAttempts = 5
    
    // MARK: - Initialization
    init(baseURL: String = "ws://localhost:8000", userID: String = "ios-user") {
        self.baseURL = baseURL
        self.userID = userID
        super.init()
        setupURLSession()
    }
    
    private func setupURLSession() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        urlSession = URLSession(configuration: config, delegate: self, delegateQueue: nil)
    }
    
    // MARK: - Connection Management
    func connect() {
        guard connectionState != .connecting && connectionState != .connected else {
            return
        }
        
        guard let url = URL(string: "\(baseURL)/ws/\(userID)") else {
            error = .invalidURL
            return
        }
        
        connectionState = .connecting
        error = nil
        
        webSocketTask = urlSession?.webSocketTask(with: url)
        webSocketTask?.resume()
        
        // Start receiving messages
        receiveMessage()
        
        // Connection timeout
        DispatchQueue.main.asyncAfter(deadline: .now() + 10) { [weak self] in
            if self?.connectionState == .connecting {
                self?.error = .connectionTimeout
                self?.disconnect()
            }
        }
    }
    
    func disconnect() {
        reconnectTimer?.invalidate()
        reconnectTimer = nil
        
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        webSocketTask = nil
        connectionState = .disconnected
        reconnectAttempts = 0
    }
    
    private func attemptReconnect() {
        guard reconnectAttempts < maxReconnectAttempts else {
            error = .maxReconnectAttemptsReached
            return
        }
        
        reconnectAttempts += 1
        let delay = min(pow(2.0, Double(reconnectAttempts)), 30.0) // Exponential backoff, max 30s
        
        reconnectTimer = Timer.scheduledTimer(withTimeInterval: delay, repeats: false) { [weak self] _ in
            self?.connect()
        }
    }
    
    // MARK: - Message Handling
    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            DispatchQueue.main.async {
                switch result {
                case .success(let message):
                    self?.handleMessage(message)
                    self?.receiveMessage() // Continue receiving
                    
                case .failure(let error):
                    self?.handleError(error)
                }
            }
        }
    }
    
    private func handleMessage(_ message: URLSessionWebSocketTask.Message) {
        switch message {
        case .string(let text):
            lastMessage = text
            if let data = text.data(using: .utf8),
               let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                handleJSONMessage(json)
            }
            
        case .data(let data):
            if let text = String(data: data, encoding: .utf8) {
                lastMessage = text
            }
            
        @unknown default:
            break
        }
    }
    
    private func handleJSONMessage(_ json: [String: Any]) {
        // Handle different message types from the server
        if let type = json["type"] as? String {
            switch type {
            case "connection_ack":
                handleConnectionAck(json)
                
            case "ai_response":
                handleAIResponse(json)
                
            case "text_response":
                handleTextResponse(json)
                
            case "processing_status":
                handleProcessingStatus(json)
                
            case "pong":
                handlePong(json)
                
            case "status_response":
                handleStatusResponse(json)
                
            case "error":
                handleErrorMessage(json)
                
            default:
                print("Unknown message type: \(type)")
            }
        }
    }
    
    private func handleConnectionAck(_ json: [String: Any]) {
        if let message = json["message"] as? String {
            print("✅ WebSocket connected: \(message)")
            NotificationCenter.default.post(
                name: .websocketConnected,
                object: json
            )
        }
    }
    
    private func handleAIResponse(_ json: [String: Any]) {
        // Complete AI pipeline response with STT, NLU, and TTS data
        NotificationCenter.default.post(
            name: .aiResponseReceived,
            object: json
        )
    }
    
    private func handleTextResponse(_ json: [String: Any]) {
        // Text-only response
        NotificationCenter.default.post(
            name: .textResponseReceived,
            object: json
        )
    }
    
    private func handleProcessingStatus(_ json: [String: Any]) {
        // Processing status updates
        if let stage = json["stage"] as? String,
           let message = json["message"] as? String {
            NotificationCenter.default.post(
                name: .processingStatusUpdate,
                object: ["stage": stage, "message": message]
            )
        }
    }
    
    private func handlePong(_ json: [String: Any]) {
        // Pong response to ping
        if let timestamp = json["timestamp"] as? String {
            print("🏓 Pong received at: \(timestamp)")
        }
    }
    
    private func handleStatusResponse(_ json: [String: Any]) {
        // Server status response
        NotificationCenter.default.post(
            name: .serverStatusReceived,
            object: json
        )
    }
    
    private func handleErrorMessage(_ json: [String: Any]) {
        if let errorMessage = json["message"] as? String {
            error = .serverError(errorMessage)
            NotificationCenter.default.post(
                name: .websocketError,
                object: errorMessage
            )
        }
    }
    
    private func handleError(_ error: Error) {
        self.error = .connectionError(error)
        connectionState = .disconnected
        
        if let nsError = error as NSError?, nsError.code != NSURLErrorCancelled {
            attemptReconnect()
        }
    }
    
    // MARK: - Send Messages
    func sendText(_ text: String) {
        guard connectionState == .connected else {
            error = .notConnected
            return
        }
        
        let message = URLSessionWebSocketTask.Message.string(text)
        webSocketTask?.send(message) { [weak self] error in
            DispatchQueue.main.async {
                if let error = error {
                    self?.error = .sendError(error)
                }
            }
        }
    }
    
    func sendJSON(_ data: [String: Any]) {
        guard let jsonData = try? JSONSerialization.data(withJSONObject: data),
              let jsonString = String(data: jsonData, encoding: .utf8) else {
            error = .invalidJSON
            return
        }
        
        sendText(jsonString)
    }
    
    func sendVoiceCommand(_ text: String, confidence: Float = 1.0, audioBase64: String? = nil) {
        let message: [String: Any] = [
            "type": "voice_command",
            "text": text,
            "confidence": confidence,
            "audio_base64": audioBase64 as Any,
            "timestamp": Date().timeIntervalSince1970,
            "user_id": userID
        ]
        
        sendJSON(message)
    }
    
    func sendTextCommand(_ text: String) {
        let message: [String: Any] = [
            "type": "text_command",
            "text": text,
            "timestamp": Date().timeIntervalSince1970,
            "user_id": userID
        ]
        
        sendJSON(message)
    }
    
    func sendPing() {
        let message: [String: Any] = [
            "type": "ping",
            "timestamp": Date().timeIntervalSince1970,
            "user_id": userID
        ]
        
        sendJSON(message)
    }
    
    func requestServerStatus() {
        let message: [String: Any] = [
            "type": "status_request",
            "timestamp": Date().timeIntervalSince1970,
            "user_id": userID
        ]
        
        sendJSON(message)
    }
}

// MARK: - URLSessionWebSocketDelegate
extension WebSocketManager: URLSessionWebSocketDelegate {
    nonisolated func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
        DispatchQueue.main.async { [weak self] in
            self?.connectionState = .connected
            self?.reconnectAttempts = 0
            self?.error = nil
        }
    }
    
    nonisolated func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        DispatchQueue.main.async { [weak self] in
            self?.connectionState = .disconnected
            
            // Attempt reconnect unless it was a normal closure
            if closeCode != .normalClosure {
                self?.attemptReconnect()
            }
        }
    }
}

// MARK: - Supporting Types
enum ConnectionState {
    case disconnected
    case connecting
    case connected
    
    var description: String {
        switch self {
        case .disconnected: return "연결 안됨"
        case .connecting: return "연결 중..."
        case .connected: return "연결됨"
        }
    }
}

enum WebSocketError: LocalizedError {
    case invalidURL
    case invalidJSON
    case notConnected
    case connectionTimeout
    case connectionError(Error)
    case sendError(Error)
    case serverError(String)
    case maxReconnectAttemptsReached
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "잘못된 서버 URL"
        case .invalidJSON:
            return "JSON 형식 오류"
        case .notConnected:
            return "서버에 연결되지 않음"
        case .connectionTimeout:
            return "연결 시간 초과"
        case .connectionError(let error):
            return "연결 오류: \(error.localizedDescription)"
        case .sendError(let error):
            return "메시지 전송 오류: \(error.localizedDescription)"
        case .serverError(let message):
            return "서버 오류: \(message)"
        case .maxReconnectAttemptsReached:
            return "최대 재연결 시도 횟수 초과"
        }
    }
}

// MARK: - Notification Names
extension Notification.Name {
    static let websocketConnected = Notification.Name("websocketConnected")
    static let websocketError = Notification.Name("websocketError")
    static let aiResponseReceived = Notification.Name("aiResponseReceived")
    static let textResponseReceived = Notification.Name("textResponseReceived")
    static let processingStatusUpdate = Notification.Name("processingStatusUpdate")
    static let serverStatusReceived = Notification.Name("serverStatusReceived")
}