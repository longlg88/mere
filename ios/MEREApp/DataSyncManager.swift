//
//  DataSyncManager.swift
//  MEREApp
//
//  Day 11: Offline Mode & Data Sync
//  Bidirectional data synchronization between local CoreData and backend server
//

import Foundation
import Combine

class DataSyncManager: ObservableObject {
    static let shared = DataSyncManager()
    
    private let localDataManager = LocalDataManager.shared
    private let networkMonitor = NetworkMonitor.shared
    private var cancellables = Set<AnyCancellable>()
    
    @Published var syncState: SyncState = .idle
    @Published var lastSyncTime: Date?
    @Published var syncProgress: Double = 0.0
    @Published var syncMessage: String = ""
    
    enum SyncState: Equatable {
        case idle
        case syncing
        case completed
        case failed(Error)
        
        static func == (lhs: SyncState, rhs: SyncState) -> Bool {
            switch (lhs, rhs) {
            case (.idle, .idle), (.syncing, .syncing), (.completed, .completed):
                return true
            case (.failed, .failed):
                return true
            default:
                return false
            }
        }
        
        var description: String {
            switch self {
            case .idle: return "대기 중"
            case .syncing: return "동기화 중"
            case .completed: return "완료"
            case .failed(let error): return "실패: \(error.localizedDescription)"
            }
        }
    }
    
    struct SyncStats {
        let totalItems: Int
        let syncedItems: Int
        let failedItems: Int
        let conflictItems: Int
    }
    
    init() {
        setupNetworkObservers()
        setupAutoSync()
    }
    
    // MARK: - Network Observers
    
    private func setupNetworkObservers() {
        NotificationCenter.default
            .publisher(for: .networkConnected)
            .sink { [weak self] _ in
                self?.onNetworkConnected()
            }
            .store(in: &cancellables)
        
        NotificationCenter.default
            .publisher(for: .networkDisconnected)
            .sink { [weak self] _ in
                self?.onNetworkDisconnected()
            }
            .store(in: &cancellables)
    }
    
    private func setupAutoSync() {
        // Auto-sync every 5 minutes when online
        Timer.publish(every: 300, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                guard let self = self,
                      self.networkMonitor.isConnected,
                      self.syncState != .syncing else { return }
                
                self.syncAllData()
            }
            .store(in: &cancellables)
    }
    
    // MARK: - Network Event Handlers
    
    private func onNetworkConnected() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            self.syncAllData()
        }
    }
    
    private func onNetworkDisconnected() {
        if syncState == .syncing {
            syncState = .failed(SyncError.networkUnavailable)
        }
    }
    
    // MARK: - Main Sync Methods
    
    func syncAllData() {
        guard networkMonitor.isConnected else {
            syncState = .failed(SyncError.networkUnavailable)
            return
        }
        
        guard syncState != .syncing else {
            print("⚠️ Sync already in progress")
            return
        }
        
        Task {
            await performFullSync()
        }
    }
    
    @MainActor
    private func performFullSync() async {
        syncState = .syncing
        syncProgress = 0.0
        syncMessage = "동기화 시작..."
        
        do {
            let stats = try await executeSyncProcess()
            
            syncState = .completed
            syncProgress = 1.0
            lastSyncTime = Date()
            syncMessage = "완료: \(stats.syncedItems)개 항목 동기화"
            
            print("✅ Sync completed: \(stats)")
            NotificationCenter.default.post(name: .syncCompleted, object: stats)
            
        } catch {
            syncState = .failed(error)
            syncMessage = "동기화 실패: \(error.localizedDescription)"
            
            print("❌ Sync failed: \(error)")
            NotificationCenter.default.post(name: .syncFailed, object: error)
        }
    }
    
    private func executeSyncProcess() async throws -> SyncStats {
        let unsyncedItems = localDataManager.getUnsyncedItems()
        let totalItems = unsyncedItems.memos.count + unsyncedItems.todos.count + unsyncedItems.events.count
        
        var syncedCount = 0
        var failedCount = 0
        
        // Upload local changes to server
        syncMessage = "로컬 변경사항 업로드 중..."
        syncProgress = 0.1
        
        // Sync memos
        for memo in unsyncedItems.memos {
            do {
                try await syncMemoToServer(memo)
                localDataManager.markAsSynced(memo: memo)
                syncedCount += 1
            } catch {
                print("❌ Failed to sync memo: \(error)")
                failedCount += 1
            }
            
            syncProgress = 0.1 + (0.3 * Double(syncedCount) / Double(totalItems))
        }
        
        // Sync todos
        for todo in unsyncedItems.todos {
            do {
                try await syncTodoToServer(todo)
                localDataManager.markAsSynced(todo: todo)
                syncedCount += 1
            } catch {
                print("❌ Failed to sync todo: \(error)")
                failedCount += 1
            }
            
            syncProgress = 0.1 + (0.3 * Double(syncedCount) / Double(totalItems))
        }
        
        // Sync events
        for event in unsyncedItems.events {
            do {
                try await syncEventToServer(event)
                localDataManager.markAsSynced(event: event)
                syncedCount += 1
            } catch {
                print("❌ Failed to sync event: \(error)")
                failedCount += 1
            }
            
            syncProgress = 0.1 + (0.3 * Double(syncedCount) / Double(totalItems))
        }
        
        // Download server changes
        syncMessage = "서버 변경사항 다운로드 중..."
        syncProgress = 0.5
        
        try await downloadServerChanges()
        syncProgress = 1.0
        
        return SyncStats(
            totalItems: totalItems,
            syncedItems: syncedCount,
            failedItems: failedCount,
            conflictItems: 0 // TODO: Implement conflict detection
        )
    }
    
    // MARK: - Individual Item Sync
    
    private func syncMemoToServer(_ memo: MemoEntity) async throws {
        let aiService = AIService.shared
        
        let _: [String: Any] = [
            "id": memo.memoId ?? UUID().uuidString,
            "title": memo.title ?? "",
            "content": memo.content ?? "",
            "category": memo.category ?? "",
            "priority": memo.priority ?? "",
            "created_at": memo.createdAt ?? Date(),
            "updated_at": memo.updatedAt ?? Date(),
            "is_deleted": memo.softDeleted
        ]
        
        // This would typically be an API call to sync with backend
        // For now, we'll simulate the sync
        try await simulateServerSync(delay: 0.1)
        print("📤 Memo synced to server: \(memo.content ?? "Unknown")")
    }
    
    private func syncTodoToServer(_ todo: TodoEntity) async throws {
        let aiService = AIService.shared
        
        let todoData: [String: Any] = [
            "id": todo.todoId ?? UUID().uuidString,
            "title": todo.title ?? "",
            "description": todo.todoDescription ?? "",
            "due_date": todo.dueDate as Any,
            "priority": todo.priority ?? "",
            "category": todo.category ?? "",
            "status": todo.status ?? "pending",
            "is_completed": todo.taskCompleted,
            "completed_at": todo.completedAt as Any,
            "created_at": todo.createdAt ?? Date(),
            "updated_at": todo.updatedAt ?? Date(),
            "is_deleted": todo.softDeleted
        ]
        
        try await simulateServerSync(delay: 0.1)
        print("📤 Todo synced to server: \(todo.title ?? "Unknown")")
    }
    
    private func syncEventToServer(_ event: EventEntity) async throws {
        let aiService = AIService.shared
        
        let _: [String: Any] = [
            "id": event.eventId ?? UUID().uuidString,
            "title": event.title ?? "",
            "description": event.eventDescription ?? "",
            "scheduled_at": event.scheduledAt ?? Date(),
            "duration": event.duration ?? "",
            "location": event.location ?? "",
            "participants": event.participants ?? "",
            "repeat_pattern": event.repeatPattern ?? "",
            "created_at": event.createdAt ?? Date(),
            "updated_at": event.updatedAt ?? Date(),
            "is_deleted": event.softDeleted
        ]
        
        try await simulateServerSync(delay: 0.1)
        print("📤 Event synced to server: \(event.title ?? "Unknown")")
    }
    
    private func downloadServerChanges() async throws {
        // This would typically fetch changes from the server
        // and update local data with conflict resolution
        
        try await simulateServerSync(delay: 0.5)
        print("📥 Downloaded server changes")
    }
    
    // MARK: - Simulation Helper
    
    private func simulateServerSync(delay: Double) async throws {
        try await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
        
        // Simulate occasional network failures
        if Double.random(in: 0...1) < 0.05 { // 5% failure rate
            throw SyncError.serverError("Simulated server error")
        }
    }
    
    // MARK: - Manual Sync Controls
    
    func forceSyncNow() {
        guard networkMonitor.isConnected else {
            syncState = .failed(SyncError.networkUnavailable)
            return
        }
        
        syncAllData()
    }
    
    func cancelSync() {
        if syncState == .syncing {
            syncState = .idle
            syncMessage = "동기화 취소됨"
        }
    }
    
    // MARK: - Sync Status
    
    func hasPendingChanges() -> Bool {
        return localDataManager.unsyncedItemsCount > 0
    }
    
    func getSyncStatus() -> String {
        let unsyncedCount = localDataManager.unsyncedItemsCount
        
        if unsyncedCount == 0 {
            return networkMonitor.isConnected ? "모든 데이터가 동기화됨" : "오프라인 (동기화 완료)"
        } else {
            return networkMonitor.isConnected 
                ? "동기화 대기 중 (\(unsyncedCount)개 항목)"
                : "오프라인 (\(unsyncedCount)개 항목 대기)"
        }
    }
    
    func getLastSyncDescription() -> String {
        guard let lastSyncTime = lastSyncTime else {
            return "동기화 기록 없음"
        }
        
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return "마지막 동기화: \(formatter.localizedString(for: lastSyncTime, relativeTo: Date()))"
    }
}

// MARK: - Sync Errors

enum SyncError: LocalizedError {
    case networkUnavailable
    case serviceUnavailable
    case serverError(String)
    case dataCorruption
    case conflictResolutionFailed
    
    var errorDescription: String? {
        switch self {
        case .networkUnavailable:
            return "네트워크 연결이 없습니다"
        case .serviceUnavailable:
            return "동기화 서비스를 사용할 수 없습니다"
        case .serverError(let message):
            return "서버 오류: \(message)"
        case .dataCorruption:
            return "데이터 손상이 감지되었습니다"
        case .conflictResolutionFailed:
            return "데이터 충돌 해결에 실패했습니다"
        }
    }
}
