import Foundation

// MARK: - Message Types
enum MessageType {
    case user
    case ai
}

// MARK: - Conversation Item
struct ConversationItem: Identifiable {
    let id: UUID
    let type: MessageType
    var content: String
    let timestamp: Date
    var isProcessing: Bool = false
    var processingTime: TimeInterval?
    var confidence: Float?
    var hasAudio: Bool = false
    
    init(id: UUID = UUID(), type: MessageType, content: String, timestamp: Date = Date(), isProcessing: Bool = false, processingTime: TimeInterval? = nil, confidence: Float? = nil, hasAudio: Bool = false) {
        self.id = id
        self.type = type
        self.content = content
        self.timestamp = timestamp
        self.isProcessing = isProcessing
        self.processingTime = processingTime
        self.confidence = confidence
        self.hasAudio = hasAudio
    }
}