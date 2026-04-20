import Cocoa

let API_URL = "http://localhost:5555/api/command"

func sendCommand(action: String, dry: Bool, completion: @escaping (String) -> Void) {
    guard let url = URL(string: API_URL) else {
        completion("Error: Invalid URL")
        return
    }
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.timeoutInterval = 60

    let body: [String: Any] = ["action": action, "dry": dry]
    request.httpBody = try? JSONSerialization.data(withJSONObject: body)

    URLSession.shared.dataTask(with: request) { data, _, error in
        if let error = error {
            DispatchQueue.main.async { completion("Error: \(error.localizedDescription)") }
            return
        }
        guard let data = data,
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            DispatchQueue.main.async { completion("Error: Invalid response") }
            return
        }
        let text = formatResult(json)
        DispatchQueue.main.async { completion(text) }
    }.resume()
}

func formatResult(_ data: [String: Any]) -> String {
    var parts: [String] = []
    if let msg = data["message"] as? String { parts.append(msg) }
    if let price = data["current_price"] as? Double {
        let strike = data["strike"] ?? "?"
        let exp = data["expiration"] ?? "?"
        parts.append("Price: $\(String(format: "%.2f", price))  Strike: $\(strike)  Exp: \(exp)")
    }
    if let success = data["success"] as? Bool {
        if success {
            parts.append("SUCCESS")
        } else if let err = data["error"] as? String {
            parts.append("FAILED: \(err)")
        }
    }
    if let results = data["results"] as? [[String: Any]] {
        for r in results {
            if let msg = r["message"] as? String { parts.append(msg) }
            if let s = r["success"] as? Bool {
                parts.append(s ? "  SUCCESS" : "  FAILED: \(r["error"] ?? "")")
            }
        }
    }
    if let err = data["error"] as? String, data["success"] == nil, data["results"] == nil {
        parts.append("Error: \(err)")
    }
    return parts.isEmpty ? "OK" : parts.joined(separator: "\n")
}

class AppDelegate: NSObject, NSApplicationDelegate {
    var statusItem: NSStatusItem!

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSLog("FidelityTrade: applicationDidFinishLaunching called")

        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)

        if let button = statusItem.button {
            button.title = "$ Trade"
            NSLog("FidelityTrade: status item button title set")
        } else {
            NSLog("FidelityTrade: ERROR - status item button is nil")
        }

        let menu = NSMenu()

        menu.addItem(makeItem("Buy Call (Dry)", tradeAction: "buy_call", dry: true))
        menu.addItem(makeItem("Buy Call (LIVE)", tradeAction: "buy_call", dry: false))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(makeItem("Buy Put (Dry)", tradeAction: "buy_put", dry: true))
        menu.addItem(makeItem("Buy Put (LIVE)", tradeAction: "buy_put", dry: false))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(makeItem("Sell Call (Dry)", tradeAction: "sell_call", dry: true))
        menu.addItem(makeItem("Sell Call (LIVE)", tradeAction: "sell_call", dry: false))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(makeItem("Sell Put (Dry)", tradeAction: "sell_put", dry: true))
        menu.addItem(makeItem("Sell Put (LIVE)", tradeAction: "sell_put", dry: false))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(makeItem("Status", tradeAction: "status", dry: true))
        menu.addItem(NSMenuItem.separator())

        let quit = NSMenuItem(title: "Quit", action: #selector(quitApp), keyEquivalent: "q")
        quit.target = self
        menu.addItem(quit)

        statusItem.menu = menu
        NSLog("FidelityTrade: menu assigned, app ready")
    }

    func makeItem(_ title: String, tradeAction: String, dry: Bool) -> NSMenuItem {
        let item = NSMenuItem(title: title, action: #selector(menuClicked(_:)), keyEquivalent: "")
        item.target = self
        item.representedObject = ["action": tradeAction, "dry": dry] as [String: Any]
        return item
    }

    @objc func quitApp() {
        NSApplication.shared.terminate(nil)
    }

    @objc func menuClicked(_ sender: NSMenuItem) {
        guard let info = sender.representedObject as? [String: Any],
              let action = info["action"] as? String,
              let dry = info["dry"] as? Bool else { return }

        if !dry {
            NSApplication.shared.activate(ignoringOtherApps: true)
            let alert = NSAlert()
            alert.messageText = "Execute \(action.replacingOccurrences(of: "_", with: " ").uppercased()) for REAL?"
            alert.informativeText = "This will place a LIVE trade on Fidelity."
            alert.alertStyle = .warning
            alert.addButton(withTitle: "Execute")
            alert.addButton(withTitle: "Cancel")
            if alert.runModal() != .alertFirstButtonReturn { return }
        }

        sendCommand(action: action, dry: dry) { result in
            let mode = dry ? "Dry" : "LIVE"
            let title = "\(action.replacingOccurrences(of: "_", with: " ").capitalized) (\(mode))"
            let body = result.prefix(256).replacingOccurrences(of: "\"", with: "\\\"")
            let script = "display notification \"\(body)\" with title \"\(title)\" sound name \"default\""
            let proc = Process()
            proc.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
            proc.arguments = ["-e", script]
            try? proc.run()
        }
    }
}

NSLog("FidelityTrade: starting app")
let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.accessory)
NSLog("FidelityTrade: calling app.run()")
app.run()
