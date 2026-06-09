//
//  PyontaPurchases.swift
//  Pyonta
//

import Cocoa
import RevenueCat
import os.log

fileprivate let pyontaPurchasesLog = OSLog(subsystem: "com.odiften.pyonta", category: "purchases")

enum PyontaPurchaseConfiguration {
	static let plusEntitlementID = "pyonta_plus"

	static var revenueCatAPIKey: String {
		let value = Bundle.main.object(forInfoDictionaryKey: "RevenueCatAPIKey") as? String ?? ""
		return value.trimmingCharacters(in: .whitespacesAndNewlines)
	}

	static var hasRevenueCatAPIKey: Bool {
		!revenueCatAPIKey.isEmpty && revenueCatAPIKey != "REVENUECAT_PUBLIC_API_KEY"
	}

	static var allowsReceivingWithoutRevenueCatConfiguration: Bool {
		#if DEBUG
		return true
		#else
		return false
		#endif
	}
}

final class PyontaPurchases {
	static let shared = PyontaPurchases()

	private(set) var isConfigured = false
	private(set) var isPlusActive = false
	private(set) var lastError: Error?
	private var purchaseAnchorWindow: NSWindow?

	var canReceiveIncomingTransfers: Bool {
		if isPlusActive { return true }
		return !isConfigured && PyontaPurchaseConfiguration.allowsReceivingWithoutRevenueCatConfiguration
	}

	private init() {}

	func configure() {
		guard !isConfigured else { return }
		guard PyontaPurchaseConfiguration.hasRevenueCatAPIKey else {
			os_log("RevenueCat API key is not configured", log: pyontaPurchasesLog, type: .info)
			return
		}

		#if DEBUG
		Purchases.logLevel = .debug
		#else
		Purchases.logLevel = .warn
		#endif

		Purchases.configure(withAPIKey: PyontaPurchaseConfiguration.revenueCatAPIKey)
		isConfigured = true
		refreshCustomerInfo()
	}

	func refreshCustomerInfo(completion: ((Bool) -> Void)? = nil) {
		guard isConfigured else {
			completion?(canReceiveIncomingTransfers)
			return
		}

		Purchases.shared.getCustomerInfo { customerInfo, error in
			OperationQueue.main.addOperation {
				let purchases = PyontaPurchases.shared
				if let error = error {
					purchases.lastError = error
					os_log("Failed to refresh RevenueCat customer info: %{private}@", log: pyontaPurchasesLog, type: .error, "\(error)")
				}
				if let customerInfo = customerInfo {
					purchases.update(customerInfo: customerInfo)
				}
				completion?(purchases.canReceiveIncomingTransfers)
			}
		}
	}

	func presentPurchaseOptions() {
		guard isConfigured else {
			showAlert(messageKey: "PlusUnavailable.Message", defaultMessage: "Pyonta+ is not configured yet. Add the RevenueCat public API key before releasing this build.")
			return
		}

		Purchases.shared.getOfferings { offerings, error in
			OperationQueue.main.addOperation {
				let purchases = PyontaPurchases.shared
				if let error = error {
					purchases.lastError = error
					os_log("Failed to fetch RevenueCat offerings: %{private}@", log: pyontaPurchasesLog, type: .error, "\(error)")
				}
				guard let packages = offerings?.current?.availablePackages, !packages.isEmpty else {
					purchases.showAlert(messageKey: "PlusNoOfferings.Message", defaultMessage: "No Pyonta+ products are available yet. Check the RevenueCat offering and App Store Connect product setup.")
					return
				}
				purchases.presentPackagePicker(packages: Array(packages.prefix(3)))
			}
		}
	}

	func restorePurchases() {
		guard isConfigured else {
			showAlert(messageKey: "PlusUnavailable.Message", defaultMessage: "Pyonta+ is not configured yet. Add the RevenueCat public API key before releasing this build.")
			return
		}

		Purchases.shared.restorePurchases { customerInfo, error in
			OperationQueue.main.addOperation {
				let purchases = PyontaPurchases.shared
				if let error = error {
					purchases.lastError = error
					os_log("Failed to restore RevenueCat purchases: %{private}@", log: pyontaPurchasesLog, type: .error, "\(error)")
					purchases.showAlert(messageKey: "PlusPurchaseFailed.Message", defaultMessage: "Purchase could not be completed. Please try again.")
					return
				}
				if let customerInfo = customerInfo {
					purchases.update(customerInfo: customerInfo)
				}
				if purchases.isPlusActive {
					purchases.showAlert(messageKey: "PlusRestoreSuccess.Message", defaultMessage: "Purchases restored. Pyonta+ is active.")
				} else {
					purchases.showAlert(messageKey: "PlusRestoreMissing.Message", defaultMessage: "No active Pyonta+ purchase was found for this Apple ID.")
				}
			}
		}
	}

	func showPlusRequiredAlert() {
		let alert = NSAlert()
		alert.messageText = NSLocalizedString("UpgradeToPlus.Title", value: "Upgrade to Pyonta+", comment: "")
		alert.informativeText = NSLocalizedString("PlusRequired.Message", value: "Receiving from Android requires Pyonta+. Upgrade, then ask the sender to try again.", comment: "")
		alert.addButton(withTitle: NSLocalizedString("UpgradeToPlus", value: "Upgrade to Pyonta+…", comment: ""))
		alert.addButton(withTitle: NSLocalizedString("Cancel", value: "Cancel", comment: ""))
		NSApp.activate(ignoringOtherApps: true)
		let result = alert.runModal()
		if result == .alertFirstButtonReturn {
			presentPurchaseOptions()
		}
	}

	private func presentPackagePicker(packages: [Package]) {
		let alert = NSAlert()
		alert.messageText = NSLocalizedString("UpgradeToPlus.Title", value: "Upgrade to Pyonta+", comment: "")
		alert.informativeText = NSLocalizedString("PlusRequired.Message", value: "Receiving from Android requires Pyonta+. Upgrade, then ask the sender to try again.", comment: "")
		for package in packages {
			alert.addButton(withTitle: Self.buttonTitle(for: package))
		}
		alert.addButton(withTitle: NSLocalizedString("Cancel", value: "Cancel", comment: ""))
		NSApp.activate(ignoringOtherApps: true)
		let result = alert.runModal()
		let index = result.rawValue - NSApplication.ModalResponse.alertFirstButtonReturn.rawValue
		guard packages.indices.contains(index) else { return }
		purchase(package: packages[index])
	}

	private func purchase(package: Package) {
		showPurchaseAnchorWindow()
		Purchases.shared.purchase(package: package) { _, customerInfo, error, userCancelled in
			OperationQueue.main.addOperation {
				let purchases = PyontaPurchases.shared
				purchases.closePurchaseAnchorWindow()
				if userCancelled { return }
				if let error = error {
					purchases.lastError = error
					os_log("RevenueCat purchase failed: %{private}@", log: pyontaPurchasesLog, type: .error, "\(error)")
					purchases.showAlert(messageKey: "PlusPurchaseFailed.Message", defaultMessage: "Purchase could not be completed. Please try again.")
					return
				}
				if let customerInfo = customerInfo {
					purchases.update(customerInfo: customerInfo)
				}
				if purchases.isPlusActive {
					purchases.showAlert(messageKey: "PlusPurchaseSuccess.Message", defaultMessage: "Pyonta+ is active. Receiving from Android is now unlocked.")
				}
			}
		}
	}

	private func showPurchaseAnchorWindow() {
		let window = purchaseAnchorWindow ?? makePurchaseAnchorWindow()
		purchaseAnchorWindow = window
		NSApp.activate(ignoringOtherApps: true)
		window.center()
		window.makeKeyAndOrderFront(nil)
		window.orderFrontRegardless()
	}

	private func closePurchaseAnchorWindow() {
		purchaseAnchorWindow?.close()
		purchaseAnchorWindow = nil
	}

	private func makePurchaseAnchorWindow() -> NSWindow {
		let window = NSWindow(
			contentRect: NSRect(x: 0, y: 0, width: 420, height: 148),
			styleMask: [.titled, .closable],
			backing: .buffered,
			defer: false
		)
		window.title = NSLocalizedString("UpgradeToPlus.Title", value: "Upgrade to Pyonta+", comment: "")
		window.isReleasedWhenClosed = false
		window.level = .floating
		window.collectionBehavior = [.moveToActiveSpace, .transient]

		let contentView = NSView(frame: NSRect(x: 0, y: 0, width: 420, height: 148))

		let label = NSTextField(labelWithString: NSLocalizedString("PlusRequired.Message", value: "Receiving from Android requires Pyonta+. Upgrade, then ask the sender to try again.", comment: ""))
		label.frame = NSRect(x: 24, y: 62, width: 372, height: 54)
		label.maximumNumberOfLines = 3
		label.lineBreakMode = .byWordWrapping
		label.font = NSFont.systemFont(ofSize: NSFont.systemFontSize)
		label.textColor = .labelColor
		label.autoresizingMask = [.width, .minYMargin]
		contentView.addSubview(label)

		let progress = NSProgressIndicator(frame: NSRect(x: 24, y: 28, width: 372, height: 16))
		progress.style = .bar
		progress.isIndeterminate = true
		progress.controlSize = .small
		progress.startAnimation(nil)
		progress.autoresizingMask = [.width, .minYMargin]
		contentView.addSubview(progress)

		window.contentView = contentView
		return window
	}

	private func update(customerInfo: CustomerInfo) {
		isPlusActive = customerInfo.entitlements[PyontaPurchaseConfiguration.plusEntitlementID]?.isActive == true
		lastError = nil
	}

	private func showAlert(messageKey: String, defaultMessage: String) {
		let alert = NSAlert()
		alert.messageText = "Pyonta"
		alert.informativeText = NSLocalizedString(messageKey, value: defaultMessage, comment: "")
		NSApp.activate(ignoringOtherApps: true)
		alert.runModal()
	}

	private static func buttonTitle(for package: Package) -> String {
		let product = package.storeProduct
		let title = product.localizedTitle.trimmingCharacters(in: .whitespacesAndNewlines)
		let price = product.localizedPriceString.trimmingCharacters(in: .whitespacesAndNewlines)
		if title.isEmpty { return price }
		if price.isEmpty { return title }
		return "\(title) - \(price)"
	}
}
