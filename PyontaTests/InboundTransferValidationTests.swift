import XCTest
@testable import NearbyShare

final class InboundTransferValidationTests: XCTestCase {
	func testValidIncomingFilesReturnDeclaredTotalSize() throws {
		let files=[
			Self.file(payloadID: 1, size: 1024),
			Self.file(payloadID: 2, size: 2048),
		]

		let total=try InboundNearbyConnection.validatedIncomingFileTotalSize(files, availableBytes: 200*1024*1024)

		XCTAssertEqual(total, 3072)
	}

	func testRejectsNegativeFileSize() {
		XCTAssertThrowsError(try InboundNearbyConnection.validatedIncomingFileTotalSize([Self.file(payloadID: 1, size: -1)], availableBytes: nil)) { error in
			guard case NearbyError.protocolError(let message)=error else {
				return XCTFail("Expected protocolError, got \(error)")
			}
			XCTAssertTrue(message.contains("negative"))
		}
	}

	func testRejectsDuplicatePayloadIDs() {
		let files=[
			Self.file(payloadID: 42, size: 10),
			Self.file(payloadID: 42, size: 20),
		]

		XCTAssertThrowsError(try InboundNearbyConnection.validatedIncomingFileTotalSize(files, availableBytes: nil)) { error in
			guard case NearbyError.protocolError(let message)=error else {
				return XCTFail("Expected protocolError, got \(error)")
			}
			XCTAssertTrue(message.contains("Duplicate"))
		}
	}

	func testRejectsMissingPayloadID() {
		var file=Self.file(payloadID: 1, size: 10)
		file.clearPayloadID()

		XCTAssertThrowsError(try InboundNearbyConnection.validatedIncomingFileTotalSize([file], availableBytes: nil)) { error in
			guard case NearbyError.requiredFieldMissing(let message)=error else {
				return XCTFail("Expected requiredFieldMissing, got \(error)")
			}
			XCTAssertTrue(message.contains("payloadID"))
		}
	}

	func testRejectsMissingSize() {
		var file=Self.file(payloadID: 1, size: 10)
		file.clearSize()

		XCTAssertThrowsError(try InboundNearbyConnection.validatedIncomingFileTotalSize([file], availableBytes: nil)) { error in
			guard case NearbyError.requiredFieldMissing(let message)=error else {
				return XCTFail("Expected requiredFieldMissing, got \(error)")
			}
			XCTAssertTrue(message.contains("size"))
		}
	}

	func testRejectsWhenDeclaredSizeWouldExhaustDisk() {
		let files=[Self.file(payloadID: 1, size: 950)]

		XCTAssertThrowsError(try InboundNearbyConnection.validatedIncomingFileTotalSize(files, availableBytes: 1000)) { error in
			guard case NearbyError.canceled(reason: .notEnoughSpace)=error else {
				return XCTFail("Expected notEnoughSpace, got \(error)")
			}
		}
	}

	func testRejectsTooManyFiles() {
		let files=(0...InboundNearbyConnection.maximumIncomingFileCount).map { Self.file(payloadID: Int64($0), size: 1) }

		XCTAssertThrowsError(try InboundNearbyConnection.validatedIncomingFileTotalSize(files, availableBytes: nil)) { error in
			guard case NearbyError.protocolError(let message)=error else {
				return XCTFail("Expected protocolError, got \(error)")
			}
			XCTAssertTrue(message.contains("Too many files"))
		}
	}

	private static func file(payloadID:Int64, size:Int64) -> Sharing_Nearby_FileMetadata {
		var file=Sharing_Nearby_FileMetadata()
		file.name="sample.txt"
		file.mimeType="text/plain"
		file.payloadID=payloadID
		file.size=size
		return file
	}
}
