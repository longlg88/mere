//
//  NetworkMonitor.swift
//  MEREApp
//
//  Day 11: Offline Mode & Data Sync
//  Network connectivity monitoring for offline/online mode switching
//

import Network
import Foundation
import Combine

class NetworkMonitor: ObservableObject {
    static let shared = NetworkMonitor()
    
    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "NetworkMonitor")
    
    @Published var isConnected = false
    @Published var connectionType: ConnectionType = .unknown
    @Published var previousConnectionState = false
    
    enum ConnectionType {
        case wifi
        case cellular
        case ethernet
        case unknown
    }
    
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        startMonitoring()
        
        // React to connection changes
        $isConnected
            .removeDuplicates()
            .sink { [weak self] isConnected in
                self?.handleConnectionChange(isConnected: isConnected)
            }
            .store(in: &cancellables)
    }
    
    deinit {
        stopMonitoring()
    }
    
    // MARK: - Monitoring Control
    
    func startMonitoring() {
        monitor.pathUpdateHandler = { [weak self] path in
            DispatchQueue.main.async {
                self?.previousConnectionState = self?.isConnected ?? false
                self?.isConnected = path.status == .satisfied
                self?.updateConnectionType(from: path)
                
                print("🌐 Network status: \(self?.isConnected == true ? "Connected" : "Disconnected") (\(self?.connectionType.description ?? "unknown"))")
            }
        }
        
        monitor.start(queue: queue)
    }
    
    func stopMonitoring() {
        monitor.cancel()
    }
    
    // MARK: - Connection Type Detection
    
    private func updateConnectionType(from path: NWPath) {
        if path.usesInterfaceType(.wifi) {
            connectionType = .wifi
        } else if path.usesInterfaceType(.cellular) {
            connectionType = .cellular
        } else if path.usesInterfaceType(.wiredEthernet) {
            connectionType = .ethernet
        } else {
            connectionType = .unknown
        }
    }
    
    // MARK: - Connection Change Handling
    
    private func handleConnectionChange(isConnected: Bool) {
        if isConnected && !previousConnectionState {
            // Just came online
            print("📶 Connection restored - triggering sync")
            NotificationCenter.default.post(name: .networkConnected, object: nil)
            triggerDataSync()
        } else if !isConnected && previousConnectionState {
            // Just went offline
            print("📵 Connection lost - switching to offline mode")
            NotificationCenter.default.post(name: .networkDisconnected, object: nil)
        }
    }
    
    // MARK: - Data Sync Integration
    
    private func triggerDataSync() {
        // Trigger data synchronization when connection is restored
        guard isConnected else { return }
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
            // Give a moment for the connection to stabilize
            DataSyncManager.shared.syncAllData()
        }
    }
    
    // MARK: - Manual Network Check
    
    func checkNetworkConnection() -> Bool {
        return isConnected
    }
    
    func getConnectionQuality() -> ConnectionQuality {
        guard isConnected else { return .offline }
        
        switch connectionType {
        case .wifi, .ethernet:
            return .excellent
        case .cellular:
            return .good
        case .unknown:
            return .poor
        }
    }
    
    enum ConnectionQuality {
        case offline
        case poor
        case good
        case excellent
        
        var description: String {
            switch self {
            case .offline: return "오프라인"
            case .poor: return "연결 불안정"
            case .good: return "양호"
            case .excellent: return "우수"
            }
        }
    }
}

// MARK: - Connection Type Extension

extension NetworkMonitor.ConnectionType {
    var description: String {
        switch self {
        case .wifi: return "WiFi"
        case .cellular: return "Cellular"
        case .ethernet: return "Ethernet"
        case .unknown: return "Unknown"
        }
    }
}

// MARK: - Notification Names

extension Notification.Name {
    static let networkConnected = Notification.Name("networkConnected")
    static let networkDisconnected = Notification.Name("networkDisconnected")
    static let syncCompleted = Notification.Name("syncCompleted")
    static let syncFailed = Notification.Name("syncFailed")
}