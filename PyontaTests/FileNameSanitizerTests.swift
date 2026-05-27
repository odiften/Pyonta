import XCTest
@testable import NearbyShare

final class FileNameSanitizerTests: XCTestCase {
	func testPathTraversalAndAbsolutePathsAreNeutralized() {
		XCTAssertEqual(FileNameSanitizer.sanitize("../secret.txt"), "_secret.txt")
		XCTAssertEqual(FileNameSanitizer.sanitize("..\\secret.txt"), "_secret.txt")
		XCTAssertEqual(FileNameSanitizer.sanitize("/tmp/passwd"), "_tmp_passwd")
		XCTAssertEqual(FileNameSanitizer.sanitize("folder/sub/file.pdf"), "folder_sub_file.pdf")
	}

	func testReservedCharactersAndControlsCannotReachFilesystemName() {
		let sanitized=FileNameSanitizer.sanitize("bad:\u{0}name?\nfile<1>.txt")

		XCTAssertEqual(sanitized, "bad_name_file_1_.txt")
		XCTAssertFalse(sanitized.contains("\u{0}"))
		XCTAssertFalse(sanitized.contains("\n"))
		XCTAssertFalse(sanitized.contains(":"))
		XCTAssertFalse(sanitized.contains("?"))
		XCTAssertFalse(sanitized.contains("<"))
		XCTAssertFalse(sanitized.contains(">"))
	}

	func testDotsWhitespaceAndHiddenFileForcingFallBackSafely() {
		XCTAssertEqual(FileNameSanitizer.sanitize("  ...  "), FileNameSanitizer.fallbackName)
		XCTAssertEqual(FileNameSanitizer.sanitize(".."), FileNameSanitizer.fallbackName)
		XCTAssertEqual(FileNameSanitizer.sanitize(".env"), "env")
		XCTAssertEqual(FileNameSanitizer.sanitize("report.txt. "), "report.txt")
		XCTAssertEqual(FileNameSanitizer.sanitize("...", fallbackExtension: "jpg"), "\(FileNameSanitizer.fallbackName).jpg")
	}

	func testOverlongNamesAreCappedAndPreserveExtension() {
		let input=String(repeating: "a", count: 260)+".jpeg"
		let sanitized=FileNameSanitizer.sanitize(input)

		XCTAssertLessThanOrEqual(sanitized.utf8.count, FileNameSanitizer.maxByteLength)
		XCTAssertTrue(sanitized.hasSuffix(".jpeg"))
		XCTAssertFalse(sanitized.isEmpty)
	}

	func testOverlongUnicodeNamesRemainValidUTF8() {
		let input=String(repeating: "ぴょん", count: 80)+".png"
		let sanitized=FileNameSanitizer.sanitize(input)

		XCTAssertLessThanOrEqual(sanitized.utf8.count, FileNameSanitizer.maxByteLength)
		XCTAssertTrue(sanitized.hasSuffix(".png"))
		XCTAssertNotNil(String(data: Data(sanitized.utf8), encoding: .utf8))
	}

	func testSanitizedSamplesAreSafeLastPathComponents() {
		let samples=[
			"../a.txt",
			"/absolute/path",
			"bad:name?.txt",
			".hidden",
			"trailing. ",
			"line\nbreak.txt",
		]

		for sample in samples {
			let sanitized=FileNameSanitizer.sanitize(sample)
			XCTAssertEqual((sanitized as NSString).lastPathComponent, sanitized, sample)
			XCTAssertFalse(sanitized.hasPrefix("."), sample)
			XCTAssertFalse(sanitized.hasSuffix("."), sample)
			XCTAssertFalse(sanitized.hasSuffix(" "), sample)
			XCTAssertFalse(sanitized.contains(".."), sample)
		}
	}
}
