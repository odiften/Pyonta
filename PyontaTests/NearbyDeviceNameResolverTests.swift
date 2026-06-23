import XCTest
@testable import NearbyShare

final class NearbyDeviceNameResolverTests: XCTestCase {
	func testPrettifiesModelHostname() {
		XCTAssertEqual(
			NearbyNetworkScannerHostLookup.displayName(fromHostname: "Pixel-8-Pro.local"),
			"Pixel 8 Pro"
		)
	}

	func testRejectsGenericAndroidRandomHostname() {
		XCTAssertNil(
			NearbyNetworkScannerHostLookup.displayName(fromHostname: "Android-6Gmegqux.local")
		)
	}

	func testRecentDeviceNameCacheReturnsOnlyUniqueRecentNameForType() {
		var cache=RecentDeviceNameCache(maxAge: 60)
		let now=Date()

		cache.remember(name: "Pixel 8 Pro", type: .phone, at: now)

		XCTAssertEqual(cache.uniqueRecentName(for: .phone, at: now.addingTimeInterval(10)), "Pixel 8 Pro")
		XCTAssertNil(cache.uniqueRecentName(for: .tablet, at: now.addingTimeInterval(10)))
	}

	func testRecentDeviceNameCacheAvoidsAmbiguousNames() {
		var cache=RecentDeviceNameCache(maxAge: 60)
		let now=Date()

		cache.remember(name: "Pixel 8 Pro", type: .phone, at: now)
		cache.remember(name: "Galaxy", type: .phone, at: now)

		XCTAssertNil(cache.uniqueRecentName(for: .phone, at: now.addingTimeInterval(10)))
	}

	func testRecentDeviceNameCacheExpiresOldNames() {
		var cache=RecentDeviceNameCache(maxAge: 60)
		let now=Date()

		cache.remember(name: "Pixel 8 Pro", type: .phone, at: now)

		XCTAssertNil(cache.uniqueRecentName(for: .phone, at: now.addingTimeInterval(61)))
	}
}
