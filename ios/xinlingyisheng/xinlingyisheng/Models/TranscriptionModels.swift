import Foundation

struct TranscriptionResponse: Codable {
    let text: String
    let detectedLanguage: String?
    let confidence: Double?
    let durationMs: Int?
    let segments: [TranscriptionSegment]?
    
    enum CodingKeys: String, CodingKey {
        case text
        case detectedLanguage = "detected_language"
        case confidence
        case durationMs = "duration_ms"
        case segments
    }
}

struct TranscriptionSegment: Codable, Identifiable {
    let startMs: Int?
    let endMs: Int?
    let text: String
    let confidence: Double?
    
    var id: UUID { UUID() }
    
    enum CodingKeys: String, CodingKey {
        case startMs = "start_ms"
        case endMs = "end_ms"
        case text
        case confidence
    }
}
