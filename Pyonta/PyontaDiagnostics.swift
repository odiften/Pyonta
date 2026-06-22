//
//  PyontaDiagnostics.swift
//  Pyonta
//

import Foundation
import NearbyShare

enum PyontaDiagnostics {
	enum Direction: String {
		case incoming = "android_to_mac"
		case outgoing = "mac_to_android"
	}

	enum ContentKind: String {
		case files
		case text
		case url
	}

	private static let lastTransferKey = "PyontaLastSanitizedTransferDiagnostic"
	private static let formatter = ISO8601DateFormatter()

	static func recordIncomingBlockedByPlus(transfer: TransferMetadata) {
		recordTransfer(
			direction: .incoming,
			kind: contentKind(for: transfer.kind),
			fileCount: transfer.files.count,
			autoAccepted: false,
			status: "blocked",
			errorCategory: "pyonta_plus_required",
			error: nil
		)
	}

	static func recordIncoming(transfer: TransferMetadata, autoAccepted: Bool, error: Error?) {
		recordTransfer(
			direction: .incoming,
			kind: contentKind(for: transfer.kind),
			fileCount: transfer.files.count,
			autoAccepted: autoAccepted,
			status: error == nil ? "success" : "failure",
			errorCategory: error.map(errorCategory(for:)) ?? "none",
			error: error
		)
	}

	static func recordOutgoing(kind: ContentKind, fileCount: Int, error: Error?) {
		recordTransfer(
			direction: .outgoing,
			kind: kind,
			fileCount: fileCount,
			autoAccepted: nil,
			status: error == nil ? "success" : "failure",
			errorCategory: error.map(errorCategory(for:)) ?? "none",
			error: error
		)
	}

	static func makeReport(defaults: UserDefaults = .standard, now: Date = Date()) -> String {
		let bundle = Bundle.main
		let appName = bundle.object(forInfoDictionaryKey: "CFBundleDisplayName") as? String
			?? bundle.object(forInfoDictionaryKey: "CFBundleName") as? String
			?? "Pyonta"
		let version = bundle.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "unknown"
		let build = bundle.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "unknown"
		let bundleID = bundle.bundleIdentifier ?? "unknown"
		let purchases = PyontaPurchases.shared

		var lines = [
			"Pyonta Diagnostics",
			"Generated: \(formatter.string(from: now))",
			"Privacy: This report excludes file contents, file names, shared text, URLs, device names, IP addresses, and purchase/customer identifiers.",
			"",
			"App",
			"- Name: \(appName)",
			"- Version: \(version)",
			"- Build: \(build)",
			"- Bundle ID: \(bundleID)",
			"",
			"System",
			"- macOS: \(ProcessInfo.processInfo.operatingSystemVersionString)",
			"",
			"Settings",
			"- Visible to everyone: \(boolString(defaults.bool(forKey: AppDelegate.visibilityKey)))",
			"- Receive without asking: \(boolString(defaults.bool(forKey: AppDelegate.autoAcceptKey)))",
			"- Open URLs automatically: \(boolString(defaults.bool(forKey: AppDelegate.openReceivedURLsKey)))",
			"- Launch at login: \(boolString(defaults.bool(forKey: AppDelegate.launchAtLoginKey)))",
			"",
			"Purchases",
			"- RevenueCat configured: \(boolString(purchases.isConfigured))",
			"- Pyonta+ active: \(boolString(purchases.isPlusActive))",
			"- Receiving unlocked: \(boolString(purchases.canReceiveIncomingTransfers))",
			"- Last purchase error: \(diagnosticErrorLine(for: purchases.lastError))",
			"",
			"Last transfer"
		]

		if let event = lastTransferEvent(defaults: defaults) {
			lines.append("- Recorded: \(event["recordedAt"] ?? "unknown")")
			lines.append("- Direction: \(event["direction"] ?? "unknown")")
			lines.append("- Status: \(event["status"] ?? "unknown")")
			lines.append("- Content kind: \(event["kind"] ?? "unknown")")
			lines.append("- File count: \(event["fileCountBucket"] ?? "unknown")")
			lines.append("- Auto accepted: \(event["autoAccepted"] ?? "not_applicable")")
			lines.append("- Error: \(event["errorCategory"] ?? "none")")
			if let domain = event["errorDomain"], domain != "none" {
				lines.append("- Error domain: \(domain)")
			}
			if let code = event["errorCode"], code != "none" {
				lines.append("- Error code: \(code)")
			}
		} else {
			lines.append("- none")
		}

		return lines.joined(separator: "\n")
	}

	private static func recordTransfer(
		direction: Direction,
		kind: ContentKind,
		fileCount: Int,
		autoAccepted: Bool?,
		status: String,
		errorCategory: String,
		error: Error?
	) {
		var event = [
			"recordedAt": formatter.string(from: Date()),
			"direction": direction.rawValue,
			"status": status,
			"kind": kind.rawValue,
			"fileCountBucket": fileCountBucket(fileCount, for: kind),
			"autoAccepted": autoAccepted.map(boolString) ?? "not_applicable",
			"errorCategory": errorCategory,
			"errorDomain": "none",
			"errorCode": "none",
		]
		if let error = error {
			let nsError = error as NSError
			event["errorDomain"] = nsError.domain
			event["errorCode"] = String(nsError.code)
		}
		UserDefaults.standard.set(event, forKey: lastTransferKey)
	}

	private static func lastTransferEvent(defaults: UserDefaults) -> [String: String]? {
		guard let raw = defaults.dictionary(forKey: lastTransferKey) else { return nil }
		return raw.reduce(into: [String: String]()) { result, item in
			if let value = item.value as? String {
				result[item.key] = value
			}
		}
	}

	private static func diagnosticErrorLine(for error: Error?) -> String {
		guard let error = error else { return "none" }
		let nsError = error as NSError
		return "\(errorCategory(for: error)) (\(nsError.domain) \(nsError.code))"
	}

	private static func contentKind(for kind: TransferMetadata.Kind) -> ContentKind {
		switch kind {
		case .files:
			return .files
		case .text:
			return .text
		case .url:
			return .url
		}
	}

	private static func fileCountBucket(_ count: Int, for kind: ContentKind) -> String {
		guard kind == .files else { return "not_applicable" }
		switch count {
		case 0:
			return "0"
		case 1:
			return "1"
		case 2...5:
			return "2-5"
		case 6...20:
			return "6-20"
		case 21...100:
			return "21-100"
		default:
			return "101+"
		}
	}

	private static func errorCategory(for error: Error) -> String {
		guard let nearbyError = error as? NearbyError else { return "other_error" }
		switch nearbyError {
		case .inputOutput:
			return "input_output"
		case .protocolError:
			return "protocol"
		case .requiredFieldMissing:
			return "protocol_required_field_missing"
		case .ukey2:
			return "encryption"
		case .canceled(reason: let reason):
			switch reason {
			case .timedOut:
				return "timed_out"
			case .userRejected:
				return "user_rejected"
			case .userCanceled:
				return "user_canceled"
			case .notEnoughSpace:
				return "not_enough_space"
			case .unsupportedType:
				return "unsupported_type"
			}
		}
	}

	private static func boolString(_ value: Bool) -> String {
		value ? "true" : "false"
	}
}
