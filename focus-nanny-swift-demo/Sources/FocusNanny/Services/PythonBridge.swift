import Foundation
import Combine

final class PythonBridge: ObservableObject {
    @Published var totals: [String: Double] = ["work": 0, "youtube_edu": 0, "youtube": 0, "game": 0, "idle": 0, "other": 0]
    @Published var currentCat: String = "other"
    @Published var exe: String = "—"
    @Published var title: String = "—"
    @Published var visionText: String = "ещё не смотрели — скрин каждые 90с"
    @Published var verdict: String = "—"
    @Published var visionTag: String = "other"
    @Published var connected: Bool = false

    private var task: Process?
    private var timer: AnyCancellable?
    private let pythonURL: URL
    private let bridgeURL: URL

    init(pythonPath: String = "/usr/bin/env") {
        pythonURL = URL(fileURLWithPath: pythonPath)
        let cwd = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
        bridgeURL = cwd.appendingPathComponent("../focus-nanny/bridge.py").standardized
        start()
        startMockIfNeeded()
    }

    func start() {
        guard FileManager.default.fileExists(atPath: bridgeURL.path) else { return }
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        p.arguments = ["python3", bridgeURL.path, "--jsonl"]
        let pipe = Pipe()
        p.standardOutput = pipe
        p.standardError = Pipe()
        do {
            try p.run()
            task = p
            connected = true
            pipe.fileHandleForReading.readabilityHandler = { [weak self] h in
                let data = h.availableData
                guard !data.isEmpty, let s = String(data: data, encoding: .utf8) else { return }
                for line in s.split(separator: "\n") {
                    self?.handle(line: String(line))
                }
            }
        } catch {
            connected = false
        }
    }

    func handle(line: String) {
        guard let d = line.data(using: .utf8),
              let m = try? JSONDecoder().decode(IPCMessage.self, from: d) else { return }
        DispatchQueue.main.async {
            if let t = m.totals { self.totals = t }
            if let c = m.currentCat { self.currentCat = c }
            if let e = m.exe { self.exe = e }
            if let ti = m.title { self.title = ti }
            if let v = m.visionText { self.visionText = v }
            if let ve = m.verdict { self.verdict = ve }
            if let tag = m.visionTag { self.visionTag = tag }
        }
    }

    func sendLimits(game: Int, youtube: Int, nag: Int, volume: Int) {
        let msg: [String: Any] = ["type": "set_limits", "game": game, "youtube": youtube, "nag": nag, "volume": volume]
        if let d = try? JSONSerialization.data(withJSONObject: msg), let s = String(data: d, encoding: .utf8) {
            task?.standardInput as? Pipe
            _ = s
        }
    }

    func triggerVision() {
        let msg = "{\"type\":\"vision_now\"}\n"
        if let d = msg.data(using: .utf8) {
            task?.standardInput?.fileHandleForWriting.write(d)
        }
    }

    func triggerNag() {
        DispatchQueue.main.async { self.verdict = "Тест: окно лимита — поверх окон и со звуком." }
    }

    private func startMockIfNeeded() {
        timer = Timer.publish(every: 1, on: .main, in: .common).autoconnect().sink { [weak self] _ in
            guard let self else { return }
            if self.connected { return }
            var t = self.totals
            let k = self.currentCat
            t[k, default: 0] += 1.0/60.0
            self.totals = t
            if Int.random(in: 0..<120) == 0 {
                self.currentCat = Category.allCases.randomElement()!.rawValue
            }
        }
    }

    func stop() {
        task?.terminate()
        timer?.cancel()
    }
}
