import Foundation
import Combine

/// AI service that integrates STT, NLU, and TTS through the backend API
@MainActor
class AIService: ObservableObject {
    
    // MARK: - Published Properties
    @Published var isProcessing = false
    @Published var lastResponse: AIResponse?
    @Published var error: AIError?
    
    // MARK: - Private Properties
    private var baseURL: String
    private var urlSession: URLSession
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - Initialization
    init(baseURL: String = "http://localhost:8000") {
        self.baseURL = baseURL
        
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        self.urlSession = URLSession(configuration: config)
    }
    
    // MARK: - Configuration
    func updateBaseURL(_ newBaseURL: String) {
        baseURL = newBaseURL
    }
    
    // MARK: - Voice Processing
    func processVoiceCommand(audioData: Data, filename: String = "recording.m4a") async {
        guard !isProcessing else { return }
        
        isProcessing = true
        error = nil
        
        do {
            let response = try await uploadAudioFile(audioData: audioData, filename: filename)
            lastResponse = response
        } catch {
            if let aiError = error as? AIError {
                self.error = aiError
            } else {
                self.error = .networkError(error)
            }
        }
        
        isProcessing = false
    }
    
    private func uploadAudioFile(audioData: Data, filename: String) async throws -> AIResponse {
        guard let url = URL(string: "\(baseURL)/api/voice/process") else {
            throw AIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        let httpBody = createMultipartBody(audioData: audioData, filename: filename, boundary: boundary)
        request.httpBody = httpBody
        
        let (data, response) = try await urlSession.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw AIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            if let errorData = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let errorMessage = errorData["detail"] as? String {
                throw AIError.serverError(errorMessage)
            }
            throw AIError.serverError("HTTP \(httpResponse.statusCode)")
        }
        
        return try parseAIResponse(from: data)
    }
    
    // MARK: - STT Only
    func transcribeAudio(audioData: Data, filename: String = "recording.m4a", language: String = "ko") async throws -> STTResponse {
        guard let url = URL(string: "\(baseURL)/api/stt/transcribe") else {
            throw AIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        var httpBody = Data()
        
        // Add file field
        httpBody.append("--\(boundary)\r\n")
        httpBody.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n")
        httpBody.append("Content-Type: audio/m4a\r\n\r\n")
        httpBody.append(audioData)
        httpBody.append("\r\n")
        
        // Add language field
        httpBody.append("--\(boundary)\r\n")
        httpBody.append("Content-Disposition: form-data; name=\"language\"\r\n\r\n")
        httpBody.append(language)
        httpBody.append("\r\n")
        
        httpBody.append("--\(boundary)--\r\n")
        
        request.httpBody = httpBody
        
        let (data, response) = try await urlSession.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw AIError.serverError("STT request failed")
        }
        
        return try parseSTTResponse(from: data)
    }
    
    // MARK: - Utility Methods
    private func createMultipartBody(audioData: Data, filename: String, boundary: String) -> Data {
        var httpBody = Data()
        
        // Add file field
        httpBody.append("--\(boundary)\r\n")
        httpBody.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n")
        httpBody.append("Content-Type: audio/m4a\r\n\r\n")
        httpBody.append(audioData)
        httpBody.append("\r\n")
        
        // Add language field
        httpBody.append("--\(boundary)\r\n")
        httpBody.append("Content-Disposition: form-data; name=\"language\"\r\n\r\n")
        httpBody.append("ko")
        httpBody.append("\r\n")
        
        httpBody.append("--\(boundary)--\r\n")
        
        return httpBody
    }
    
    private func parseAIResponse(from data: Data) throws -> AIResponse {
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw AIError.invalidJSON
        }
        
        guard let success = json["success"] as? Bool, success else {
            let errorMessage = json["error"] as? String ?? "Unknown error"
            throw AIError.serverError(errorMessage)
        }
        
        // Parse STT data
        guard let sttData = json["stt"] as? [String: Any],
              let text = sttData["text"] as? String,
              let sttConfidence = sttData["confidence"] as? Double else {
            throw AIError.invalidJSON
        }
        
        // Parse NLU data
        guard let nluData = json["nlu"] as? [String: Any],
              let intent = nluData["intent"] as? String,
              let nluConfidence = nluData["confidence"] as? Double else {
            throw AIError.invalidJSON
        }
        
        let entities = nluData["entities"] as? [String: Any] ?? [:]
        // Parse Response data
        let responseData: ResponseData
        if let responseDict = json["response"] as? [String: Any] {
            let responseText = responseDict["text"] as? String ?? "처리되었습니다."
            let audioBase64 = responseDict["audio_base64"] as? String
            responseData = ResponseData(text: responseText, audioBase64: audioBase64)
        } else {
            // Legacy support: response as string
            let responseText = json["response"] as? String ?? "처리되었습니다."
            responseData = ResponseData(text: responseText, audioBase64: nil)
        }
        
        return AIResponse(
            stt: STTResponse(
                success: true,
                text: text,
                confidence: sttConfidence,
                language: "ko"
            ),
            nlu: NLUResponse(
                intent: intent,
                confidence: nluConfidence,
                entities: entities
            ),
            response: responseData
        )
    }
    
    private func parseSTTResponse(from data: Data) throws -> STTResponse {
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw AIError.invalidJSON
        }
        
        guard let success = json["success"] as? Bool, success else {
            let errorMessage = json["error"] as? String ?? "STT failed"
            throw AIError.serverError(errorMessage)
        }
        
        guard let text = json["text"] as? String,
              let confidence = json["confidence"] as? Double,
              let language = json["language"] as? String else {
            throw AIError.invalidJSON
        }
        
        return STTResponse(
            success: success,
            text: text,
            confidence: confidence,
            language: language
        )
    }
    
    // MARK: - Health Check
    func checkServerHealth() async -> Bool {
        guard let url = URL(string: "\(baseURL)/health") else { return false }
        
        do {
            let (data, response) = try await urlSession.data(from: url)
            
            if let httpResponse = response as? HTTPURLResponse,
               httpResponse.statusCode == 200,
               let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
               let status = json["status"] as? String,
               status == "healthy" {
                return true
            }
        } catch {
            // Health check failed
        }
        
        return false
    }
}

// MARK: - Data Extensions
extension Data {
    mutating func append(_ string: String) {
        if let data = string.data(using: .utf8) {
            append(data)
        }
    }
}

// MARK: - Response Models
struct AIResponse {
    let stt: STTResponse
    let nlu: NLUResponse
    let response: ResponseData
    var processingTime: TimeInterval = 0
}

struct ResponseData {
    let text: String
    let audioBase64: String?
    
    var hasAudio: Bool {
        return audioBase64 != nil && !audioBase64!.isEmpty
    }
}

struct STTResponse {
    let success: Bool
    let text: String
    let confidence: Double
    let language: String
}

struct NLUResponse {
    let intent: String
    let confidence: Double
    let entities: [String: Any]
}

// MARK: - Error Types
enum AIError: LocalizedError {
    case invalidURL
    case invalidJSON
    case networkError(Error)
    case serverError(String)
    case invalidResponse
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "잘못된 서버 URL"
        case .invalidJSON:
            return "JSON 응답 파싱 오류"
        case .networkError(let error):
            return "네트워크 오류: \(error.localizedDescription)"
        case .serverError(let message):
            return "서버 오류: \(message)"
        case .invalidResponse:
            return "잘못된 서버 응답"
        }
    }
}