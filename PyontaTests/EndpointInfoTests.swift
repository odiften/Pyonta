import XCTest
@testable import NearbyShare

final class EndpointInfoTests: XCTestCase {
	func testHiddenQuickShareV3EndpointInfoAllowsSeventeenBytesWithoutName() {
		let data=Data([
			0x32,
			0x14, 0xc2, 0xfa, 0x2e, 0xec, 0xf2, 0xf0,
			0xbe, 0x5b, 0x19, 0xa0, 0x72, 0xc7, 0x05, 0x04, 0xf7,
		])

		let info=EndpointInfo(data: data)

		XCTAssertNotNil(info)
		XCTAssertNil(info?.name)
		XCTAssertEqual(info?.deviceType, .phone)
		XCTAssertNil(info?.qrCodeData)
	}

	func testNamedEndpointInfoDecodesUTF8DeviceName() {
		let name=Array("Pixel 8 Pro".utf8)
		let data=Data([0x02]+Self.randomBytes+[UInt8(name.count)]+name)

		let info=EndpointInfo(data: data)

		XCTAssertEqual(info?.name, "Pixel 8 Pro")
		XCTAssertEqual(info?.deviceType, .phone)
	}

	func testEndpointInfoRejectsTooShortPayload() {
		let data=Data(repeating: 0x00, count: 16)

		XCTAssertNil(EndpointInfo(data: data))
	}

	func testNamedEndpointInfoRejectsLengthBeyondAvailableBytes() {
		let data=Data([0x02]+Self.randomBytes+[5, 0x41, 0x42])

		XCTAssertNil(EndpointInfo(data: data))
	}

	func testNamedEndpointInfoRejectsInvalidUTF8Name() {
		let data=Data([0x02]+Self.randomBytes+[2, 0xff, 0xff])

		XCTAssertNil(EndpointInfo(data: data))
	}

	func testHiddenEndpointInfoExtractsQrCodeTlv() {
		let qrData=Data([0xde, 0xad, 0xbe, 0xef])
		let data=Data([0x32]+Self.randomBytes+[1, UInt8(qrData.count)]+Array(qrData))

		let info=EndpointInfo(data: data)

		XCTAssertEqual(info?.deviceType, .phone)
		XCTAssertEqual(info?.qrCodeData, qrData)
	}

	func testMalformedTlvDoesNotCrashOrReadPastEnd() {
		let data=Data([0x32]+Self.randomBytes+[1, 20, 0xde, 0xad])

		let info=EndpointInfo(data: data)

		XCTAssertNotNil(info)
		XCTAssertNil(info?.qrCodeData)
	}

	private static let randomBytes:[UInt8]=[
		0x14, 0xc2, 0xfa, 0x2e, 0xec, 0xf2, 0xf0, 0xbe,
		0x5b, 0x19, 0xa0, 0x72, 0xc7, 0x05, 0x04, 0xf7,
	]
}
