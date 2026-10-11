import Foundation

struct TodayStats: Codable { var totals: [String: Double] = [:] }
struct SessionFile: Codable { var days: [String: [String: Double]] = [:] }
struct IPCMessage: Codable {
    var type: String
    var today: String?
    var totals: [String: Double]?
    var currentCat: String?
    var exe: String?
    var title: String?
    var visionText: String?
    var verdict: String?
    var visionTag: String?
    var limits: [String: Int]?
}

extension IPCMessage {
    static func totalsPayload(_ m: [String: Double], cat: String) -> IPCMessage {
        IPCMessage(type: "tick", today: ISO8601Day.now, totals: m, currentCat: cat)
    }
}
enum ISO8601Day { static var now: String { let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"; return f.string(from: Date()) } }
