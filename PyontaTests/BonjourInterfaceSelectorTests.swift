import XCTest
@testable import NearbyShare

final class BonjourInterfaceSelectorTests: XCTestCase {
	func testKeepsUsablePrimaryInterface() {
		let selected=BonjourInterfaceSelector.selectedInterfaceName(
			primaryName: "en7",
			interfaces: [
				iface("en0", "192.168.1.173", flags: usableFlags),
				iface("en7", "192.168.1.125", flags: usableFlags),
			]
		)

		XCTAssertEqual(selected, "en7")
	}

	func testSkipsPointToPointPrimaryAndFallsBackToLocalLan() {
		let selected=BonjourInterfaceSelector.selectedInterfaceName(
			primaryName: "ppp0",
			interfaces: [
				iface("ppp0", "192.168.20.150", flags: usableFlags | UInt32(IFF_POINTOPOINT)),
				iface("en7", "192.168.1.125", flags: usableFlags),
				iface("en0", "192.168.1.173", flags: usableFlags),
			]
		)

		XCTAssertEqual(selected, "en0")
	}

	func testRejectsTunnelLoopbackAndLinkLocalInterfaces() {
		let selected=BonjourInterfaceSelector.selectedInterfaceName(
			primaryName: "utun4",
			interfaces: [
				iface("lo0", "127.0.0.1", flags: usableFlags | UInt32(IFF_LOOPBACK)),
				iface("utun4", "100.111.151.46", flags: usableFlags | UInt32(IFF_POINTOPOINT)),
				iface("en0", "169.254.1.10", flags: usableFlags),
			]
		)

		XCTAssertNil(selected)
	}

	private func iface(_ name:String, _ address:String, flags:UInt32) -> BonjourIPv4Interface {
		BonjourIPv4Interface(name: name, address: address, flags: flags)
	}

	private var usableFlags:UInt32 {
		UInt32(IFF_UP) | UInt32(IFF_RUNNING) | UInt32(IFF_MULTICAST) | UInt32(IFF_BROADCAST)
	}
}
