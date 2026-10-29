// Yeufonic.app's own program: the icon in the menu bar, with the Python launcher as its child.
//
// macOS 26 shows a menu-bar icon only for the program the app was opened as: a shell script
// that hands over to Python with exec, as the app's program did at first, made an icon nobody
// could see.  So this program stays, owns the icon and its menu, and runs Resources/start.sh,
// which sets the install up when it needs it (and then ends) or runs `launcher.py --child`.
// The launcher reports on its output in lines starting "@@" (see run_child in launcher.py);
// Restart the engine is SIGUSR1 to it, and quitting is SIGTERM.
import AppKit

let appName = "Yeufonic"
let environment = ProcessInfo.processInfo.environment
let home = FileManager.default.homeDirectoryForCurrentUser
let logs = URL(fileURLWithPath: environment["YEUFONIC_LOGS"]
               ?? home.appendingPathComponent("Library/Logs/\(appName)").path)

final class Menu: NSObject, NSApplicationDelegate {
    var item: NSStatusItem?
    var child: Process?
    var url = ""           // the page, once the launcher has said where it is
    var failure = ""       // why it could not start, from the launcher
    var quitting = false
    var leftover = ""

    func applicationDidFinishLaunching(_ note: Notification) {
        startChild()
    }

    /// Once the launcher has started: before then setup may still be about to run instead.
    func showIcon() {
        guard item == nil else { return }
        let bar = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        bar.button?.image = mark()
        bar.button?.toolTip = appName
        let menu = NSMenu()
        for (title, action) in [("Open \(appName)", #selector(openPage)), ("Show the logs", #selector(showLogs)),
                                ("Restart the engine", #selector(restartEngine)), ("", nil),
                                ("Quit \(appName)", #selector(quit))] {
            guard let action = action else { menu.addItem(.separator()); continue }
            let entry = NSMenuItem(title: title, action: action, keyEquivalent: "")
            entry.target = self
            menu.addItem(entry)
        }
        bar.menu = menu
        item = bar
    }

    /// Yeufonic's mark, the fork and its dot from app/static/logo.svg, in one colour: macOS tints a
    /// template image to suit the menu bar.  A gap round the dot keeps it a dot at this size.
    func mark() -> NSImage {
        let image = NSImage(size: NSSize(width: 18, height: 18), flipped: true) { _ in
            let s: CGFloat = 18 / 54  // the logo's view box is 48 x 54, from (8, 5)
            func at(_ x: CGFloat, _ y: CGFloat) -> NSPoint { NSPoint(x: (x - 8) * s + 1, y: (y - 5) * s) }
            let fork = NSBezierPath()
            fork.move(to: at(32, 54)); fork.line(to: at(32, 36))
            fork.curve(to: at(14, 12), controlPoint1: at(32, 26), controlPoint2: at(19, 23))
            fork.move(to: at(32, 36))
            fork.curve(to: at(50, 12), controlPoint1: at(32, 26), controlPoint2: at(45, 23))
            fork.lineWidth = 8.5 * s
            fork.lineCapStyle = .round
            fork.lineJoinStyle = .round
            NSColor.black.set()
            fork.stroke()
            func dot(_ r: CGFloat) -> NSBezierPath {
                let c = at(50, 12)
                return NSBezierPath(ovalIn: NSRect(x: c.x - r * s, y: c.y - r * s, width: 2 * r * s, height: 2 * r * s))
            }
            NSGraphicsContext.current?.compositingOperation = .clear
            dot(7.4).fill()
            NSGraphicsContext.current?.compositingOperation = .sourceOver
            dot(5.6).fill()
            return true
        }
        image.isTemplate = true
        image.accessibilityDescription = appName
        return image
    }

    func startChild() {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/bash")
        process.arguments = [Bundle.main.resourceURL!.appendingPathComponent("start.sh").path]
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = FileHandle.nullDevice
        pipe.fileHandleForReading.readabilityHandler = { handle in
            let data = handle.availableData
            guard !data.isEmpty, let text = String(data: data, encoding: .utf8) else { return }
            DispatchQueue.main.async { self.heard(text) }
        }
        process.terminationHandler = { _ in DispatchQueue.main.async { self.childEnded() } }
        do {
            try process.run()
            child = process
        } catch {
            alert("\(appName) could not start.", "\(error.localizedDescription)")
            NSApp.terminate(nil)
        }
    }

    func heard(_ text: String) {
        let lines = (leftover + text).components(separatedBy: "\n")
        leftover = lines.last ?? ""
        for line in lines.dropLast() where line.hasPrefix("@@") {
            let parts = line.dropFirst(2).split(separator: " ", maxSplits: 1).map(String.init)
            let detail = parts.count > 1 ? parts[1] : ""
            switch parts.first ?? "" {
            case "url": url = detail; showIcon()
            case "fail": failure = detail
            case "engine-stopped":
                alert("The engine stopped.", "Songs cannot be made until it is running again. Restart it from the "
                      + "\(appName) menu in the menu bar; the engine log may say why.")
            default: break
            }
        }
    }

    func childEnded() {
        let status = child?.terminationStatus ?? 0
        if quitting { return }  // applicationShouldTerminate finishes the quit
        child = nil
        do {
            if !failure.isEmpty {
                alert(appName, failure)
            } else if status != 0 {
                alert("\(appName) stopped.", "The app log in \(logs.path) may say why.")
            }
            // Status 0 without a failure: setup was started instead, or Yeufonic was already
            // running and its page was opened; either way nothing is left for this one to do.
        }
        NSApp.terminate(nil)
    }

    @discardableResult
    func alert(_ text: String, _ detail: String, _ buttons: [String] = ["OK"]) -> Int {
        let box = NSAlert()
        box.messageText = text
        box.informativeText = detail
        for label in buttons { box.addButton(withTitle: label) }
        NSApp.activate(ignoringOtherApps: true)
        return box.runModal().rawValue - NSApplication.ModalResponse.alertFirstButtonReturn.rawValue
    }

    /// What quitting or a restart would stop, in a few words, or nothing: the launcher's busy().
    func busy() -> String {
        guard let address = URL(string: url + "/api/state") else { return "" }
        var request = URLRequest(url: address)
        request.timeoutInterval = 2
        var state: [String: Any] = [:]
        let done = DispatchSemaphore(value: 0)
        URLSession.shared.dataTask(with: request) { data, _, _ in
            if let data = data, let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                state = object
            }
            done.signal()
        }.resume()
        _ = done.wait(timeout: .now() + 3)
        func given(_ value: Any?) -> Bool {
            switch value {
            case nil, is NSNull: return false
            case let number as NSNumber: return number.boolValue
            case let text as String: return !text.isEmpty
            case let list as [Any]: return !list.isEmpty
            case let table as [String: Any]: return !table.isEmpty
            default: return true
            }
        }
        if given(state["training"]) { return "A LoRA is training. Quitting stops it." }
        if given(state["current"]) || given(state["queue"]) { return "A job is running. Quitting stops it." }
        return ""
    }

    @objc func openPage() {
        if let page = URL(string: url), !url.isEmpty { NSWorkspace.shared.open(page) }
    }

    @objc func showLogs() {
        NSWorkspace.shared.open(logs)
    }

    @objc func restartEngine() {
        let warning = busy()
        if !warning.isEmpty && alert("Restart the engine?", warning, ["Cancel", "Restart"]) != 1 { return }
        if let process = child, process.isRunning { kill(process.processIdentifier, SIGUSR1) }
    }

    @objc func quit() {
        // Asked only when it would stop a job or a training run, as on Windows.
        let warning = busy()
        if !warning.isEmpty && alert("Quit \(appName)?", warning, ["Cancel", "Quit"]) != 1 { return }
        NSApp.terminate(nil)
    }

    func applicationShouldHandleReopen(_ app: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        // Opening Yeufonic again while it runs: the page, as a second click does on Windows.
        openPage()
        return false
    }

    func applicationShouldTerminate(_ app: NSApplication) -> NSApplication.TerminateReply {
        // Logging out, shutting down and Quit all come here: the launcher stops the app and the
        // engine before this one goes.
        // Waited for here, not with .terminateLater: while a quit is pending the main thread
        // runs in a mode that never delivers a reply queued with DispatchQueue.main, so the
        // app stayed open with its launcher gone.  Stopping takes a second or two.
        guard let process = child, process.isRunning else { return .terminateNow }
        quitting = true
        process.terminate()
        let deadline = Date().addingTimeInterval(30)
        while process.isRunning && Date() < deadline { usleep(100_000) }
        if process.isRunning { kill(process.processIdentifier, SIGKILL) }
        return .terminateNow
    }
}

// A plain SIGTERM (kill, or launchd) quits as the menu does.
signal(SIGTERM, SIG_IGN)
let onTerm = DispatchSource.makeSignalSource(signal: SIGTERM, queue: .main)
onTerm.setEventHandler { NSApp.terminate(nil) }
onTerm.resume()

let app = NSApplication.shared
let menu = Menu()
app.delegate = menu
app.setActivationPolicy(.accessory)
app.run()
