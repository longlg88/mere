//
//  LocalDataManager.swift
//  MEREApp
//
//  Day 11: Offline Mode & Data Sync
//  Local data management for offline functionality
//

import CoreData
import Foundation
import Combine

class LocalDataManager: ObservableObject {
    static let shared = LocalDataManager()
    
    private let coreDataStack = CoreDataStack.shared
    private var cancellables = Set<AnyCancellable>()
    
    // MARK: - Published Properties for UI
    @Published var memos: [MemoEntity] = []
    @Published var todos: [TodoEntity] = []
    @Published var events: [EventEntity] = []
    @Published var unsyncedItemsCount: Int = 0
    
    init() {
        loadAllData()
        updateUnsyncedCount()
    }
    
    // MARK: - Data Loading
    
    func loadAllData() {
        loadMemos()
        loadTodos()
        loadEvents()
    }
    
    private func loadMemos() {
        let request: NSFetchRequest<MemoEntity> = MemoEntity.fetchRequest()
        request.predicate = NSPredicate(format: "isDeleted == NO")
        request.sortDescriptors = [NSSortDescriptor(keyPath: \MemoEntity.createdAt, ascending: false)]
        
        memos = coreDataStack.fetch(request)
    }
    
    private func loadTodos() {
        let request: NSFetchRequest<TodoEntity> = TodoEntity.fetchRequest()
        request.predicate = NSPredicate(format: "isDeleted == NO")
        request.sortDescriptors = [NSSortDescriptor(keyPath: \TodoEntity.createdAt, ascending: false)]
        
        todos = coreDataStack.fetch(request)
    }
    
    private func loadEvents() {
        let request: NSFetchRequest<EventEntity> = EventEntity.fetchRequest()
        request.predicate = NSPredicate(format: "isDeleted == NO")
        request.sortDescriptors = [NSSortDescriptor(keyPath: \EventEntity.scheduledAt, ascending: true)]
        
        events = coreDataStack.fetch(request)
    }
    
    // MARK: - Memo Operations
    
    func createMemo(title: String?, content: String, category: String? = nil, priority: String? = nil) -> MemoEntity {
        let context = coreDataStack.viewContext
        let memo = MemoEntity(context: context)
        
        memo.memoId = UUID().uuidString
        memo.title = title
        memo.content = content
        memo.category = category
        memo.priority = priority
        memo.userId = getCurrentUserId()
        memo.createdAt = Date()
        memo.updatedAt = Date()
        memo.isSynced = false
        memo.isDeleted = false
        
        coreDataStack.save()
        loadMemos()
        updateUnsyncedCount()
        
        print("✅ Memo created locally: \(content)")
        return memo
    }
    
    func updateMemo(_ memo: MemoEntity, title: String?, content: String, category: String? = nil, priority: String? = nil) {
        memo.title = title
        memo.content = content
        memo.category = category
        memo.priority = priority
        memo.updatedAt = Date()
        memo.isSynced = false
        
        coreDataStack.save()
        loadMemos()
        updateUnsyncedCount()
        
        print("✅ Memo updated locally: \(content)")
    }
    
    func deleteMemo(_ memo: MemoEntity) {
        memo.isDeleted = true
        memo.updatedAt = Date()
        memo.isSynced = false
        
        coreDataStack.save()
        loadMemos()
        updateUnsyncedCount()
        
        print("✅ Memo marked as deleted locally")
    }
    
    // MARK: - Todo Operations
    
    func createTodo(title: String, description: String? = nil, dueDate: Date? = nil, priority: String? = nil, category: String? = nil) -> TodoEntity {
        let context = coreDataStack.viewContext
        let todo = TodoEntity(context: context)
        
        todo.todoId = UUID().uuidString
        todo.title = title
        todo.todoDescription = description
        todo.dueDate = dueDate
        todo.priority = priority
        todo.category = category
        todo.status = "pending"
        todo.isCompleted = false
        todo.userId = getCurrentUserId()
        todo.createdAt = Date()
        todo.updatedAt = Date()
        todo.isSynced = false
        todo.isDeleted = false
        
        coreDataStack.save()
        loadTodos()
        updateUnsyncedCount()
        
        print("✅ Todo created locally: \(title)")
        return todo
    }
    
    func updateTodo(_ todo: TodoEntity, title: String? = nil, description: String? = nil, dueDate: Date? = nil, priority: String? = nil, category: String? = nil) {
        if let title = title { todo.title = title }
        if let description = description { todo.todoDescription = description }
        if let dueDate = dueDate { todo.dueDate = dueDate }
        if let priority = priority { todo.priority = priority }
        if let category = category { todo.category = category }
        
        todo.updatedAt = Date()
        todo.isSynced = false
        
        coreDataStack.save()
        loadTodos()
        updateUnsyncedCount()
        
        print("✅ Todo updated locally: \(todo.title ?? "Unknown")")
    }
    
    func completeTodo(_ todo: TodoEntity) {
        todo.isCompleted = true
        todo.status = "completed"
        todo.completedAt = Date()
        todo.updatedAt = Date()
        todo.isSynced = false
        
        coreDataStack.save()
        loadTodos()
        updateUnsyncedCount()
        
        print("✅ Todo completed locally: \(todo.title ?? "Unknown")")
    }
    
    func deleteTodo(_ todo: TodoEntity) {
        todo.isDeleted = true
        todo.updatedAt = Date()
        todo.isSynced = false
        
        coreDataStack.save()
        loadTodos()
        updateUnsyncedCount()
        
        print("✅ Todo marked as deleted locally")
    }
    
    // MARK: - Event Operations
    
    func createEvent(title: String, description: String? = nil, scheduledAt: Date, duration: String? = nil, location: String? = nil, participants: String? = nil, repeatPattern: String? = nil) -> EventEntity {
        let context = coreDataStack.viewContext
        let event = EventEntity(context: context)
        
        event.eventId = UUID().uuidString
        event.title = title
        event.eventDescription = description
        event.scheduledAt = scheduledAt
        event.duration = duration
        event.location = location
        event.participants = participants
        event.repeatPattern = repeatPattern
        event.userId = getCurrentUserId()
        event.createdAt = Date()
        event.updatedAt = Date()
        event.isSynced = false
        event.isDeleted = false
        
        coreDataStack.save()
        loadEvents()
        updateUnsyncedCount()
        
        print("✅ Event created locally: \(title)")
        return event
    }
    
    func updateEvent(_ event: EventEntity, title: String? = nil, description: String? = nil, scheduledAt: Date? = nil, duration: String? = nil, location: String? = nil, participants: String? = nil) {
        if let title = title { event.title = title }
        if let description = description { event.eventDescription = description }
        if let scheduledAt = scheduledAt { event.scheduledAt = scheduledAt }
        if let duration = duration { event.duration = duration }
        if let location = location { event.location = location }
        if let participants = participants { event.participants = participants }
        
        event.updatedAt = Date()
        event.isSynced = false
        
        coreDataStack.save()
        loadEvents()
        updateUnsyncedCount()
        
        print("✅ Event updated locally: \(event.title ?? "Unknown")")
    }
    
    func deleteEvent(_ event: EventEntity) {
        event.isDeleted = true
        event.updatedAt = Date()
        event.isSynced = false
        
        coreDataStack.save()
        loadEvents()
        updateUnsyncedCount()
        
        print("✅ Event marked as deleted locally")
    }
    
    // MARK: - Sync Support
    
    func getUnsyncedItems() -> (memos: [MemoEntity], todos: [TodoEntity], events: [EventEntity]) {
        let memoRequest: NSFetchRequest<MemoEntity> = MemoEntity.fetchRequest()
        memoRequest.predicate = NSPredicate(format: "isSynced == NO")
        
        let todoRequest: NSFetchRequest<TodoEntity> = TodoEntity.fetchRequest()
        todoRequest.predicate = NSPredicate(format: "isSynced == NO")
        
        let eventRequest: NSFetchRequest<EventEntity> = EventEntity.fetchRequest()
        eventRequest.predicate = NSPredicate(format: "isSynced == NO")
        
        return (
            memos: coreDataStack.fetch(memoRequest),
            todos: coreDataStack.fetch(todoRequest),
            events: coreDataStack.fetch(eventRequest)
        )
    }
    
    func markAsSynced(memo: MemoEntity) {
        memo.isSynced = true
        coreDataStack.save()
        updateUnsyncedCount()
    }
    
    func markAsSynced(todo: TodoEntity) {
        todo.isSynced = true
        coreDataStack.save()
        updateUnsyncedCount()
    }
    
    func markAsSynced(event: EventEntity) {
        event.isSynced = true
        coreDataStack.save()
        updateUnsyncedCount()
    }
    
    private func updateUnsyncedCount() {
        let unsyncedItems = getUnsyncedItems()
        unsyncedItemsCount = unsyncedItems.memos.count + unsyncedItems.todos.count + unsyncedItems.events.count
    }
    
    // MARK: - Utility
    
    private func getCurrentUserId() -> String {
        // For now, return a default user ID
        // In production, this should be fetched from authentication service
        return "default-user"
    }
    
    // MARK: - Search and Query
    
    func searchMemos(query: String) -> [MemoEntity] {
        let request: NSFetchRequest<MemoEntity> = MemoEntity.fetchRequest()
        request.predicate = NSPredicate(format: "isDeleted == NO AND (content CONTAINS[c] %@ OR title CONTAINS[c] %@)", query, query)
        request.sortDescriptors = [NSSortDescriptor(keyPath: \MemoEntity.updatedAt, ascending: false)]
        
        return coreDataStack.fetch(request)
    }
    
    func searchTodos(query: String) -> [TodoEntity] {
        let request: NSFetchRequest<TodoEntity> = TodoEntity.fetchRequest()
        request.predicate = NSPredicate(format: "isDeleted == NO AND (title CONTAINS[c] %@ OR todoDescription CONTAINS[c] %@)", query, query)
        request.sortDescriptors = [NSSortDescriptor(keyPath: \TodoEntity.updatedAt, ascending: false)]
        
        return coreDataStack.fetch(request)
    }
    
    func getTodosByCategory(_ category: String) -> [TodoEntity] {
        let request: NSFetchRequest<TodoEntity> = TodoEntity.fetchRequest()
        request.predicate = NSPredicate(format: "isDeleted == NO AND category == %@", category)
        request.sortDescriptors = [NSSortDescriptor(keyPath: \TodoEntity.createdAt, ascending: false)]
        
        return coreDataStack.fetch(request)
    }
    
    func getUpcomingEvents(limit: Int = 10) -> [EventEntity] {
        let request: NSFetchRequest<EventEntity> = EventEntity.fetchRequest()
        request.predicate = NSPredicate(format: "isDeleted == NO AND scheduledAt >= %@", Date() as NSDate)
        request.sortDescriptors = [NSSortDescriptor(keyPath: \EventEntity.scheduledAt, ascending: true)]
        request.fetchLimit = limit
        
        return coreDataStack.fetch(request)
    }
}