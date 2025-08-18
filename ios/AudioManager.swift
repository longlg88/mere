import AVFoundation
import Combine
import Foundation
import os.log

/// Audio recording and playback manager for MERE app
@MainActor
class AudioManager: NSObject, ObservableObject {
    
    // MARK: - Published Properties
    @Published var isRecording = false
    @Published var isPlaying = false
    @Published var audioLevel: Float = 0.0
    @Published var recordingDuration: TimeInterval = 0.0
    @Published var permissionStatus: AVAudioSession.RecordPermission = .undetermined
    @Published var error: AudioError?
    
    // MARK: - Private Properties
    private var audioRecorder: AVAudioRecorder?
    private var audioPlayer: AVAudioPlayer?
    private var recordingTimer: Timer?
    private var levelTimer: Timer?
    private var audioSession: AVAudioSession
    private let logger = Logger(subsystem: "com.mere.app", category: "AudioManager")
    
    // Audio settings
    private let audioSettings: [String: Any] = [
        AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
        AVSampleRateKey: 16000.0, // 16kHz for Whisper
        AVNumberOfChannelsKey: 1, // Mono
        AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
    ]
    
    override init() {
        self.audioSession = AVAudioSession.sharedInstance()
        super.init()
        setupAudioSession()
        checkPermissions()
    }
    
    // MARK: - Setup
    private func setupAudioSession() {
        do {
            try audioSession.setCategory(
                .playAndRecord,
                mode: .default,
                options: [.defaultToSpeaker, .allowBluetooth]
            )
            try audioSession.setActive(true)
        } catch {
            self.error = .sessionSetupFailed(error)
        }
    }
    
    private func checkPermissions() {
        permissionStatus = audioSession.recordPermission
        
        if permissionStatus == .undetermined {
            requestPermission()
        }
    }
    
    func requestPermission() {
        audioSession.requestRecordPermission { [weak self] granted in
            DispatchQueue.main.async {
                self?.permissionStatus = granted ? .granted : .denied
            }
        }
    }
    
    // MARK: - Recording
    func startRecording() {
        guard permissionStatus == .granted else {
            error = .permissionDenied
            return
        }
        
        guard !isRecording else { return }
        
        // Create temporary file for recording
        let tempDir = FileManager.default.temporaryDirectory
        let recordingURL = tempDir.appendingPathComponent("recording_\(Date().timeIntervalSince1970).m4a")
        
        do {
            audioRecorder = try AVAudioRecorder(url: recordingURL, settings: audioSettings)
            audioRecorder?.delegate = self
            audioRecorder?.isMeteringEnabled = true
            audioRecorder?.prepareToRecord()
            
            if audioRecorder?.record() == true {
                isRecording = true
                recordingDuration = 0.0
                startTimers()
                error = nil
            } else {
                error = .recordingFailed("Failed to start recording")
            }
        } catch {
            self.error = .recordingFailed(error.localizedDescription)
        }
    }
    
    func stopRecording() -> URL? {
        guard isRecording else { return nil }
        
        audioRecorder?.stop()
        stopTimers()
        isRecording = false
        audioLevel = 0.0
        
        return audioRecorder?.url
    }
    
    // MARK: - Playback
    func playAudio(from url: URL) {
        do {
            audioPlayer = try AVAudioPlayer(contentsOf: url)
            audioPlayer?.delegate = self
            audioPlayer?.prepareToPlay()
            
            if audioPlayer?.play() == true {
                isPlaying = true
                error = nil
            } else {
                error = .playbackFailed("Failed to start playback")
            }
        } catch {
            self.error = .playbackFailed(error.localizedDescription)
        }
    }
    
    func playAudio(from data: Data) {
        do {
            audioPlayer = try AVAudioPlayer(data: data)
            audioPlayer?.delegate = self
            audioPlayer?.prepareToPlay()
            
            if audioPlayer?.play() == true {
                isPlaying = true
                error = nil
            } else {
                error = .playbackFailed("Failed to start playback")
            }
        } catch {
            self.error = .playbackFailed(error.localizedDescription)
        }
    }
    
    func playAudio(fromBase64 base64String: String) {
        guard let audioData = Data(base64Encoded: base64String) else {
            error = .playbackFailed("Invalid Base64 audio data")
            return
        }
        
        playAudio(from: audioData)
    }
    
    func playAudioFromResponse(_ response: ResponseData) {
        if response.hasAudio, let audioBase64 = response.audioBase64 {
            playAudio(fromBase64: audioBase64)
        } else {
            // No audio available - could implement TTS fallback or just skip
            logger.info("No audio data available in response")
        }
    }
    
    func stopPlayback() {
        audioPlayer?.stop()
        isPlaying = false
    }
    
    // MARK: - Timers
    private func startTimers() {
        recordingTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            guard let self = self, let recorder = self.audioRecorder else { return }
            self.recordingDuration = recorder.currentTime
        }
        
        levelTimer = Timer.scheduledTimer(withTimeInterval: 0.05, repeats: true) { [weak self] _ in
            guard let self = self, let recorder = self.audioRecorder else { return }
            recorder.updateMeters()
            
            // Convert dB to linear scale (0.0 to 1.0)
            let power = recorder.averagePower(forChannel: 0)
            let normalizedLevel = pow(10.0, (0.05 * power))
            self.audioLevel = Float(normalizedLevel)
        }
    }
    
    private func stopTimers() {
        recordingTimer?.invalidate()
        levelTimer?.invalidate()
        recordingTimer = nil
        levelTimer = nil
    }
    
    // MARK: - Utility
    func getRecordingData() -> Data? {
        guard let url = audioRecorder?.url else { return nil }
        return try? Data(contentsOf: url)
    }
    
    func cleanupTempFiles() {
        guard let url = audioRecorder?.url else { return }
        try? FileManager.default.removeItem(at: url)
    }
}

// MARK: - AVAudioRecorderDelegate
extension AudioManager: AVAudioRecorderDelegate {
    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        isRecording = false
        stopTimers()
        
        if !flag {
            error = .recordingFailed("Recording finished unsuccessfully")
        }
    }
    
    func audioRecorderEncodeErrorDidOccur(_ recorder: AVAudioRecorder, error: Error?) {
        isRecording = false
        stopTimers()
        self.error = .recordingFailed(error?.localizedDescription ?? "Unknown recording error")
    }
}

// MARK: - AVAudioPlayerDelegate
extension AudioManager: AVAudioPlayerDelegate {
    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        isPlaying = false
        
        if !flag {
            error = .playbackFailed("Playback finished unsuccessfully")
        }
    }
    
    func audioPlayerDecodeErrorDidOccur(_ player: AVAudioPlayer, error: Error?) {
        isPlaying = false
        self.error = .playbackFailed(error?.localizedDescription ?? "Unknown playback error")
    }
}

// MARK: - AudioError
enum AudioError: LocalizedError {
    case permissionDenied
    case sessionSetupFailed(Error)
    case recordingFailed(String)
    case playbackFailed(String)
    
    var errorDescription: String? {
        switch self {
        case .permissionDenied:
            return "마이크 사용 권한이 필요합니다"
        case .sessionSetupFailed(let error):
            return "오디오 세션 설정 실패: \(error.localizedDescription)"
        case .recordingFailed(let message):
            return "녹음 실패: \(message)"
        case .playbackFailed(let message):
            return "재생 실패: \(message)"
        }
    }
}