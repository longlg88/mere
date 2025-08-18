//
//  OfflineIntentProcessor.swift
//  MEREApp
//
//  Day 11: Offline Mode & Data Sync
//  Local intent processing for offline functionality
//

import Foundation
import Combine

struct OfflineIntent {
    let type: String
    let text: String
    let entities: [String: Any]
    let confidence: Double
}

class OfflineIntentProcessor: ObservableObject {
    static let shared = OfflineIntentProcessor()
    
    private let localDataManager = LocalDataManager.shared
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - Intent Processing
    
    func processIntent(from text: String) -> (intent: OfflineIntent, response: String) {
        let cleanText = text.lowercased().trimmingCharacters(in: .whitespacesAndNewlines)
        
        // Simple rule-based intent classification for offline mode
        if let intent = classifyIntent(text: cleanText) {
            let response = executeIntent(intent, originalText: text)
            return (intent, response)
        }
        
        // Fallback intent
        let fallbackIntent = OfflineIntent(
            type: "unknown",
            text: text,
            entities: [:],
            confidence: 0.0
        )
        
        return (fallbackIntent, "오프라인 모드에서는 기본적인 메모, 할일, 일정 관리만 가능합니다.")
    }
    
    // MARK: - Intent Classification
    
    private func classifyIntent(text: String) -> OfflineIntent? {
        // Memo creation patterns
        if containsAny(text, patterns: ["기록해", "메모해", "저장해", "적어", "기억해"]) {
            let entities = extractMemoEntities(from: text)
            return OfflineIntent(type: "create_memo", text: text, entities: entities, confidence: 0.9)
        }
        
        // Todo creation patterns
        if containsAny(text, patterns: ["할일", "해야", "작업", "업무", "태스크"]) &&
           containsAny(text, patterns: ["추가", "등록", "만들", "생성"]) {
            let entities = extractTodoEntities(from: text)
            return OfflineIntent(type: "create_todo", text: text, entities: entities, confidence: 0.9)
        }
        
        // Todo completion patterns
        if containsAny(text, patterns: ["완료", "끝", "다했", "마쳤"]) {
            let entities = extractTodoEntities(from: text)
            return OfflineIntent(type: "complete_todo", text: text, entities: entities, confidence: 0.8)
        }
        
        // Event creation patterns
        if containsAny(text, patterns: ["일정", "약속", "회의", "미팅", "만남"]) &&
           containsAny(text, patterns: ["잡아", "예약", "등록", "추가"]) {
            let entities = extractEventEntities(from: text)
            return OfflineIntent(type: "create_event", text: text, entities: entities, confidence: 0.9)
        }
        
        // Query patterns
        if containsAny(text, patterns: ["보여", "확인", "찾아", "검색", "알려"]) {
            if containsAny(text, patterns: ["메모", "기록"]) {
                return OfflineIntent(type: "query_memo", text: text, entities: [:], confidence: 0.8)
            } else if containsAny(text, patterns: ["할일", "태스크", "업무"]) {
                return OfflineIntent(type: "query_todo", text: text, entities: [:], confidence: 0.8)
            } else if containsAny(text, patterns: ["일정", "약속", "스케줄"]) {
                return OfflineIntent(type: "query_event", text: text, entities: [:], confidence: 0.8)
            }
        }
        
        // Greeting patterns
        if containsAny(text, patterns: ["안녕", "hello", "hi"]) {
            return OfflineIntent(type: "greeting", text: text, entities: [:], confidence: 0.9)
        }
        
        return nil
    }
    
    // MARK: - Entity Extraction
    
    private func extractMemoEntities(from text: String) -> [String: Any] {
        var entities: [String: Any] = [:]
        
        // Extract priority
        if containsAny(text, patterns: ["긴급", "중요", "급한"]) {
            entities["priority"] = "high"
        } else if containsAny(text, patterns: ["나중에", "여유"]) {
            entities["priority"] = "low"
        }
        
        // Extract category based on keywords
        if containsAny(text, patterns: ["업무", "일", "비즈니스"]) {
            entities["category"] = "업무"
        } else if containsAny(text, patterns: ["개인", "사적", "프라이빗"]) {
            entities["category"] = "개인"
        } else if containsAny(text, patterns: ["쇼핑", "구매", "사기"]) {
            entities["category"] = "쇼핑"
        } else if containsAny(text, patterns: ["건강", "운동", "병원"]) {
            entities["category"] = "건강"
        }
        
        // Extract content (everything after trigger words)
        let triggerWords = ["기록해", "메모해", "저장해", "적어", "기억해"]
        for trigger in triggerWords {
            if let range = text.range(of: trigger) {
                let content = String(text[..<range.lowerBound]).trimmingCharacters(in: .whitespacesAndNewlines)
                if !content.isEmpty {
                    entities["content"] = content
                }
                break
            }
        }
        
        return entities
    }
    
    private func extractTodoEntities(from text: String) -> [String: Any] {
        var entities: [String: Any] = [:]
        
        // Extract priority
        if containsAny(text, patterns: ["긴급", "급한", "중요한"]) {
            entities["priority"] = "high"
        }
        
        // Extract due date keywords
        if containsAny(text, patterns: ["오늘", "today"]) {
            entities["dueDate"] = "today"
        } else if containsAny(text, patterns: ["내일", "tomorrow"]) {
            entities["dueDate"] = "tomorrow"
        } else if containsAny(text, patterns: ["이번주", "this week"]) {
            entities["dueDate"] = "thisWeek"
        }
        
        // Extract category
        if containsAny(text, patterns: ["업무", "일", "프로젝트"]) {
            entities["category"] = "업무"
        } else if containsAny(text, patterns: ["개인", "사적"]) {
            entities["category"] = "개인"
        } else if containsAny(text, patterns: ["쇼핑", "구매"]) {
            entities["category"] = "쇼핑"
        }
        
        return entities
    }
    
    private func extractEventEntities(from text: String) -> [String: Any] {
        var entities: [String: Any] = [:]
        
        // Extract time patterns
        if containsAny(text, patterns: ["오늘", "today"]) {
            entities["date"] = "today"
        } else if containsAny(text, patterns: ["내일", "tomorrow"]) {
            entities["date"] = "tomorrow"
        } else if containsAny(text, patterns: ["다음주", "next week"]) {
            entities["date"] = "nextWeek"
        }
        
        // Extract location
        if containsAny(text, patterns: ["회사", "사무실", "office"]) {
            entities["location"] = "사무실"
        } else if containsAny(text, patterns: ["집", "home"]) {
            entities["location"] = "집"
        } else if containsAny(text, patterns: ["카페", "cafe"]) {
            entities["location"] = "카페"
        }
        
        // Extract duration
        if text.contains("시간") {
            let patterns = ["1시간", "2시간", "3시간", "30분", "1시간 30분"]
            for pattern in patterns {
                if text.contains(pattern) {
                    entities["duration"] = pattern
                    break
                }
            }
        }
        
        return entities
    }
    
    // MARK: - Intent Execution
    
    private func executeIntent(_ intent: OfflineIntent, originalText: String) -> String {
        switch intent.type {
        case "create_memo":
            return executeMemoCreation(intent: intent, originalText: originalText)
        case "create_todo":
            return executeTodoCreation(intent: intent, originalText: originalText)
        case "complete_todo":
            return executeTodoCompletion(intent: intent)
        case "create_event":
            return executeEventCreation(intent: intent, originalText: originalText)
        case "query_memo":
            return executeQueryMemo()
        case "query_todo":
            return executeQueryTodo()
        case "query_event":
            return executeQueryEvent()
        case "greeting":
            return "안녕하세요! 현재 오프라인 모드입니다. 기본적인 메모, 할일, 일정 관리를 도와드릴게요."
        default:
            return "죄송합니다. 오프라인 모드에서는 해당 기능을 처리할 수 없습니다."
        }
    }
    
    private func executeMemoCreation(intent: OfflineIntent, originalText: String) -> String {
        let content = intent.entities["content"] as? String ?? originalText
        let category = intent.entities["category"] as? String
        let priority = intent.entities["priority"] as? String
        
        let memo = localDataManager.createMemo(
            title: nil,
            content: content,
            category: category,
            priority: priority
        )
        
        var response = "메모를 저장했습니다: '\(content)'"
        if let category = category {
            response += " (카테고리: \(category))"
        }
        if let priority = priority {
            response += " (우선순위: \(priority))"
        }
        response += "\n온라인 연결 시 자동으로 동기화됩니다."
        
        return response
    }
    
    private func executeTodoCreation(intent: OfflineIntent, originalText: String) -> String {
        let title = extractTodoTitle(from: originalText)
        let category = intent.entities["category"] as? String
        let priority = intent.entities["priority"] as? String
        let dueDate = parseDueDate(from: intent.entities["dueDate"] as? String)
        
        let todo = localDataManager.createTodo(
            title: title,
            description: nil,
            dueDate: dueDate,
            priority: priority,
            category: category
        )
        
        var response = "할일을 추가했습니다: '\(title)'"
        if let dueDate = dueDate {
            let formatter = DateFormatter()
            formatter.dateStyle = .medium
            response += " (마감: \(formatter.string(from: dueDate)))"
        }
        response += "\n온라인 연결 시 자동으로 동기화됩니다."
        
        return response
    }
    
    private func executeTodoCompletion(intent: OfflineIntent) -> String {
        // For offline mode, complete the most recent incomplete todo
        let incompleteTodos = localDataManager.todos.filter { !$0.isCompleted && !$0.isDeleted }
        
        if let todo = incompleteTodos.first {
            localDataManager.completeTodo(todo)
            return "할일을 완료했습니다: '\(todo.title ?? "Unknown")'\n온라인 연결 시 자동으로 동기화됩니다."
        } else {
            return "완료할 할일이 없습니다."
        }
    }
    
    private func executeEventCreation(intent: OfflineIntent, originalText: String) -> String {
        let title = extractEventTitle(from: originalText)
        let location = intent.entities["location"] as? String
        let duration = intent.entities["duration"] as? String
        let scheduledAt = parseEventDate(from: intent.entities["date"] as? String)
        
        let event = localDataManager.createEvent(
            title: title,
            description: nil,
            scheduledAt: scheduledAt,
            duration: duration,
            location: location
        )
        
        var response = "일정을 등록했습니다: '\(title)'"
        if let location = location {
            response += " @ \(location)"
        }
        if let duration = duration {
            response += " (\(duration))"
        }
        response += "\n온라인 연결 시 자동으로 동기화됩니다."
        
        return response
    }
    
    private func executeQueryMemo() -> String {
        let recentMemos = Array(localDataManager.memos.prefix(5))
        if recentMemos.isEmpty {
            return "저장된 메모가 없습니다."
        }
        
        let memoList = recentMemos.map { memo in
            let content = memo.content?.prefix(30) ?? "내용 없음"
            return "• \(content)..."
        }.joined(separator: "\n")
        
        return "최근 메모 목록:\n\(memoList)"
    }
    
    private func executeQueryTodo() -> String {
        let incompleteTodos = localDataManager.todos.filter { !$0.isCompleted && !$0.isDeleted }
        if incompleteTodos.isEmpty {
            return "남은 할일이 없습니다."
        }
        
        let todoList = Array(incompleteTodos.prefix(5)).map { todo in
            return "• \(todo.title ?? "제목 없음")"
        }.joined(separator: "\n")
        
        return "남은 할일 목록:\n\(todoList)"
    }
    
    private func executeQueryEvent() -> String {
        let upcomingEvents = localDataManager.getUpcomingEvents(limit: 5)
        if upcomingEvents.isEmpty {
            return "예정된 일정이 없습니다."
        }
        
        let formatter = DateFormatter()
        formatter.dateStyle = .short
        formatter.timeStyle = .short
        
        let eventList = upcomingEvents.map { event in
            let dateStr = formatter.string(from: event.scheduledAt ?? Date())
            return "• \(event.title ?? "제목 없음") - \(dateStr)"
        }.joined(separator: "\n")
        
        return "예정된 일정:\n\(eventList)"
    }
    
    // MARK: - Helper Methods
    
    private func containsAny(_ text: String, patterns: [String]) -> Bool {
        return patterns.contains { text.contains($0) }
    }
    
    private func extractTodoTitle(from text: String) -> String {
        // Extract meaningful title from todo creation text
        let stopWords = ["할일", "추가", "등록", "만들", "생성", "해야", "해"]
        var words = text.components(separatedBy: .whitespacesAndNewlines)
        words = words.filter { word in
            !stopWords.contains { word.contains($0) }
        }
        return words.joined(separator: " ").trimmingCharacters(in: .whitespacesAndNewlines)
    }
    
    private func extractEventTitle(from text: String) -> String {
        // Extract meaningful title from event creation text
        let stopWords = ["일정", "약속", "잡아", "예약", "등록", "추가"]
        var words = text.components(separatedBy: .whitespacesAndNewlines)
        words = words.filter { word in
            !stopWords.contains { word.contains($0) }
        }
        return words.joined(separator: " ").trimmingCharacters(in: .whitespacesAndNewlines)
    }
    
    private func parseDueDate(from dateString: String?) -> Date? {
        guard let dateString = dateString else { return nil }
        
        let calendar = Calendar.current
        let now = Date()
        
        switch dateString {
        case "today":
            return calendar.startOfDay(for: now)
        case "tomorrow":
            return calendar.date(byAdding: .day, value: 1, to: calendar.startOfDay(for: now))
        case "thisWeek":
            return calendar.date(byAdding: .day, value: 7, to: now)
        default:
            return nil
        }
    }
    
    private func parseEventDate(from dateString: String?) -> Date {
        guard let dateString = dateString else { return Date() }
        
        let calendar = Calendar.current
        let now = Date()
        
        switch dateString {
        case "today":
            return now
        case "tomorrow":
            return calendar.date(byAdding: .day, value: 1, to: now) ?? now
        case "nextWeek":
            return calendar.date(byAdding: .day, value: 7, to: now) ?? now
        default:
            return now
        }
    }
}