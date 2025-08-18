//
//  CoreDataStack.swift
//  MEREApp
//
//  Day 11: Offline Mode & Data Sync
//  CoreData stack implementation for local data storage
//

import CoreData
import Foundation

class CoreDataStack: ObservableObject {
    static let shared = CoreDataStack()
    
    // MARK: - Core Data stack
    
    lazy var persistentContainer: NSPersistentContainer = {
        let container = NSPersistentContainer(name: "MERE")
        
        container.loadPersistentStores(completionHandler: { [weak self] (storeDescription, error) in
            if let error = error as NSError? {
                print("❌ CoreData loading error: \(error), \(error.userInfo)")
                fatalError("Unresolved error \(error), \(error.userInfo)")
            } else {
                print("✅ CoreData loaded successfully")
                // Configure for automatic merging
                container.viewContext.automaticallyMergesChangesFromParent = true
                container.viewContext.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
            }
        })
        
        return container
    }()
    
    var viewContext: NSManagedObjectContext {
        return persistentContainer.viewContext
    }
    
    var backgroundContext: NSManagedObjectContext {
        return persistentContainer.newBackgroundContext()
    }
    
    // MARK: - Core Data Saving support
    
    func save() {
        let context = persistentContainer.viewContext
        
        if context.hasChanges {
            do {
                try context.save()
                print("✅ CoreData context saved successfully")
            } catch {
                let nsError = error as NSError
                print("❌ CoreData save error: \(nsError), \(nsError.userInfo)")
                fatalError("Unresolved error \(nsError), \(nsError.userInfo)")
            }
        }
    }
    
    func saveBackground(context: NSManagedObjectContext) {
        if context.hasChanges {
            do {
                try context.save()
                print("✅ Background context saved successfully")
            } catch {
                let nsError = error as NSError
                print("❌ Background context save error: \(nsError), \(nsError.userInfo)")
            }
        }
    }
    
    // MARK: - Utility Methods
    
    func performBackgroundTask(_ block: @escaping (NSManagedObjectContext) -> Void) {
        persistentContainer.performBackgroundTask(block)
    }
    
    func fetch<T: NSManagedObject>(_ request: NSFetchRequest<T>) -> [T] {
        do {
            return try viewContext.fetch(request)
        } catch {
            print("❌ Fetch error: \(error)")
            return []
        }
    }
    
    func count<T: NSManagedObject>(_ request: NSFetchRequest<T>) -> Int {
        do {
            return try viewContext.count(for: request)
        } catch {
            print("❌ Count error: \(error)")
            return 0
        }
    }
    
    // MARK: - Migration and Reset
    
    func deleteStore() {
        guard let storeURL = persistentContainer.persistentStoreDescriptions.first?.url else {
            return
        }
        
        do {
            try persistentContainer.persistentStoreCoordinator.destroyPersistentStore(
                at: storeURL,
                ofType: NSSQLiteStoreType,
                options: nil
            )
            print("✅ CoreData store deleted successfully")
        } catch {
            print("❌ Failed to delete store: \(error)")
        }
    }
    
    private init() {}
}

// MARK: - Preview Helper

extension CoreDataStack {
    static var preview: CoreDataStack = {
        let stack = CoreDataStack()
        let container = NSPersistentContainer(name: "MERE")
        
        // In-memory store for previews
        container.persistentStoreDescriptions.first?.url = URL(fileURLWithPath: "/dev/null")
        
        container.loadPersistentStores { _, error in
            if let error = error {
                fatalError("Preview store failed to load: \(error)")
            }
        }
        
        stack.persistentContainer = container
        return stack
    }()
}