//
//  AppDelegate.swift
//  Pyonta
//
//  Created by Grishka on 08.04.2023.
//

import Cocoa
import SwiftUI
import UserNotifications
import NearbyShare
import os.log

fileprivate let pyontaAppLog = OSLog(subsystem: "com.odiften.pyonta", category: "app")

final class BoolToggleState: ObservableObject {
	@Published var isOn: Bool {
		didSet {
			UserDefaults.standard.set(isOn, forKey: key)
			onChange?(isOn)
		}
	}
	let key: String
	var onChange: ((Bool) -> Void)?

	init(key: String, defaultValue: Bool) {
		self.key = key
		if UserDefaults.standard.object(forKey: key) == nil {
			UserDefaults.standard.set(defaultValue, forKey: key)
		}
		self.isOn = UserDefaults.standard.bool(forKey: key)
	}

	func reload() {
		let v = UserDefaults.standard.bool(forKey: key)
		if isOn != v { isOn = v }
	}
}

struct ToggleMenuRow: View {
	@ObservedObject var state: BoolToggleState
	let label: String
	var body: some View {
		HStack(spacing: 8) {
			Text(label)
			Spacer(minLength: 8)
			CustomToggleSwitch(isOn: $state.isOn)
		}
		.padding(.horizontal, 14)
		.padding(.vertical, 4)
		.frame(maxWidth: .infinity)
	}
}

struct CustomToggleSwitch: View {
	@Binding var isOn: Bool
	private let trackWidth: CGFloat = 36
	private let trackHeight: CGFloat = 20
	private let knobSize: CGFloat = 16
	var body: some View {
		ZStack(alignment: isOn ? .trailing : .leading) {
			Capsule()
				.fill(isOn ? Color(NSColor.controlAccentColor) : Color(NSColor.tertiaryLabelColor))
				.frame(width: trackWidth, height: trackHeight)
			Circle()
				.fill(Color.white)
				.frame(width: knobSize, height: knobSize)
				.padding(2)
				.shadow(color: Color.black.opacity(0.18), radius: 1, x: 0, y: 0.5)
		}
		.frame(width: trackWidth, height: trackHeight)
		.contentShape(Capsule())
		.onTapGesture {
			withAnimation(.easeInOut(duration: 0.15)) {
				isOn.toggle()
			}
		}
	}
}

@main
class AppDelegate: NSObject, NSApplicationDelegate, UNUserNotificationCenterDelegate, NSMenuDelegate, MainAppDelegate{
	static let autoAcceptKey="automaticallyAcceptFiles"
	static let visibilityKey="visibleToEveryone"
	static let launchAtLoginKey="launchAtLogin"
	private var statusItem:NSStatusItem?
	private var activeIncomingTransfers:[String:TransferInfo]=[:]
	private var sendWindowController:SendWindowController?
	private let autoAcceptToggleState = BoolToggleState(key: AppDelegate.autoAcceptKey, defaultValue: false)
	private let visibilityToggleState = BoolToggleState(key: AppDelegate.visibilityKey, defaultValue: true)
	// macOS 12 以前ではメニューに表示しないが、状態自体は保持しておく（13 にアップ時にそのまま使える）
	private let launchAtLoginToggleState = BoolToggleState(key: AppDelegate.launchAtLoginKey, defaultValue: false)

    func applicationDidFinishLaunching(_ aNotification: Notification) {
		PyontaPurchases.shared.configure()

		visibilityToggleState.onChange = { isOn in
			if isOn {
				NearbyConnectionManager.shared.becomeVisible()
			} else {
				NearbyConnectionManager.shared.becomeInvisible()
			}
		}

		// SMAppService の状態を真として、UserDefaults に同期してから onChange を繋ぐ。
		// 順序が大事: isOn 代入 -> didSet -> onChange?(isOn)。onChange はまだ nil なので無害。
		if #available(macOS 13.0, *) {
			let actual = LaunchAtLogin.isEnabled
			if launchAtLoginToggleState.isOn != actual {
				launchAtLoginToggleState.isOn = actual
			}
			launchAtLoginToggleState.onChange = { isOn in
				LaunchAtLogin.setEnabled(isOn)
			}
		}

		let menu=NSMenu()
		menu.delegate=self
		let visibilityItem=NSMenuItem()
		visibilityItem.view=makeVisibilityItemView()
		menu.addItem(visibilityItem)
		menu.addItem(withTitle: String(format: NSLocalizedString("DeviceName", value: "Device name: %@", comment: ""), arguments: [Host.current().localizedName!]), action: nil, keyEquivalent: "")
		let autoAcceptItem=NSMenuItem()
		autoAcceptItem.view=makeAutoAcceptItemView()
		menu.addItem(autoAcceptItem)
		if #available(macOS 13.0, *) {
			let launchItem=NSMenuItem()
			launchItem.view=makeLaunchAtLoginItemView()
			menu.addItem(launchItem)
		}
		menu.addItem(NSMenuItem.separator())
		let sendItem=NSMenuItem(title: NSLocalizedString("SendFiles", value: "Send files…", comment: ""), action: #selector(sendFiles(_:)), keyEquivalent: "")
		sendItem.target=self
		menu.addItem(sendItem)
		let sendClipboardItem=NSMenuItem(title: NSLocalizedString("SendClipboard", value: "Send clipboard…", comment: ""), action: #selector(sendClipboard(_:)), keyEquivalent: "")
		sendClipboardItem.target=self
		menu.addItem(sendClipboardItem)
		menu.addItem(NSMenuItem.separator())
		let upgradeItem=NSMenuItem(title: NSLocalizedString("UpgradeToPlus", value: "Upgrade to Pyonta+…", comment: ""), action: #selector(upgradeToPlus(_:)), keyEquivalent: "")
		upgradeItem.target=self
		menu.addItem(upgradeItem)
		let restorePurchasesItem=NSMenuItem(title: NSLocalizedString("RestorePurchases", value: "Restore purchases…", comment: ""), action: #selector(restorePurchases(_:)), keyEquivalent: "")
		restorePurchasesItem.target=self
		menu.addItem(restorePurchasesItem)
		menu.addItem(NSMenuItem.separator())
		let odiftenItem=NSMenuItem(title: NSLocalizedString("OdiftenContact", value: "Made by odiften / App development inquiries…", comment: ""), action: #selector(openOdiftenContact(_:)), keyEquivalent: "")
		odiftenItem.target=self
		odiftenItem.toolTip=NSLocalizedString("OdiftenContact.Tooltip", value: "Open a contact email to odiften.", comment: "")
		menu.addItem(odiftenItem)
		menu.addItem(NSMenuItem.separator())
		menu.addItem(withTitle: NSLocalizedString("Quit", value: "Quit Pyonta", comment: ""), action: #selector(NSApplication.terminate(_:)), keyEquivalent: "")
		statusItem=NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
		statusItem?.button?.image=NSImage(named: "MenuBarIcon")
		statusItem?.menu=menu
		statusItem?.behavior = .removalAllowed

		let nc=UNUserNotificationCenter.current()
		nc.requestAuthorization(options: [.alert, .sound]) { granted, err in
			if let err=err {
				os_log("Notification authorization failed: %{public}@", log: pyontaAppLog, type: .error, "\(err)")
			}
			os_log("Notification authorization result: granted=%{public}@", log: pyontaAppLog, type: .info, granted ? "yes" : "no")
			if !granted{
				os_log("Notifications are unavailable; incoming transfers will use the in-app fallback prompt", log: pyontaAppLog, type: .info)
			}
		}
		nc.delegate=self
		let incomingTransfersCategory=UNNotificationCategory(identifier: "INCOMING_TRANSFERS", actions: [
			UNNotificationAction(identifier: "ACCEPT", title: NSLocalizedString("Accept", comment: ""), options: UNNotificationActionOptions.authenticationRequired),
			UNNotificationAction(identifier: "DECLINE", title: NSLocalizedString("Decline", comment: ""))
		], intentIdentifiers: [])
		let errorsCategory=UNNotificationCategory(identifier: "ERRORS", actions: [], intentIdentifiers: [])
		nc.setNotificationCategories([incomingTransfersCategory, errorsCategory])
		NearbyConnectionManager.shared.mainAppDelegate=self
		if visibilityToggleState.isOn {
			NearbyConnectionManager.shared.becomeVisible()
		}
	}

	func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
		statusItem?.isVisible=true
		return true
	}

    func applicationWillTerminate(_ aNotification: Notification) {
		NearbyConnectionManager.shared.becomeInvisible()
		UNUserNotificationCenter.current().removeAllDeliveredNotifications()
    }

    func applicationSupportsSecureRestorableState(_ app: NSApplication) -> Bool {
        return true
    }

	func showNotificationsDeniedAlert(){
		let alert=NSAlert()
		alert.alertStyle = .critical
		alert.messageText=NSLocalizedString("NotificationsDenied.Title", value: "Notification Permission Required", comment: "")
		alert.informativeText=NSLocalizedString("NotificationsDenied.Message", value: "Pyonta needs to be able to display notifications for incoming file transfers. Please allow notifications in System Settings.", comment: "")
		alert.addButton(withTitle: NSLocalizedString("NotificationsDenied.OpenSettings", value: "Open settings", comment: ""))
		alert.addButton(withTitle: NSLocalizedString("Quit", value: "Quit Pyonta", comment: ""))
		let result=alert.runModal()
		if result==NSApplication.ModalResponse.alertFirstButtonReturn{
			NSWorkspace.shared.open(URL(string: "x-apple.systempreferences:com.apple.preference.notifications")!)
		}else if result==NSApplication.ModalResponse.alertSecondButtonReturn{
			NSApplication.shared.terminate(nil)
		}
	}

	func userNotificationCenter(_ center: UNUserNotificationCenter, didReceive response: UNNotificationResponse, withCompletionHandler completionHandler: @escaping () -> Void) {
		let transferID=response.notification.request.content.userInfo["transferID"]! as! String
		NearbyConnectionManager.shared.submitUserConsent(transferID: transferID, accept: response.actionIdentifier=="ACCEPT")
		if response.actionIdentifier != "ACCEPT"{
			activeIncomingTransfers.removeValue(forKey: transferID)
		}
		completionHandler()
	}

	func userNotificationCenter(_ center: UNUserNotificationCenter, willPresent notification: UNNotification, withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
		if #available(macOS 11.0, *) {
			completionHandler([.banner, .sound])
		}else{
			completionHandler([.alert, .sound])
		}
	}

	func obtainUserConsent(for transfer: TransferMetadata, from device: RemoteDeviceInfo) {
		guard PyontaPurchases.shared.canReceiveIncomingTransfers else {
			NearbyConnectionManager.shared.submitUserConsent(transferID: transfer.id, accept: false)
			DispatchQueue.main.async {
				PyontaPurchases.shared.showPlusRequiredAlert()
			}
			return
		}

		let autoAccept=UserDefaults.standard.bool(forKey: AppDelegate.autoAcceptKey)
		self.activeIncomingTransfers[transfer.id]=TransferInfo(device: device, transfer: transfer, autoAccepted: autoAccept)
		if autoAccept {
			NearbyConnectionManager.shared.submitUserConsent(transferID: transfer.id, accept: true)
			return
		}
		let fileStr:String
		if let textTitle=transfer.textDescription{
			fileStr=textTitle
		}else if transfer.files.count==1{
			fileStr=transfer.files[0].name
		}else{
			fileStr=String.localizedStringWithFormat(NSLocalizedString("NFiles", value: "%d files", comment: ""), transfer.files.count)
		}
		let notificationContent=UNMutableNotificationContent()
		notificationContent.title="Pyonta"
		notificationContent.subtitle=String(format:NSLocalizedString("PinCode", value: "PIN: %@", comment: ""), arguments: [transfer.pinCode!])
		notificationContent.body=String(format: NSLocalizedString("DeviceSendingFiles", value: "%1$@ is sending you %2$@", comment: ""), arguments: [device.name, fileStr])
		notificationContent.sound = .default
		notificationContent.categoryIdentifier="INCOMING_TRANSFERS"
		notificationContent.userInfo=["transferID": transfer.id]
		if #available(macOS 11.0, *){
			NDNotificationCenterHackery.removeDefaultAction(notificationContent)
		}
		let notificationReq=UNNotificationRequest(identifier: "transfer_"+transfer.id, content: notificationContent, trigger: nil)
		let notificationCenter=UNUserNotificationCenter.current()
		notificationCenter.getNotificationSettings { settings in
			let isAuthorized=settings.authorizationStatus == .authorized || settings.authorizationStatus == .provisional
			let canShowAlert=isAuthorized && settings.alertSetting == .enabled
			guard canShowAlert else {
				os_log("Notification unavailable for incoming transfer: auth=%ld alert=%ld", log: pyontaAppLog, type: .info, settings.authorizationStatus.rawValue, settings.alertSetting.rawValue)
				DispatchQueue.main.async {
					self.showIncomingTransferFallbackAlert(transfer: transfer, from: device, fileStr: fileStr)
				}
				return
			}
			notificationCenter.add(notificationReq) { error in
				if let error=error {
					os_log("Failed to add incoming transfer notification: %{public}@", log: pyontaAppLog, type: .error, "\(error)")
					DispatchQueue.main.async {
						self.showIncomingTransferFallbackAlert(transfer: transfer, from: device, fileStr: fileStr)
					}
				}
			}
		}
	}

	private func showIncomingTransferFallbackAlert(transfer: TransferMetadata, from device: RemoteDeviceInfo, fileStr: String){
		guard activeIncomingTransfers[transfer.id] != nil else { return }
		NSApp.activate(ignoringOtherApps: true)
		let alert=NSAlert()
		alert.messageText=String(format: NSLocalizedString("DeviceSendingFiles", value: "%1$@ is sending you %2$@", comment: ""), arguments: [device.name, fileStr])
		alert.informativeText=String(format:NSLocalizedString("PinCode", value: "PIN: %@", comment: ""), arguments: [transfer.pinCode ?? "----"])
		alert.addButton(withTitle: NSLocalizedString("Accept", comment: ""))
		alert.addButton(withTitle: NSLocalizedString("Decline", comment: ""))
		let result=alert.runModal()
		let accepted=result == NSApplication.ModalResponse.alertFirstButtonReturn
		NearbyConnectionManager.shared.submitUserConsent(transferID: transfer.id, accept: accepted)
		if !accepted{
			activeIncomingTransfers.removeValue(forKey: transfer.id)
		}
	}

	func menuWillOpen(_ menu: NSMenu) {
		autoAcceptToggleState.reload()
		visibilityToggleState.reload()
		// Launch at login は SMAppService が真の値を持つので OS から取り直す。
		// ユーザーがシステム設定→ログイン項目から直接 OFF にしたケースに追従するため。
		if #available(macOS 13.0, *) {
			let actual = LaunchAtLogin.isEnabled
			if launchAtLoginToggleState.isOn != actual {
				launchAtLoginToggleState.isOn = actual
			}
		}
	}

	private func makeAutoAcceptItemView() -> NSView {
		return makeToggleItemView(
			state: autoAcceptToggleState,
			label: NSLocalizedString("AutoAcceptFiles", value: "Auto-accept files", comment: ""),
			tooltip: NSLocalizedString("AutoAcceptFiles.Tooltip", value: "When on, anyone on your network who selects this Mac in Quick Share can send files without confirmation.", comment: "")
		)
	}

	private func makeVisibilityItemView() -> NSView {
		return makeToggleItemView(
			state: visibilityToggleState,
			label: NSLocalizedString("VisibleToEveryone", value: "Visible to everyone", comment: ""),
			tooltip: NSLocalizedString("VisibleToEveryone.Tooltip", value: "When off, your Mac is hidden from Quick Share. Sending to other devices still works.", comment: "")
		)
	}

	private func makeLaunchAtLoginItemView() -> NSView {
		return makeToggleItemView(
			state: launchAtLoginToggleState,
			label: NSLocalizedString("LaunchAtLogin", value: "Launch at login", comment: ""),
			tooltip: NSLocalizedString("LaunchAtLogin.Tooltip", value: "When on, Pyonta starts automatically when you log in to your Mac.", comment: "")
		)
	}

	private func makeToggleItemView(state: BoolToggleState, label: String, tooltip: String) -> NSView {
		let row = ToggleMenuRow(state: state, label: label)
		let host = NSHostingView(rootView: row)
		host.frame = NSRect(x: 0, y: 0, width: 280, height: 28)
		host.autoresizingMask = [.width]
		host.toolTip = tooltip
		return host
	}

	@objc func upgradeToPlus(_ sender: Any?) {
		PyontaPurchases.shared.presentPurchaseOptions()
	}

	@objc func restorePurchases(_ sender: Any?) {
		PyontaPurchases.shared.restorePurchases()
	}

	@objc func openOdiftenContact(_ sender: Any?) {
		let subject="Pyonta app inquiry".addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "Pyonta%20app%20inquiry"
		if let url=URL(string: "mailto:info@odiften.com?subject=\(subject)") {
			NSWorkspace.shared.open(url)
		}
	}

	@objc func sendFiles(_ sender: Any?) {
		let panel=NSOpenPanel()
		panel.allowsMultipleSelection=true
		panel.canChooseFiles=true
		panel.canChooseDirectories=false
		panel.title=NSLocalizedString("ChooseFiles.Title", value: "Choose files to send", comment: "")
		NSApp.activate(ignoringOtherApps: true)
		panel.begin { [weak self] response in
			guard response == .OK, !panel.urls.isEmpty else { return }
			self?.presentSendWindow(SendWindowController(urls: panel.urls))
		}
	}

	@objc func sendClipboard(_ sender: Any?) {
		let pb=NSPasteboard.general
		guard let raw=pb.string(forType: .string) else {
			showClipboardEmptyAlert()
			return
		}
		let text=raw.trimmingCharacters(in: .whitespacesAndNewlines)
		guard !text.isEmpty else {
			showClipboardEmptyAlert()
			return
		}
		let isURL=AppDelegate.isLikelyURL(text)
		presentSendWindow(SendWindowController(text: text, isURL: isURL))
	}

	private func presentSendWindow(_ controller:SendWindowController){
		self.sendWindowController=controller
		NotificationCenter.default.addObserver(forName: NSWindow.willCloseNotification, object: controller.window, queue: .main) { [weak self] _ in
			self?.sendWindowController=nil
		}
		controller.showWindow(nil)
	}

	private func showClipboardEmptyAlert(){
		let alert=NSAlert()
		alert.messageText=NSLocalizedString("ClipboardEmpty.Title", value: "Clipboard is empty", comment: "")
		alert.informativeText=NSLocalizedString("ClipboardEmpty.Body", value: "Copy some text first, then try again.", comment: "")
		alert.runModal()
	}

	private static func isLikelyURL(_ text:String) -> Bool {
		guard !text.contains(" "), !text.contains("\n"), !text.contains("\t") else { return false }
		guard let url=URL(string: text), let scheme=url.scheme?.lowercased() else { return false }
		return scheme=="http" || scheme=="https"
	}

	func incomingTransfer(id: String, didFinishWith error: Error?) {
		guard let transfer=self.activeIncomingTransfers[id] else {return}
		if let error=error{
			let notificationContent=UNMutableNotificationContent()
			notificationContent.title=String(format: NSLocalizedString("TransferError", value: "Failed to receive files from %@", comment: ""), arguments: [transfer.device.name])
			if let ne=(error as? NearbyError){
				switch ne{
				case .inputOutput:
					notificationContent.body="I/O Error";
				case .protocolError(_):
					notificationContent.body=NSLocalizedString("Error.Protocol", value: "Communication error", comment: "")
				case .requiredFieldMissing:
					notificationContent.body=NSLocalizedString("Error.Protocol", value: "Communication error", comment: "")
				case .ukey2:
					notificationContent.body=NSLocalizedString("Error.Crypto", value: "Encryption error", comment: "")
				case .canceled(reason: let reason):
					switch reason {
					case .timedOut:
						notificationContent.body=NSLocalizedString("TransferTimedOut", value: "Timed out", comment: "")
					case .userRejected:
						notificationContent.body=NSLocalizedString("TransferDeclined", value: "Declined", comment: "")
					case .userCanceled:
						notificationContent.body=NSLocalizedString("TransferCanceled", value: "Canceled", comment: "")
					case .notEnoughSpace:
						notificationContent.body=NSLocalizedString("NotEnoughSpace", value: "Not enough disk space", comment: "")
					case .unsupportedType:
						notificationContent.body=NSLocalizedString("UnsupportedType", value: "Attachment type not supported", comment: "")
					}
				}
			}else{
				notificationContent.body=error.localizedDescription
			}
			notificationContent.categoryIdentifier="ERRORS"
			UNUserNotificationCenter.current().add(UNNotificationRequest(identifier: "transferError_"+id, content: notificationContent, trigger: nil))
		}else if transfer.autoAccepted{
			let notificationContent=UNMutableNotificationContent()
			notificationContent.title="Pyonta"
			switch transfer.transfer.kind{
			case .text:
				notificationContent.body=String(format: NSLocalizedString("ReceivedTextToClipboard", value: "Text from %@ copied to clipboard", comment: ""), arguments: [transfer.device.name])
			case .url:
				notificationContent.body=String(format: NSLocalizedString("ReceivedURLOpened", value: "URL from %@ opened in browser", comment: ""), arguments: [transfer.device.name])
			case .files:
				let fileStr:String
				if transfer.transfer.files.count==1{
					fileStr=transfer.transfer.files[0].name
				}else{
					fileStr=String.localizedStringWithFormat(NSLocalizedString("NFiles", value: "%d files", comment: ""), transfer.transfer.files.count)
				}
				notificationContent.body=String(format: NSLocalizedString("ReceivedFiles", value: "Received %1$@ from %2$@", comment: ""), arguments: [fileStr, transfer.device.name])
			}
			notificationContent.sound = .default
			UNUserNotificationCenter.current().add(UNNotificationRequest(identifier: "received_"+id, content: notificationContent, trigger: nil))
		}
		UNUserNotificationCenter.current().removeDeliveredNotifications(withIdentifiers: ["transfer_"+id])
		self.activeIncomingTransfers.removeValue(forKey: id)
	}
}

struct TransferInfo{
	let device:RemoteDeviceInfo
	let transfer:TransferMetadata
	let autoAccepted:Bool
}

// MARK: - SendWindowController
//
// SendViewController.xib (ShareExtension の ShareViewController.xib をコピー)
// を NSWindow に embed する単純なラッパー。実際の UI ロジックは SendViewController に集約。

class SendWindowController: NSWindowController {

	private let viewController:SendViewController

	convenience init(urls:[URL]){
		self.init(viewController: SendViewController(urls: urls))
	}

	convenience init(text:String, isURL:Bool){
		self.init(viewController: SendViewController(text: text, isURL: isURL))
	}

	private init(viewController:SendViewController){
		self.viewController=viewController
		let window=NSWindow(contentViewController: viewController)
		window.styleMask = [.titled, .closable]
		window.title=NSLocalizedString("SendFiles.Title", value: "Send to Android", comment: "")
		window.isReleasedWhenClosed=false
		super.init(window: window)
	}

	required init?(coder:NSCoder){
		fatalError("init(coder:) has not been implemented")
	}

	override func showWindow(_ sender: Any?) {
		super.showWindow(sender)
		window?.center()
		NSApp.activate(ignoringOtherApps: true)
	}
}
