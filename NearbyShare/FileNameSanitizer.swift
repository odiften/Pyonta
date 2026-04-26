//
//  FileNameSanitizer.swift
//  Pyonta
//
//  Defends against malicious peer-supplied file names: path traversal
//  (..), absolute paths (/x), NUL injection, control characters,
//  filesystem-reserved characters, and overlong names.
//
//  Reference: SafeBreach "RCE Attack Chain on Quick Share" — typical
//  vulnerability pattern in Quick Share / Nearby Share implementations.
//

import Foundation

enum FileNameSanitizer {
	/// Cap the resulting name well under the 255-byte HFS+/APFS limit.
	static let maxByteLength = 200
	/// Used when sanitization yields an empty or pure-dot result.
	static let fallbackName = "received_file"

	/// Sanitize a file name received from a remote peer for safe use as
	/// the last path component of a download destination.
	///
	/// - Strips ASCII control chars (0x00–0x1F, 0x7F) including NUL/CR/LF.
	/// - Replaces path separators and OS-reserved characters with `_`.
	/// - Trims trailing dots/spaces and leading dots (kills `..` and hidden-file forcing).
	/// - Caps total UTF-8 byte length while preserving extension.
	/// - Returns `fallbackName` (with optional extension) if input becomes empty.
	static func sanitize(_ name: String, fallbackExtension: String = "") -> String {
		let controlsRemoved = String(String.UnicodeScalarView(name.unicodeScalars.filter { scalar in
			scalar.value >= 0x20 && scalar.value != 0x7F
		}))

		let reservedChars: Set<Character> = ["/", "\\", ":", "?", "%", "*", "|", "\"", "<", ">", "="]
		var sanitized = String(controlsRemoved.map { reservedChars.contains($0) ? "_" : $0 })

		sanitized = sanitized.trimmingCharacters(in: .whitespaces)
		while let last = sanitized.last, last == "." || last == " " {
			sanitized.removeLast()
		}
		while let first = sanitized.first, first == "." {
			sanitized.removeFirst()
		}

		if sanitized.isEmpty {
			return fallbackExtension.isEmpty ? fallbackName : "\(fallbackName).\(fallbackExtension)"
		}

		if sanitized.utf8.count > maxByteLength {
			let nsName = sanitized as NSString
			let ext = nsName.pathExtension
			let stem = nsName.deletingPathExtension
			let extWithDot = ext.isEmpty ? "" : ".\(ext)"
			let stemBudget = max(0, maxByteLength - extWithDot.utf8.count)
			var truncatedStem = stem
			while truncatedStem.utf8.count > stemBudget && !truncatedStem.isEmpty {
				truncatedStem.removeLast()
			}
			sanitized = truncatedStem + extWithDot
			if sanitized.isEmpty {
				return fallbackExtension.isEmpty ? fallbackName : "\(fallbackName).\(fallbackExtension)"
			}
		}

		return sanitized
	}
}
