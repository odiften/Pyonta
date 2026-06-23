//
//  NearbyConnectionManager.swift
//  Pyonta
//
//  Created by Grishka on 08.04.2023.
//

import Foundation
import Network
import System
import CryptoKit
import SwiftECC
import os.log
import dnssd
import SystemConfiguration
import Darwin

fileprivate let pyontaLog = OSLog(subsystem: "com.odiften.pyonta", category: "discovery")

public struct RemoteDeviceInfo{
	public let name:String
	public let type:DeviceType
	public let qrCodeData:Data?
	public var id:String?
	
	init(name: String, type: DeviceType, id: String? = nil, qrCodeData: Data? = nil) {
		self.name = name
		self.type = type
		self.id = id
		self.qrCodeData = qrCodeData
	}
	
	init(info:EndpointInfo, id: String? = nil){
		self.name=info.name ?? NSLocalizedString("UnknownAndroidDevice", value: "Android device", comment: "Fallback name when an Android peer advertises without a device name (Visibility=Hidden)")
		self.type=info.deviceType
		self.qrCodeData=info.qrCodeData
		self.id=id
	}

	func renamed(_ name:String) -> RemoteDeviceInfo {
		RemoteDeviceInfo(name: name, type: type, id: id, qrCodeData: qrCodeData)
	}
	
	public enum DeviceType:Int32{
		case unknown=0
		case phone
		case tablet
		case computer
		
		public static func fromRawValue(value:Int) -> DeviceType{
			switch value {
			case 0:
				return .unknown
			case 1:
				return .phone
			case 2:
				return .tablet
			case 3:
				return .computer
			default:
				return .unknown
			}
		}
	}
}


public enum NearbyError:Error{
	case protocolError(_ message:String)
	case requiredFieldMissing(_ message:String)
	case ukey2
	case inputOutput
	case canceled(reason:CancellationReason)
	
	public enum CancellationReason{
		case userRejected, userCanceled, notEnoughSpace, unsupportedType, timedOut
	}
}

public struct TransferMetadata{
	public enum Kind{
		case files, text, url
	}
	public let files:[FileMetadata]
	public let id:String
	public let pinCode:String?
	public let textDescription:String?
	public let kind:Kind

	init(files: [FileMetadata], id: String, pinCode: String?, textDescription: String?=nil, kind: Kind = .files){
		self.files = files
		self.id = id
		self.pinCode = pinCode
		self.textDescription = textDescription
		self.kind = kind
	}
}

public struct FileMetadata{
	public let name:String
	public let size:Int64
	public let mimeType:String
}

struct FoundServiceInfo{
	let service:NWBrowser.Result
	var device:RemoteDeviceInfo?
}

struct OutgoingTransferInfo{
	let service:NWBrowser.Result
	let device:RemoteDeviceInfo
	let connection:OutboundNearbyConnection
	let delegate:ShareExtensionDelegate
}

struct RecentDeviceNameCache {
	private struct Entry {
		let name:String
		let type:RemoteDeviceInfo.DeviceType
		let learnedAt:Date
	}

	private var entries:[String:Entry]=[:]
	private let maxAge:TimeInterval

	init(maxAge:TimeInterval = 10*60) {
		self.maxAge=maxAge
	}

	mutating func remember(name:String, type:RemoteDeviceInfo.DeviceType, at date:Date = Date()) {
		let cleaned=name.trimmingCharacters(in: .whitespacesAndNewlines)
		guard !cleaned.isEmpty else { return }
		entries[cleaned.lowercased()]=Entry(name: cleaned, type: type, learnedAt: date)
	}

	mutating func uniqueRecentName(for type:RemoteDeviceInfo.DeviceType, at date:Date = Date()) -> String? {
		entries=entries.filter { _, entry in
			date.timeIntervalSince(entry.learnedAt) <= maxAge
		}
		let matching=entries.values.filter { $0.type == type }
		let names=Set(matching.map(\.name))
		guard names.count==1 else { return nil }
		return matching.first?.name
	}
}

private struct NetworkPathSignature: Equatable {
	let isSatisfied:Bool
	let status:String
	let usesWiFi:Bool
	let usesWiredEthernet:Bool
	let interfaces:[String]

	init(path:NWPath) {
		isSatisfied=path.status == .satisfied
		status="\(path.status)"
		usesWiFi=path.usesInterfaceType(.wifi)
		usesWiredEthernet=path.usesInterfaceType(.wiredEthernet)
		interfaces=path.availableInterfaces.map { $0.name }.sorted()
	}
}

struct BonjourIPv4Interface: Equatable {
	let name:String
	let address:String
	let flags:UInt32

	var isUsableForLocalBonjour:Bool {
		guard hasFlag(IFF_UP), hasFlag(IFF_RUNNING), hasFlag(IFF_MULTICAST) else { return false }
		guard !hasFlag(IFF_LOOPBACK), !hasFlag(IFF_POINTOPOINT) else { return false }
		guard address != "0.0.0.0", !address.hasPrefix("127."), !address.hasPrefix("169.254.") else { return false }
		let excludedPrefixes=["awdl", "llw", "utun", "ppp", "bridge", "gif", "stf"]
		return !excludedPrefixes.contains { name.hasPrefix($0) }
	}

	var preferenceScore:Int {
		if name=="en0" { return 1000 }
		if name.hasPrefix("en") { return 900 }
		return 100
	}

	private func hasFlag(_ flag:Int32) -> Bool {
		(flags & UInt32(flag)) != 0
	}
}

enum BonjourInterfaceSelector {
	static func selectedInterfaceName(primaryName:String?, interfaces:[BonjourIPv4Interface]) -> String? {
		let usable=interfaces.filter(\.isUsableForLocalBonjour)
		if let primaryName=primaryName, usable.contains(where: { $0.name==primaryName }) {
			return primaryName
		}
		return usable.sorted {
			if $0.preferenceScore != $1.preferenceScore {
				return $0.preferenceScore > $1.preferenceScore
			}
			return $0.name < $1.name
		}.first?.name
	}
}

private final class BonjourServicePublisher {
	private let log:OSLog
	private var serviceRef:DNSServiceRef?
	private var fallbackService:NetService?

	init(log:OSLog) {
		self.log=log
	}

	func publish(type:String, name:String, port:Int32, txtRecord:Data) {
		stop()

		let primaryName=Self.primaryIPv4InterfaceName()
		let interfaceName=BonjourInterfaceSelector.selectedInterfaceName(
			primaryName: primaryName,
			interfaces: Self.activeIPv4Interfaces()
		)
		let interfaceIndex=interfaceName.flatMap { UInt32(if_nametoindex($0)) } ?? 0
		guard interfaceIndex != 0 else {
			os_log("Publishing mDNS service on all interfaces (no primary interface found): name=%{private}@ port=%d", log: log, type: .info, name, port)
			publishWithNetService(type: type, name: name, port: port, txtRecord: txtRecord)
			return
		}
		if let primaryName=primaryName, primaryName != interfaceName {
			os_log("Primary interface %{private}@ is not suitable for local Bonjour; publishing on %{private}@ instead", log: log, type: .info, primaryName, interfaceName!)
		}

		var ref:DNSServiceRef?
		let error:DNSServiceErrorType=txtRecord.withUnsafeBytes { txtBytes in
			DNSServiceRegister(
				&ref,
				0,
				interfaceIndex,
				name,
				type,
				"local.",
				nil,
				UInt16(port).bigEndian,
				UInt16(txtRecord.count),
				txtBytes.baseAddress,
				nil,
				nil
			)
		}
		if error == kDNSServiceErr_NoError, let ref=ref {
			serviceRef=ref
			os_log("Publishing mDNS service: name=%{private}@ port=%d interface=%{private}@(%d)", log: log, type: .info, name, port, interfaceName!, interfaceIndex)
		} else {
			os_log("DNSServiceRegister failed (%d); falling back to all-interface NetService publish", log: log, type: .error, error)
			publishWithNetService(type: type, name: name, port: port, txtRecord: txtRecord)
		}
	}

	func stop() {
		if let serviceRef=serviceRef {
			DNSServiceRefDeallocate(serviceRef)
			self.serviceRef=nil
		}
		fallbackService?.stop()
		fallbackService=nil
	}

	private func publishWithNetService(type:String, name:String, port:Int32, txtRecord:Data) {
		let service=NetService(domain: "", type: type, name: name, port: port)
		service.setTXTRecord(txtRecord)
		service.publish()
		fallbackService=service
	}

	private static func primaryIPv4InterfaceName() -> String? {
		guard let state=SCDynamicStoreCopyValue(nil, "State:/Network/Global/IPv4" as CFString) as? [String:Any] else { return nil }
		return state["PrimaryInterface"] as? String
	}

	private static func activeIPv4Interfaces() -> [BonjourIPv4Interface] {
		var addresses:UnsafeMutablePointer<ifaddrs>?
		guard getifaddrs(&addresses)==0, let first=addresses else { return [] }
		defer { freeifaddrs(addresses) }

		var interfaces:[BonjourIPv4Interface]=[]
		var pointer:UnsafeMutablePointer<ifaddrs>?=first
		while let current=pointer {
			defer { pointer=current.pointee.ifa_next }
			guard let addr=current.pointee.ifa_addr else { continue }
			guard addr.pointee.sa_family == sa_family_t(AF_INET) else { continue }
			guard let namePointer=current.pointee.ifa_name else { continue }

			var host=[CChar](repeating: 0, count: Int(NI_MAXHOST))
			let result=getnameinfo(
				addr,
				socklen_t(addr.pointee.sa_len),
				&host,
				socklen_t(host.count),
				nil,
				0,
				NI_NUMERICHOST
			)
			guard result==0 else { continue }

			interfaces.append(BonjourIPv4Interface(
				name: String(cString: namePointer),
				address: String(cString: host),
				flags: current.pointee.ifa_flags
			))
		}
		return interfaces
	}
}

struct EndpointInfo{
	var name:String?
	let deviceType:RemoteDeviceInfo.DeviceType
	let qrCodeData:Data?
	
	init(name: String, deviceType: RemoteDeviceInfo.DeviceType){
		self.name = name
		self.deviceType = deviceType
		self.qrCodeData=nil
	}
	
	init?(data:Data){
#if DEBUG
		let hexDump=data.prefix(64).map{String(format:"%02x",$0)}.joined(separator: " ")
		os_log("EndpointInfo decode: count=%d byte0=0x%02x hex=%{public}@", log: pyontaLog, type: .info, data.count, Int(data.first ?? 0), hexDump)
#endif
		guard data.count>=17 else {
#if DEBUG
			os_log("  -> reject: data too short", log: pyontaLog, type: .info)
#endif
			return nil
		}
		let hasName=(data[0] & 0x10)==0
#if DEBUG
		os_log("  hasName=%d (bit0x10=%d), deviceTypeRaw=%d", log: pyontaLog, type: .info, hasName ? 1 : 0, Int(data[0] & 0x10), Int(data[0] & 7) >> 1)
#endif
		let deviceNameLength:Int
		let deviceName:String?
		if hasName{
			deviceNameLength=Int(data[17])
#if DEBUG
			os_log("  deviceNameLength byte17 = %d", log: pyontaLog, type: .info, deviceNameLength)
#endif
			guard data.count>=deviceNameLength+18 else {
#if DEBUG
				os_log("  -> reject: name length %d exceeds data (count=%d)", log: pyontaLog, type: .info, deviceNameLength, data.count)
#endif
				return nil
			}
			guard let _deviceName=String(data: data[18..<(18+deviceNameLength)], encoding: .utf8) else {
#if DEBUG
				os_log("  -> reject: UTF-8 decode failed", log: pyontaLog, type: .info)
#endif
				return nil
			}
			deviceName=_deviceName
#if DEBUG
			os_log("  decoded name=%{private}@", log: pyontaLog, type: .info, _deviceName)
#endif
		}else{
			deviceNameLength=0
			deviceName=nil
		}
		let rawDeviceType:Int=Int(data[0] & 7) >> 1
		self.name=deviceName
		self.deviceType=RemoteDeviceInfo.DeviceType.fromRawValue(value: rawDeviceType)
		var offset=1+16
		if hasName{
			offset=offset+1+deviceNameLength
		}
		var qrCodeData:Data?=nil
		while data.count-offset>2{ // read TLV records, if any
			let type=data[offset]
			let length=Int(data[offset+1])
			offset=offset+2
			if data.count-offset>=length{
				if type==1{ // QR code data
					qrCodeData=data.subdata(in: offset..<offset+length)
				}
				offset=offset+length
			}
		}
		self.qrCodeData=qrCodeData
	}
	
	func serialize()->Data{
		// 1 byte: Version(3 bits)|Visibility(1 bit)|Device Type(3 bits)|Reserved(1 bits)
		// Device types: unknown=0, phone=1, tablet=2, laptop=3
		var endpointInfo:[UInt8]=[UInt8(deviceType.rawValue << 1)]
		// 16 bytes: unknown random bytes
		for _ in 0...15{
			endpointInfo.append(UInt8.random(in: 0...255))
		}
		// Device name in UTF-8 prefixed with 1-byte length
		var nameChars=[UInt8](name!.utf8)
		if nameChars.count>255{
			nameChars=[UInt8](nameChars[0..<255])
		}
		endpointInfo.append(UInt8(nameChars.count))
		for ch in nameChars{
			endpointInfo.append(UInt8(ch))
		}
		return Data(endpointInfo)
	}
}

public protocol MainAppDelegate{
	func obtainUserConsent(for transfer:TransferMetadata, from device:RemoteDeviceInfo)
	func incomingTransfer(id:String, didFinishWith error:Error?)
}

public protocol ShareExtensionDelegate:AnyObject{
	func addDevice(device:RemoteDeviceInfo)
	func updateDevice(device:RemoteDeviceInfo)
	func removeDevice(id:String)
	func startTransferWithQrCode(device:RemoteDeviceInfo)
	func connectionWasEstablished(pinCode:String)
	func connectionFailed(with error:Error)
	func transferAccepted()
	func transferProgress(progress:Double)
	func transferFinished()
}

// Default empty implementation so older delegates compile.
// hostname 解決で機種名が後から判明したときの再描画用。
public extension ShareExtensionDelegate {
	func updateDevice(device:RemoteDeviceInfo) {}
}

public class NearbyConnectionManager : NSObject, NetServiceDelegate, InboundNearbyConnectionDelegate, OutboundNearbyConnectionDelegate{
	
	private var tcpListener:NWListener;
	public let endpointID:[UInt8]=generateEndpointID()
	private var mdnsService:BonjourServicePublisher?
	private var activeConnections:[String:InboundNearbyConnection]=[:]
	private var foundServices:[String:FoundServiceInfo]=[:]
	private var learnedDeviceNames:[String:String]=[:]
	private var recentDeviceNameCache=RecentDeviceNameCache()
	private var shareExtensionDelegates:[ShareExtensionDelegate]=[]
	private var outgoingTransfers:[String:OutgoingTransferInfo]=[:]
	public var mainAppDelegate:(any MainAppDelegate)?
	private var discoveryRefCount=0
	
	private var browser:NWBrowser?
	private let deviceNameResolver = NearbyDeviceNameResolver()
	private let networkPathMonitor=NWPathMonitor()
	private let networkPathMonitorQueue=DispatchQueue(label: "com.odiften.pyonta.networkPathMonitor", qos: .utility)
	private var lastNetworkPathSignature:NetworkPathSignature?
	private var networkResyncWorkItem:DispatchWorkItem?
	private var emptyDiscoveryRefreshTimer:Timer?

	private var qrCodePublicKey:ECPublicKey?
	private var qrCodePrivateKey:ECPrivateKey?
	private var qrCodeAdvertisingToken:Data?
	private var qrCodeNameEncryptionKey:SymmetricKey?
	private var qrCodeData:Data?
	
	public static let shared=NearbyConnectionManager()
	
	override init() {
		tcpListener=try! NWListener(using: NWParameters(tls: .none))
		super.init()
		startNetworkPathMonitor()
	}
	
	private var tcpListenerStarted=false
	public private(set) var isVisible:Bool=false

	public func becomeVisible(){
		guard !isVisible else { return }
		isVisible=true
		if !tcpListenerStarted {
			tcpListenerStarted=true
			startTCPListener()  // when ready, stateUpdateHandler calls initMDNS
		} else {
			initMDNS()  // tcp already up, just re-publish bonjour record
		}
	}

	public func becomeInvisible(){
		guard isVisible else { return }
		isVisible=false
		mdnsService?.stop()
		mdnsService=nil
	}

	private func startNetworkPathMonitor(){
		networkPathMonitor.pathUpdateHandler={ [weak self] path in
			let signature=NetworkPathSignature(path: path)
			DispatchQueue.main.async {
				self?.handleNetworkPathUpdate(signature)
			}
		}
		networkPathMonitor.start(queue: networkPathMonitorQueue)
	}

	private func handleNetworkPathUpdate(_ signature:NetworkPathSignature){
		guard lastNetworkPathSignature != signature else { return }
		lastNetworkPathSignature=signature
		os_log("Network path changed: status=%{public}@ wifi=%{public}@ wired=%{public}@ interfaces=%{private}@",
			   log: pyontaLog,
			   type: .info,
			   signature.status,
			   signature.usesWiFi ? "yes" : "no",
			   signature.usesWiredEthernet ? "yes" : "no",
			   signature.interfaces.joined(separator: ","))

		if signature.isSatisfied {
			scheduleNetworkResync(reason: "network path changed")
		} else {
			mdnsService?.stop()
			mdnsService=nil
			pauseDeviceBrowserForNetworkLoss(reason: "network path unavailable")
		}
	}

	private func scheduleNetworkResync(reason:String){
		networkResyncWorkItem?.cancel()
		let workItem=DispatchWorkItem { [weak self] in
			self?.resyncNetworkServices(reason: reason)
		}
		networkResyncWorkItem=workItem
		DispatchQueue.main.asyncAfter(deadline: .now()+1.0, execute: workItem)
	}

	private func resyncNetworkServices(reason:String){
		os_log("Resyncing network services: %{public}@", log: pyontaLog, type: .info, reason)
		if isVisible, tcpListener.port != nil {
			initMDNS()
		}
		if discoveryRefCount>0 {
			restartDeviceBrowser(reason: reason, clearFoundDevices: true)
		}
	}
	
	private func startTCPListener(){
		tcpListener.stateUpdateHandler={(state:NWListener.State) in
			os_log("TCP listener state changed to %{private}@", log: pyontaLog, type: .info, "\(state)")
			if case .ready = state {
				self.initMDNS()
			}
		}
		tcpListener.newConnectionHandler={(connection:NWConnection) in
			let id=UUID().uuidString
			os_log("Accepted inbound connection: id=%{private}@ endpoint=%{private}@", log: pyontaLog, type: .info, id, "\(connection.endpoint)")
			let conn=InboundNearbyConnection(connection: connection, id: id)
			self.activeConnections[id]=conn
			conn.delegate=self
			conn.start()
		}
		tcpListener.start(queue: .global(qos: .utility))
	}
	
	private static func generateEndpointID()->[UInt8]{
		var id:[UInt8]=[]
		let alphabet="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ".compactMap {UInt8($0.asciiValue!)}
		for _ in 0...3{
			id.append(alphabet[Int.random(in: 0..<alphabet.count)])
		}
		return id
	}
	
	private func initMDNS(){
		let nameBytes:[UInt8]=[
			0x23, // PCP
			endpointID[0], endpointID[1], endpointID[2], endpointID[3],
			0xFC, 0x9F, 0x5E, // Service ID hash
			0, 0
		]
		let name=Data(nameBytes).urlSafeBase64EncodedString()
		let endpointInfo=EndpointInfo(name: Host.current().localizedName!, deviceType: .computer)
		
		let port:Int32=Int32(tcpListener.port!.rawValue)
		let txtRecord=NetService.data(fromTXTRecord: [
			"n": endpointInfo.serialize().urlSafeBase64EncodedString().data(using: .utf8)!
		])
		mdnsService=BonjourServicePublisher(log: pyontaLog)
		mdnsService?.publish(type: "_FC9F5ED42C8A._tcp", name: name, port: port, txtRecord: txtRecord)
	}
	
	func obtainUserConsent(for transfer: TransferMetadata, from device: RemoteDeviceInfo, connection: InboundNearbyConnection) {
		rememberLearnedDeviceName(device.name, endpointID: connection.remoteEndpointID, deviceType: device.type)
		guard let delegate=mainAppDelegate else {return}
		delegate.obtainUserConsent(for: transfer, from: device)
	}
	
	func connectionWasTerminated(connection:InboundNearbyConnection, error:Error?){
		guard let delegate=mainAppDelegate else {return}
		delegate.incomingTransfer(id: connection.id, didFinishWith: error)
		activeConnections.removeValue(forKey: connection.id)
	}
	
	public func submitUserConsent(transferID:String, accept:Bool){
		guard let conn=activeConnections[transferID] else {return}
		conn.submitUserConsent(accepted: accept)
	}
	
	public func startDeviceDiscovery(){
#if DEBUG
		os_log("startDeviceDiscovery called (refCount=%d)", log: pyontaLog, type: .info, discoveryRefCount)
#endif
		if discoveryRefCount==0{
			clearFoundDevices(reason: "device discovery started")
			startDeviceBrowser()
			startEmptyDiscoveryRefreshTimer()
		}
		discoveryRefCount+=1
	}
	
	public func stopDeviceDiscovery(){
		if discoveryRefCount<=0{
			os_log("stopDeviceDiscovery called with no active discovery", log: pyontaLog, type: .fault)
			discoveryRefCount=0
			return
		}
		discoveryRefCount-=1
		if discoveryRefCount==0{
			browser?.cancel()
			browser=nil
			stopEmptyDiscoveryRefreshTimer()
			deviceNameResolver.cancelAll()
		}
	}

	private func startDeviceBrowser(){
		browser?.cancel()
		let browser=NWBrowser(for: .bonjourWithTXTRecord(type: "_FC9F5ED42C8A._tcp.", domain: nil), using: .tcp)
		browser.stateUpdateHandler={ [weak self] state in
#if DEBUG
			os_log("NWBrowser state changed to %{public}@", log: pyontaLog, type: .info, "\(state)")
#endif
			if case .failed = state {
				DispatchQueue.main.async {
					self?.restartDeviceBrowser(reason: "NWBrowser failed", clearFoundDevices: true)
				}
			}
		}
		browser.browseResultsChangedHandler={ [weak self] newResults, changes in
			guard let self=self else { return }
#if DEBUG
			os_log("browseResultsChangedHandler: %d changes, %d total results", log: pyontaLog, type: .info, changes.count, newResults.count)
#endif
			for change in changes{
				switch change{
				case let .added(res):
#if DEBUG
					os_log("  added: %{public}@", log: pyontaLog, type: .info, "\(res.endpoint)")
#endif
					self.maybeAddFoundDevice(service: res)
				case let .removed(res):
#if DEBUG
					os_log("  removed: %{public}@", log: pyontaLog, type: .info, "\(res.endpoint)")
#endif
					self.maybeRemoveFoundDevice(service: res)
				default:
					break
				}
			}
		}
		self.browser=browser
		browser.start(queue: .main)
#if DEBUG
		os_log("NWBrowser.start called", log: pyontaLog, type: .info)
#endif
	}

	private func restartDeviceBrowser(reason:String, clearFoundDevices:Bool){
		guard discoveryRefCount>0 else { return }
		os_log("Restarting device discovery: %{public}@", log: pyontaLog, type: .info, reason)
		browser?.cancel()
		browser=nil
		if clearFoundDevices {
			self.clearFoundDevices(reason: reason)
		}
		startDeviceBrowser()
	}

	private func pauseDeviceBrowserForNetworkLoss(reason:String){
		browser?.cancel()
		browser=nil
		clearFoundDevices(reason: reason)
	}

	private func startEmptyDiscoveryRefreshTimer(){
		emptyDiscoveryRefreshTimer?.invalidate()
		emptyDiscoveryRefreshTimer=Timer.scheduledTimer(withTimeInterval: 12.0, repeats: true) { [weak self] _ in
			guard let self=self else { return }
			guard self.discoveryRefCount>0, self.foundServices.isEmpty else { return }
			self.restartDeviceBrowser(reason: "empty discovery refresh", clearFoundDevices: false)
		}
	}

	private func stopEmptyDiscoveryRefreshTimer(){
		emptyDiscoveryRefreshTimer?.invalidate()
		emptyDiscoveryRefreshTimer=nil
	}
	
	public func addShareExtensionDelegate(_ delegate:ShareExtensionDelegate){
		shareExtensionDelegates.append(delegate)
		for service in foundServices.values{
			guard let device=service.device else {continue}
			delegate.addDevice(device: device)
		}
	}
	
	public func removeShareExtensionDelegate(_ delegate:ShareExtensionDelegate){
		shareExtensionDelegates.removeAll(where: {$0===delegate})
	}
	
	public func cancelOutgoingTransfer(id:String){
		guard let transfer=outgoingTransfers[id] else {return}
		transfer.connection.cancel()
	}
	
	private func endpointID(for service:NWBrowser.Result)->String?{
		guard case let NWEndpoint.service(name: serviceName, type: _, domain: _, interface: _)=service.endpoint else {return nil}
		guard let nameData=Data.dataFromUrlSafeBase64(serviceName) else {return nil}
		guard nameData.count>=10 else {return nil}
		let pcp=nameData[0]
		guard pcp==0x23 else {return nil}
		let endpointID=String(data: nameData.subdata(in: 1..<5), encoding: .ascii)!
		let serviceIDHash=nameData.subdata(in: 5..<8)
		guard serviceIDHash==Data([0xFC, 0x9F, 0x5E]) else {return nil}
		return endpointID
	}
	
	private func maybeAddFoundDevice(service:NWBrowser.Result){
#if DEBUG
		os_log("maybeAddFoundDevice: %{public}@", log: pyontaLog, type: .info, "\(service.endpoint)")
#endif
		for interface in service.interfaces{
			if case .loopback=interface.type{
#if DEBUG
				os_log("  -> ignored (loopback)", log: pyontaLog, type: .info)
#endif
				return
			}
		}
		guard let endpointID=endpointID(for: service) else {
#if DEBUG
			os_log("  -> rejected: invalid endpointID", log: pyontaLog, type: .info)
#endif
			return
		}
		if endpointID == String(bytes: self.endpointID, encoding: .ascii)! {
#if DEBUG
			os_log("  -> ignored (self endpointID=%{private}@)", log: pyontaLog, type: .info, endpointID)
#endif
			return
		}
#if DEBUG
		os_log("  -> service name valid, endpointID=%{private}@", log: pyontaLog, type: .info, endpointID)
#endif
		var foundService=preferredFoundService(for: endpointID, newService: service)
		
		guard case let NWBrowser.Result.Metadata.bonjour(txtRecord)=service.metadata else {
#if DEBUG
			os_log("  -> rejected: no bonjour TXT metadata", log: pyontaLog, type: .info)
#endif
			return
		}
		guard let endpointInfoEncoded=txtRecord.dictionary["n"] else {
#if DEBUG
			os_log("  -> rejected: TXT lacks 'n' key", log: pyontaLog, type: .info)
#endif
			return
		}
		guard let endpointInfoSerialized=Data.dataFromUrlSafeBase64(endpointInfoEncoded) else {
#if DEBUG
			os_log("  -> rejected: 'n' value not valid base64", log: pyontaLog, type: .info)
#endif
			return
		}
		guard var endpointInfo=EndpointInfo(data: endpointInfoSerialized) else {
#if DEBUG
			os_log("  -> rejected: EndpointInfo decode failed", log: pyontaLog, type: .info)
#endif
			return
		}
#if DEBUG
		os_log("  -> EndpointInfo: name=%{private}@ type=%d", log: pyontaLog, type: .info, endpointInfo.name ?? "(nil)", endpointInfo.deviceType.rawValue)
#endif

		if deviceNameResolver.needsLookup(for: endpointInfo),
		   let learnedName=learnedDeviceNames[endpointID] {
			endpointInfo.name=learnedName
		} else if deviceNameResolver.needsLookup(for: endpointInfo),
				  let recentName=recentDeviceNameCache.uniqueRecentName(for: endpointInfo.deviceType) {
			endpointInfo.name=recentName
		} else if let name=endpointInfo.name, !isFallbackDeviceName(name) {
			recentDeviceNameCache.remember(name: name, type: endpointInfo.deviceType)
		}

		// Quick Share v3 (Hidden mode) では Bonjour TXT に name が無い。
		// その場合は mDNS hostname の reverse DNS lookup で機種名を補完する。
		let needsDeviceNameLookup=deviceNameResolver.needsLookup(for: endpointInfo)

		var deviceInfo:RemoteDeviceInfo?
		deviceInfo=addFoundDevice(foundService: &foundService, endpointInfo: endpointInfo, endpointID: endpointID)

		if needsDeviceNameLookup {
			let capturedEndpointInfo=endpointInfo
			deviceNameResolver.resolveName(for: service, endpointID: endpointID) { [weak self] resolvedName in
				guard let self=self else { return }
				// すでに別経路で名前が解決済 / デバイスが消えた場合はスキップ
				guard var stale=self.foundServices[endpointID] else { return }
				var updatedEndpointInfo=capturedEndpointInfo
				updatedEndpointInfo.name=resolvedName
				self.recentDeviceNameCache.remember(name: resolvedName, type: updatedEndpointInfo.deviceType)
				_=self.addFoundDevice(foundService: &stale, endpointInfo: updatedEndpointInfo, endpointID: endpointID)
			}
		} else {
			deviceNameResolver.cancelLookup(for: endpointID)
		}
		
		if let qrData=endpointInfo.qrCodeData, let _=qrCodeAdvertisingToken{
#if DEBUG
			print("Device has QR data: \(qrData.base64EncodedString()), our advertising token is \(qrCodeAdvertisingToken!.base64EncodedString())")
#endif
			if qrData==qrCodeAdvertisingToken!{
				if let deviceInfo=deviceInfo{
					for delegate in shareExtensionDelegates{
						delegate.startTransferWithQrCode(device: deviceInfo)
					}
				}
			}else if qrData.count>28{
				do{
					let box=try AES.GCM.SealedBox(combined: qrData)
					let decryptedName=try AES.GCM.open(box, using: qrCodeNameEncryptionKey!, authenticating: qrCodeAdvertisingToken!)
					guard let name=String.init(data: decryptedName, encoding: .utf8) else {return}
					endpointInfo.name=name
					let deviceInfo=addFoundDevice(foundService: &foundService, endpointInfo: endpointInfo, endpointID: endpointID)
					for delegate in shareExtensionDelegates{
						delegate.startTransferWithQrCode(device: deviceInfo)
					}
				}catch{
#if DEBUG
					print("Error decrypting QR code data of an invisible device: \(error)")
#endif
				}
			}
		}
	}

	private func preferredFoundService(for endpointID:String, newService:NWBrowser.Result) -> FoundServiceInfo{
		guard let existing=foundServices[endpointID] else {
			return FoundServiceInfo(service: newService)
		}
		let existingScore=servicePreferenceScore(existing.service)
		let newScore=servicePreferenceScore(newService)
		if newScore < existingScore {
#if DEBUG
			os_log("  -> keeping existing service route for %{private}@ (existing=%d new=%d)", log: pyontaLog, type: .info, endpointID, existingScore, newScore)
#endif
			return existing
		}
		if newScore > existingScore {
#if DEBUG
			os_log("  -> replacing service route for %{private}@ (existing=%d new=%d)", log: pyontaLog, type: .info, endpointID, existingScore, newScore)
#endif
		}
		return FoundServiceInfo(service: newService)
	}

	private func rememberLearnedDeviceName(_ name:String, endpointID:String?, deviceType:RemoteDeviceInfo.DeviceType){
		guard let endpointID=endpointID else { return }
		let cleaned=name.trimmingCharacters(in: .whitespacesAndNewlines)
		guard !cleaned.isEmpty, !isFallbackDeviceName(cleaned) else { return }
		learnedDeviceNames[endpointID]=cleaned
		recentDeviceNameCache.remember(name: cleaned, type: deviceType)

		guard var foundService=foundServices[endpointID], let device=foundService.device else { return }
		guard device.name != cleaned else { return }
		let updatedDevice=device.renamed(cleaned)
		foundService.device=updatedDevice
		foundServices[endpointID]=foundService
		for delegate in shareExtensionDelegates {
			delegate.updateDevice(device: updatedDevice)
		}
	}

	private func isFallbackDeviceName(_ name:String) -> Bool {
		let fallback=NSLocalizedString("UnknownAndroidDevice", value: "Android device", comment: "")
		return name == fallback || name == "Android device"
	}

	private func servicePreferenceScore(_ service:NWBrowser.Result) -> Int{
		guard !service.interfaces.isEmpty else { return 10 }
		return service.interfaces.reduce(0) { score, interface in
			let interfaceScore:Int
			switch interface.type {
			case .wifi:
				interfaceScore=400
			case .wiredEthernet:
				interfaceScore=300
			case .cellular:
				interfaceScore=200
			case .other:
				interfaceScore=100
			case .loopback:
				interfaceScore=0
			@unknown default:
				interfaceScore=50
			}
			return max(score, interfaceScore)
		}
	}
	
	private func addFoundDevice(foundService:inout FoundServiceInfo, endpointInfo:EndpointInfo, endpointID:String) -> RemoteDeviceInfo{
		let hadPreviousDevice=foundServices[endpointID]?.device != nil
		let deviceInfo=RemoteDeviceInfo(info: endpointInfo, id: endpointID)
		foundService.device=deviceInfo
		foundServices[endpointID]=foundService
#if DEBUG
		os_log("addFoundDevice: name=%{private}@ id=%{private}@ delegates=%d previous=%{public}@", log: pyontaLog, type: .info, deviceInfo.name, endpointID, shareExtensionDelegates.count, hadPreviousDevice ? "yes(update)" : "no(add)")
#endif
		for delegate in shareExtensionDelegates{
			if hadPreviousDevice {
				delegate.updateDevice(device: deviceInfo)
			} else {
				delegate.addDevice(device: deviceInfo)
			}
		}
		return deviceInfo
	}

	private func maybeRemoveFoundDevice(service:NWBrowser.Result){
		guard let endpointID=endpointID(for: service) else {return}
		removeFoundDevice(endpointID: endpointID, reason: "browser result removed")
	}

	private func removeFoundDevice(endpointID:String, reason:String){
		deviceNameResolver.cancelLookup(for: endpointID)
		guard let _=foundServices.removeValue(forKey: endpointID) else {return}
		os_log("Removing discovered device: id=%{private}@ reason=%{public}@", log: pyontaLog, type: .info, endpointID, reason)
		for delegate in shareExtensionDelegates {
			delegate.removeDevice(id: endpointID)
		}
	}

	private func clearFoundDevices(reason:String){
		guard !foundServices.isEmpty else { return }
		let endpointIDs=Array(foundServices.keys)
		foundServices.removeAll()
		deviceNameResolver.cancelAll()
		os_log("Clearing discovered devices: count=%d reason=%{public}@", log: pyontaLog, type: .info, endpointIDs.count, reason)
		for endpointID in endpointIDs {
			for delegate in shareExtensionDelegates {
				delegate.removeDevice(id: endpointID)
			}
		}
	}
	
	public func generateQrCodeKey() -> String{
		let domain=Domain.instance(curve: .EC256r1)
		let (pubKey, privKey)=domain.makeKeyPair()
		qrCodePublicKey=pubKey
		qrCodePrivateKey=privKey
		var keyData=Data()
		keyData.append(contentsOf: [0, 0, 2])
		let keyBytes=Data(pubKey.w.x.asSignedBytes())
		// Sometimes, for some keys, there will be a leading zero byte. Strip that, Android really hates it (it breaks the endpoint info)
		keyData.append(keyBytes.suffixOfAtMost(numBytes: 32))
		
		let ikm=SymmetricKey(data: keyData)
		qrCodeAdvertisingToken=NearbyConnection.hkdf(inputKeyMaterial: ikm, salt: Data(), info: "advertisingContext".data(using: .utf8)!, outputByteCount: 16).data()
		qrCodeNameEncryptionKey=NearbyConnection.hkdf(inputKeyMaterial: ikm, salt: Data(), info: "encryptionKey".data(using: .utf8)!, outputByteCount: 16)
		qrCodeData=keyData
		
		return keyData.urlSafeBase64EncodedString()
	}
	
	public func clearQrCodeKey(){
		qrCodePublicKey=nil
		qrCodePrivateKey=nil
		qrCodeAdvertisingToken=nil
		qrCodeNameEncryptionKey=nil
		qrCodeData=nil
	}
	
	public func startOutgoingTransfer(deviceID:String, delegate:ShareExtensionDelegate, urls:[URL]){
		guard let info=foundServices[deviceID] else {return}
		os_log("Starting outgoing file transfer: id=%{private}@ endpoint=%{private}@ interfaces=%{private}@", log: pyontaLog, type: .info, deviceID, "\(info.service.endpoint)", "\(info.service.interfaces)")
		let tcp=NWProtocolTCP.Options.init()
		tcp.noDelay=true
		let nwconn=NWConnection(to: info.service.endpoint, using: NWParameters(tls: .none, tcp: tcp))
		let conn=OutboundNearbyConnection(connection: nwconn, id: deviceID, urlsToSend: urls)
		conn.delegate=self
		conn.qrCodePrivateKey=qrCodePrivateKey
		let transfer=OutgoingTransferInfo(service: info.service, device: info.device!, connection: conn, delegate: delegate)
		storeOutgoingTransfer(transfer, for: deviceID)
		conn.start()
	}

	public func startOutgoingTransfer(deviceID:String, delegate:ShareExtensionDelegate, text:String, isURL:Bool){
		guard let info=foundServices[deviceID] else {return}
		os_log("Starting outgoing text transfer: id=%{private}@ endpoint=%{private}@ interfaces=%{private}@", log: pyontaLog, type: .info, deviceID, "\(info.service.endpoint)", "\(info.service.interfaces)")
		let tcp=NWProtocolTCP.Options.init()
		tcp.noDelay=true
		let nwconn=NWConnection(to: info.service.endpoint, using: NWParameters(tls: .none, tcp: tcp))
		let conn=OutboundNearbyConnection(connection: nwconn, id: deviceID, textToSend: text, isURL: isURL)
		conn.delegate=self
		conn.qrCodePrivateKey=qrCodePrivateKey
		let transfer=OutgoingTransferInfo(service: info.service, device: info.device!, connection: conn, delegate: delegate)
		storeOutgoingTransfer(transfer, for: deviceID)
		conn.start()
	}

	private func storeOutgoingTransfer(_ transfer:OutgoingTransferInfo, for deviceID:String){
		let previous=outgoingTransfers.updateValue(transfer, forKey: deviceID)
		if let previous=previous, previous.connection !== transfer.connection {
			previous.connection.cancel()
		}
	}

	private func activeOutgoingTransfer(for connection:OutboundNearbyConnection) -> OutgoingTransferInfo? {
		guard let transfer=outgoingTransfers[connection.id] else { return nil }
		guard transfer.connection === connection else {
			os_log("Ignoring stale outgoing transfer callback: id=%{private}@", log: pyontaLog, type: .info, connection.id)
			return nil
		}
		return transfer
	}
	
	func outboundConnectionWasEstablished(connection: OutboundNearbyConnection) {
		guard let transfer=activeOutgoingTransfer(for: connection) else {return}
		DispatchQueue.main.async {
			transfer.delegate.connectionWasEstablished(pinCode: connection.pinCode!)
		}
	}
	
	func outboundConnectionTransferAccepted(connection: OutboundNearbyConnection) {
		guard let transfer=activeOutgoingTransfer(for: connection) else {return}
		DispatchQueue.main.async {
			transfer.delegate.transferAccepted()
		}
	}
	
	func outboundConnection(connection: OutboundNearbyConnection, transferProgress: Double) {
		guard let transfer=activeOutgoingTransfer(for: connection) else {return}
		DispatchQueue.main.async {
			transfer.delegate.transferProgress(progress: transferProgress)
		}
	}
	
	func outboundConnection(connection: OutboundNearbyConnection, failedWithError: Error) {
		guard let transfer=activeOutgoingTransfer(for: connection) else {return}
		DispatchQueue.main.async {
			transfer.delegate.connectionFailed(with: failedWithError)
		}
		outgoingTransfers.removeValue(forKey: connection.id)
		if shouldRemoveFoundDevice(after: failedWithError) {
			removeFoundDevice(endpointID: connection.id, reason: "outgoing connection failed")
		}
	}
	
	func outboundConnectionTransferFinished(connection: OutboundNearbyConnection) {
		guard let transfer=activeOutgoingTransfer(for: connection) else {return}
		DispatchQueue.main.async {
			transfer.delegate.transferFinished()
		}
		outgoingTransfers.removeValue(forKey: connection.id)
	}

	private func shouldRemoveFoundDevice(after error:Error) -> Bool{
		guard let nearbyError=error as? NearbyError else { return false }
		switch nearbyError {
		case .inputOutput, .canceled(.timedOut):
			return true
		default:
			return false
		}
	}
}
