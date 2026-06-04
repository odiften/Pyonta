//
//  InboundNearbyConnection.swift
//  Pyonta
//
//  Created by Grishka on 08.04.2023.
//

import Foundation
import Network
import CryptoKit
import CommonCrypto
import System
import AppKit
import os.log

import SwiftECC
import BigInt

fileprivate let pyontaReceiveLog = OSLog(subsystem: "com.odiften.pyonta", category: "receive")
fileprivate let openReceivedURLsUserDefaultsKey = "openReceivedURLs"
fileprivate let autoAcceptUserDefaultsKey = "automaticallyAcceptFiles"

class InboundNearbyConnection: NearbyConnection{

	private static let userConsentTimeout:TimeInterval = 60.0
	private static let minimumFreeBytesAfterTransfer:Int64 = 100*1024*1024
	static let maximumIncomingFileCount = 1000
	private var currentState:State = .initial
	public var delegate:InboundNearbyConnectionDelegate?
	private var cipherCommitment:Data?
	private var consentTimeoutWorkItem:DispatchWorkItem?

	private var textPayloadID:Int64=0
	private var textPayloadIsURL:Bool=false

	private static func shouldOpenReceivedURLs() -> Bool {
		let defaults=UserDefaults.standard
		guard defaults.bool(forKey: autoAcceptUserDefaultsKey) else { return false }
		guard defaults.object(forKey: openReceivedURLsUserDefaultsKey) != nil else { return false }
		return defaults.bool(forKey: openReceivedURLsUserDefaultsKey)
	}

	private static func httpURL(from text:String) -> URL? {
		let trimmed=text.trimmingCharacters(in: .whitespacesAndNewlines)
		guard !trimmed.contains(" "), !trimmed.contains("\n"), !trimmed.contains("\t") else { return nil }
		guard let url=URL(string: trimmed), let scheme=url.scheme?.lowercased() else { return nil }
		guard scheme=="http" || scheme=="https" else { return nil }
		return url
	}

	private static func copyToPasteboard(_ text:String) {
		NSPasteboard.general.clearContents()
		NSPasteboard.general.setString(text, forType: .string)
	}
	
	enum State{
		case initial, receivedConnectionRequest, sentUkeyServerInit, receivedUkeyClientFinish, sentConnectionResponse, sentPairedKeyResult, receivedPairedKeyResult, waitingForUserConsent, receivingFiles, disconnected
	}
	
	override init(connection: NWConnection, id:String) {
		super.init(connection: connection, id: id)
	}

	deinit {
		cancelUserConsentTimeout()
	}
	
	override func handleConnectionClosure() {
		super.handleConnectionClosure()
		cancelUserConsentTimeout()
		currentState = .disconnected
		do{
			try deletePartiallyReceivedFiles()
		}catch{
			os_log("Error deleting partially received files: %{private}@", log: pyontaReceiveLog, type: .error, "\(error)")
		}
		DispatchQueue.main.async {
			self.delegate?.connectionWasTerminated(connection: self, error: self.lastError)
		}
	}
	
	override internal func processReceivedFrame(frameData:Data){
		do{
			switch currentState {
			case .initial:
				let frame=try Location_Nearby_Connections_OfflineFrame(serializedData: frameData)
				try processConnectionRequestFrame(frame)
			case .receivedConnectionRequest:
				let msg=try Securegcm_Ukey2Message(serializedData: frameData)
				ukeyClientInitMsgData=frameData
				try processUkey2ClientInit(msg)
			case .sentUkeyServerInit:
				let msg=try Securegcm_Ukey2Message(serializedData: frameData)
				try processUkey2ClientFinish(msg, raw: frameData)
			case .receivedUkeyClientFinish:
				let frame=try Location_Nearby_Connections_OfflineFrame(serializedData: frameData)
				try processConnectionResponseFrame(frame)
			default:
				let smsg=try Securemessage_SecureMessage(serializedData: frameData)
				try decryptAndProcessReceivedSecureMessage(smsg)
			}
		}catch{
			lastError=error
#if DEBUG
			print("Deserialization error: \(error) in state \(currentState)")
#endif
			protocolError()
		}
	}
	
	override internal func processTransferSetupFrame(_ frame:Sharing_Nearby_Frame) throws{
		if frame.hasV1 && frame.v1.hasType, case .cancel = frame.v1.type {
#if DEBUG
			print("Transfer canceled")
#endif
			try sendDisconnectionAndDisconnect()
			return
		}
		switch currentState{
		case .sentConnectionResponse:
			try processPairedKeyEncryptionFrame(frame)
		case .sentPairedKeyResult:
			try processPairedKeyResultFrame(frame)
		case .receivedPairedKeyResult:
			try processIntroductionFrame(frame)
		default:
#if DEBUG
			print("Unexpected connection state in processTransferSetupFrame: \(currentState)")
			print(frame)
#endif
		}
	}
	
	override func isServer() -> Bool {
		return true
	}
	
	override func processFileChunk(frame: Location_Nearby_Connections_PayloadTransferFrame) throws{
		let id=frame.payloadHeader.id
		guard let fileInfo=transferredFiles[id] else { throw NearbyError.protocolError("File payload ID \(id) is not known") }
		let currentOffset=fileInfo.bytesTransferred
		guard frame.payloadChunk.offset==currentOffset else { throw NearbyError.protocolError("Invalid offset into file \(frame.payloadChunk.offset), expected \(currentOffset)") }
		guard currentOffset+Int64(frame.payloadChunk.body.count)<=fileInfo.meta.size else { throw NearbyError.protocolError("Transferred file size exceeds previously specified value") }
		if frame.payloadChunk.body.count>0{
			fileInfo.fileHandle?.write(frame.payloadChunk.body)
			transferredFiles[id]!.bytesTransferred+=Int64(frame.payloadChunk.body.count)
			fileInfo.progress?.completedUnitCount=transferredFiles[id]!.bytesTransferred
		}else if (frame.payloadChunk.flags & 1)==1{
			try fileInfo.fileHandle?.close()
			transferredFiles[id]!.fileHandle=nil
			fileInfo.progress?.unpublish()
			transferredFiles.removeValue(forKey: id)
			if transferredFiles.isEmpty{
				try sendDisconnectionAndDisconnect()
			}
		}
	}
	
	override func processBytesPayload(payload: Data, id: Int64) throws -> Bool {
		if id==textPayloadID{
			if let s=String(data: payload, encoding: .utf8){
				DispatchQueue.main.async {
					if self.textPayloadIsURL,
					   Self.shouldOpenReceivedURLs(),
					   let url=Self.httpURL(from: s),
					   NSWorkspace.shared.open(url) {
						return
					}
					Self.copyToPasteboard(s)
				}
				os_log("Received text payload: id=%{private}@ kind=%{public}@ bytes=%d",
					   log: pyontaReceiveLog,
					   type: .info,
					   "\(id)",
					   textPayloadIsURL ? "url" : "text",
					   payload.count)
			}
			try sendDisconnectionAndDisconnect()
			return true
		}else if let fileInfo=transferredFiles[id]{
			fileInfo.fileHandle?.write(payload)
			transferredFiles[id]!.bytesTransferred+=Int64(payload.count)
			fileInfo.progress?.completedUnitCount=transferredFiles[id]!.bytesTransferred
			try fileInfo.fileHandle?.close()
			transferredFiles[id]!.fileHandle=nil
			fileInfo.progress?.unpublish()
			transferredFiles.removeValue(forKey: id)
			try sendDisconnectionAndDisconnect()
			return true
		}
		return false
	}
	
	private func processConnectionRequestFrame(_ frame:Location_Nearby_Connections_OfflineFrame) throws{
		guard frame.hasV1 && frame.v1.hasConnectionRequest && frame.v1.connectionRequest.hasEndpointInfo else { throw NearbyError.requiredFieldMissing("connectionRequest.endpointInfo") }
		guard case .connectionRequest = frame.v1.type else { throw NearbyError.protocolError("Unexpected frame type \(frame.v1.type)") }
		let endpointInfo=frame.v1.connectionRequest.endpointInfo
		guard endpointInfo.count>17 else { throw NearbyError.protocolError("Endpoint info too short") }
		let deviceNameLength=Int(endpointInfo[17])
		guard endpointInfo.count>=deviceNameLength+18 else { throw NearbyError.protocolError("Endpoint info too short to contain the device name") }
		guard let deviceName=String(data: endpointInfo[18..<(18+deviceNameLength)], encoding: .utf8) else { throw NearbyError.protocolError("Device name is not valid UTF-8") }
		let rawDeviceType:Int=Int(endpointInfo[0] & 7) >> 1
		remoteDeviceInfo=RemoteDeviceInfo(name: deviceName, type: RemoteDeviceInfo.DeviceType.fromRawValue(value: rawDeviceType))
		os_log("Inbound connection request: id=%{private}@ device=%{private}@", log: pyontaReceiveLog, type: .info, id, deviceName)
		currentState = .receivedConnectionRequest
	}
	
	private func processUkey2ClientInit(_ msg:Securegcm_Ukey2Message) throws{
		guard msg.hasMessageType, msg.hasMessageData else { throw NearbyError.requiredFieldMissing("clientInit ukey2message.type|data") }
		guard case .clientInit = msg.messageType else{
			sendUkey2Alert(type: .badMessageType)
			throw NearbyError.ukey2
		}
		let clientInit:Securegcm_Ukey2ClientInit
		do{
			clientInit=try Securegcm_Ukey2ClientInit(serializedData: msg.messageData)
		}catch{
			sendUkey2Alert(type: .badMessageData)
			throw NearbyError.ukey2
		}
		guard clientInit.version==1 else{
			sendUkey2Alert(type: .badVersion)
			throw NearbyError.ukey2
		}
		guard clientInit.random.count==32 else{
			sendUkey2Alert(type: .badRandom)
			throw NearbyError.ukey2
		}
		var found=false
		for commitment in clientInit.cipherCommitments{
			if case .p256Sha512 = commitment.handshakeCipher{
				found=true
				cipherCommitment=commitment.commitment
				break
			}
		}
		guard found else{
			sendUkey2Alert(type: .badHandshakeCipher)
			throw NearbyError.ukey2
		}
		guard clientInit.nextProtocol=="AES_256_CBC-HMAC_SHA256" else{
			sendUkey2Alert(type: .badNextProtocol)
			throw NearbyError.ukey2
		}
		
		let domain=Domain.instance(curve: .EC256r1)
		let (pubKey, privKey)=domain.makeKeyPair()
		publicKey=pubKey
		privateKey=privKey
		
		var serverInit=Securegcm_Ukey2ServerInit()
		serverInit.version=1
		serverInit.random=Data.randomData(length: 32)
		serverInit.handshakeCipher = .p256Sha512
		
		var pkey=Securemessage_GenericPublicKey()
		pkey.type = .ecP256
		pkey.ecP256PublicKey=Securemessage_EcP256PublicKey()
		pkey.ecP256PublicKey.x=Data(pubKey.w.x.asSignedBytes())
		pkey.ecP256PublicKey.y=Data(pubKey.w.y.asSignedBytes())
		serverInit.publicKey=try pkey.serializedData()
		
		var serverInitMsg=Securegcm_Ukey2Message()
		serverInitMsg.messageType = .serverInit
		serverInitMsg.messageData=try serverInit.serializedData()
		let serverInitData=try serverInitMsg.serializedData()
		ukeyServerInitMsgData=serverInitData
		sendFrameAsync(serverInitData)
		currentState = .sentUkeyServerInit
	}
	
	private func processUkey2ClientFinish(_ msg:Securegcm_Ukey2Message, raw:Data) throws{
		guard msg.hasMessageType, msg.hasMessageData else { throw NearbyError.requiredFieldMissing("clientFinish ukey2message.type|data") }
		guard case .clientFinish = msg.messageType else { throw NearbyError.ukey2 }
		
		var sha=SHA512()
		sha.update(data: raw)
		guard cipherCommitment==Data(sha.finalize()) else { throw NearbyError.ukey2 }
		
		let clientFinish=try Securegcm_Ukey2ClientFinished(serializedData: msg.messageData)
		guard clientFinish.hasPublicKey else {throw NearbyError.requiredFieldMissing("ukey2clientFinish.publicKey") }
		let clientKey=try Securemessage_GenericPublicKey(serializedData: clientFinish.publicKey)
		
		try finalizeKeyExchange(peerKey: clientKey)
		
		currentState = .receivedUkeyClientFinish
	}
	
	private func processConnectionResponseFrame(_ frame:Location_Nearby_Connections_OfflineFrame) throws{
		guard frame.hasV1, frame.v1.hasType else { throw NearbyError.requiredFieldMissing("offlineFrame.v1.type") }
		if case .connectionResponse = frame.v1.type {
			var resp=Location_Nearby_Connections_OfflineFrame()
			resp.version = .v1
			resp.v1=Location_Nearby_Connections_V1Frame()
			resp.v1.type = .connectionResponse
			resp.v1.connectionResponse=Location_Nearby_Connections_ConnectionResponseFrame()
			resp.v1.connectionResponse.response = .accept
			resp.v1.connectionResponse.status=0
			resp.v1.connectionResponse.osInfo=Location_Nearby_Connections_OsInfo()
			resp.v1.connectionResponse.osInfo.type = .apple
			sendFrameAsync(try resp.serializedData())
			
			encryptionDone=true
			
			var pairedEncryption=Sharing_Nearby_Frame()
			pairedEncryption.version = .v1
			pairedEncryption.v1=Sharing_Nearby_V1Frame()
			pairedEncryption.v1.type = .pairedKeyEncryption
			pairedEncryption.v1.pairedKeyEncryption=Sharing_Nearby_PairedKeyEncryptionFrame()
			// Presumably used for all the phone number stuff that no one needs anyway
			pairedEncryption.v1.pairedKeyEncryption.secretIDHash=Data.randomData(length: 6)
			pairedEncryption.v1.pairedKeyEncryption.signedData=Data.randomData(length: 72)
			try sendTransferSetupFrame(pairedEncryption)
			currentState = .sentConnectionResponse
		} else {
#if DEBUG
			print("Unhandled offline frame plaintext: \(frame)")
#endif
		}
	}
	
	private func processPairedKeyEncryptionFrame(_ frame:Sharing_Nearby_Frame) throws{
		guard frame.hasV1, frame.v1.hasPairedKeyEncryption else { throw NearbyError.requiredFieldMissing("shareNearbyFrame.v1.pairedKeyEncryption") }
		var pairedResult=Sharing_Nearby_Frame()
		pairedResult.version = .v1
		pairedResult.v1=Sharing_Nearby_V1Frame()
		pairedResult.v1.type = .pairedKeyResult
		pairedResult.v1.pairedKeyResult=Sharing_Nearby_PairedKeyResultFrame()
		pairedResult.v1.pairedKeyResult.status = .unable
		try sendTransferSetupFrame(pairedResult)
		currentState = .sentPairedKeyResult
	}
	
	private func processPairedKeyResultFrame(_ frame:Sharing_Nearby_Frame) throws{
		guard frame.hasV1, frame.v1.hasPairedKeyResult else { throw NearbyError.requiredFieldMissing("shareNearbyFrame.v1.pairedKeyResult") }
		currentState = .receivedPairedKeyResult
	}
	
	private func makeFileDestinationURL(_ initialDest:URL) -> URL{
		var dest=initialDest
		if FileManager.default.fileExists(atPath: dest.path){
			var counter=1
			var path:String
			let ext=dest.pathExtension
			let baseUrl=dest.deletingPathExtension()
			repeat{
				path="\(baseUrl.path) (\(counter))"
				if !ext.isEmpty{
					path+=".\(ext)"
				}
				counter+=1
			}while FileManager.default.fileExists(atPath: path)
			dest=URL(fileURLWithPath: path)
		}
		return dest
	}
	
	private func processIntroductionFrame(_ frame:Sharing_Nearby_Frame) throws{
		guard frame.hasV1, frame.v1.hasIntroduction else { throw NearbyError.requiredFieldMissing("shareNearbyFrame.v1.introduction") }
		currentState = .waitingForUserConsent
		if frame.v1.introduction.fileMetadata.count>0 && frame.v1.introduction.textMetadata.isEmpty{
			let downloadsDirectory=(try FileManager.default.url(for: .downloadsDirectory, in: .userDomainMask, appropriateFor: nil, create: true)).resolvingSymlinksInPath()
			do{
				_=try Self.validatedIncomingFileTotalSize(frame.v1.introduction.fileMetadata, availableBytes: Self.availableBytes(for: downloadsDirectory))
			}catch NearbyError.canceled(reason: .notEnoughSpace){
				rejectTransfer(with: .notEnoughSpace)
				return
			}
			for file in frame.v1.introduction.fileMetadata{
				let safeName=FileNameSanitizer.sanitize(file.name)
				let dest=makeFileDestinationURL(downloadsDirectory.appendingPathComponent(safeName))
				let info=InternalFileInfo(meta: FileMetadata(name: safeName, size: file.size, mimeType: file.mimeType),
										  payloadID: file.payloadID,
										  destinationURL: dest)
				transferredFiles[file.payloadID]=info
			}
			let metadata=TransferMetadata(files: transferredFiles.map({$0.value.meta}), id: id, pinCode: pinCode)
			scheduleUserConsentTimeout()
			DispatchQueue.main.async {
				self.delegate?.obtainUserConsent(for: metadata, from: self.remoteDeviceInfo!, connection: self)
			}
			}else if frame.v1.introduction.textMetadata.count==1{
				let meta=frame.v1.introduction.textMetadata[0]
				if case .url=meta.type{
					guard meta.hasPayloadID else { throw NearbyError.requiredFieldMissing("introduction.textMetadata.payloadID") }
					textPayloadID=meta.payloadID
					textPayloadIsURL=true
					let metadata=TransferMetadata(files: [], id: id, pinCode: pinCode, textDescription: meta.textTitle, kind: .url)
					os_log("Incoming URL metadata: id=%{private}@ payload=%{private}@", log: pyontaReceiveLog, type: .info, id, "\(meta.payloadID)")
					scheduleUserConsentTimeout()
					DispatchQueue.main.async {
						self.delegate?.obtainUserConsent(for: metadata, from: self.remoteDeviceInfo!, connection: self)
					}
				}else if case .text=meta.type{
					guard meta.hasPayloadID else { throw NearbyError.requiredFieldMissing("introduction.textMetadata.payloadID") }
					textPayloadID=meta.payloadID
					textPayloadIsURL=false
					let title=meta.textTitle.isEmpty ? NSLocalizedString("ClipboardText", value: "Text", comment: "") : meta.textTitle
					let metadata=TransferMetadata(files: [], id: id, pinCode: pinCode, textDescription: title, kind: .text)
					os_log("Incoming text metadata: id=%{private}@ payload=%{private}@", log: pyontaReceiveLog, type: .info, id, "\(meta.payloadID)")
					scheduleUserConsentTimeout()
					DispatchQueue.main.async {
						self.delegate?.obtainUserConsent(for: metadata, from: self.remoteDeviceInfo!, connection: self)
				}
			}else{
				rejectTransfer(with: .unsupportedAttachmentType)
			}
		}else{
			rejectTransfer(with: .unsupportedAttachmentType)
		}
	}

	static func validatedIncomingFileTotalSize(_ files:[Sharing_Nearby_FileMetadata], availableBytes:Int64?) throws -> Int64 {
		guard files.count <= maximumIncomingFileCount else { throw NearbyError.protocolError("Too many files in introduction") }

		var payloadIDs=Set<Int64>()
		var totalSize:Int64=0
		for file in files {
			guard file.hasPayloadID else { throw NearbyError.requiredFieldMissing("introduction.fileMetadata.payloadID") }
			guard file.hasSize else { throw NearbyError.requiredFieldMissing("introduction.fileMetadata.size") }
			guard file.size >= 0 else { throw NearbyError.protocolError("File size must not be negative") }
			guard payloadIDs.insert(file.payloadID).inserted else { throw NearbyError.protocolError("Duplicate file payload ID") }
			guard file.size <= Int64.max-totalSize else { throw NearbyError.protocolError("Total incoming file size overflow") }
			totalSize+=file.size
		}

		if let availableBytes=availableBytes {
			guard availableBytes > minimumFreeBytesAfterTransfer else { throw NearbyError.canceled(reason: .notEnoughSpace) }
			guard totalSize <= availableBytes-minimumFreeBytesAfterTransfer else { throw NearbyError.canceled(reason: .notEnoughSpace) }
		}
		return totalSize
	}

	private static func availableBytes(for directory:URL) -> Int64? {
		if let values=try? directory.resourceValues(forKeys: [.volumeAvailableCapacityForImportantUsageKey]),
		   let capacity=values.volumeAvailableCapacityForImportantUsage {
			return capacity
		}
		if let attributes=try? FileManager.default.attributesOfFileSystem(forPath: directory.path),
		   let freeSize=attributes[.systemFreeSize] as? NSNumber {
			return freeSize.int64Value
		}
		return nil
	}
	
	func submitUserConsent(accepted:Bool){
		cancelUserConsentTimeout()
		DispatchQueue.global(qos: .utility).async {
			if accepted{
				self.acceptTransfer()
			}else{
				self.rejectTransfer()
			}
		}
	}
	
	private func acceptTransfer(){
		do{
			cancelUserConsentTimeout()
			for (id, file) in transferredFiles{
				FileManager.default.createFile(atPath: file.destinationURL.path, contents: nil)
				let handle=try FileHandle(forWritingTo: file.destinationURL)
				transferredFiles[id]!.fileHandle=handle
				let progress=Progress()
				progress.fileURL=file.destinationURL
				progress.totalUnitCount=file.meta.size
				progress.kind = .file
				progress.isPausable=false
				progress.publish()
				transferredFiles[id]!.progress=progress
				transferredFiles[id]!.created=true
			}
			
			var frame=Sharing_Nearby_Frame()
			frame.version = .v1
			frame.v1.type = .response
			frame.v1.connectionResponse.status = .accept
			currentState = .receivingFiles
			try sendTransferSetupFrame(frame)
		}catch{
			lastError=error
			protocolError()
		}
	}
	
	private func rejectTransfer(with reason:Sharing_Nearby_ConnectionResponseFrame.Status = .reject){
		cancelUserConsentTimeout()
		var frame=Sharing_Nearby_Frame()
		frame.version = .v1
		frame.v1.type = .response
		frame.v1.connectionResponse.status = reason
		do{
			try sendTransferSetupFrame(frame)
			try sendDisconnectionAndDisconnect()
		}catch{
			os_log("Error rejecting incoming transfer: %{private}@", log: pyontaReceiveLog, type: .error, "\(error)")
			protocolError()
		}
	}
	
	private func deletePartiallyReceivedFiles() throws{
		for (_, file) in transferredFiles{
			guard file.created else { continue }
			try FileManager.default.removeItem(at: file.destinationURL)
		}
	}

	private func scheduleUserConsentTimeout(){
		cancelUserConsentTimeout()
		let workItem=DispatchWorkItem { [weak self] in
			guard let self=self else { return }
			guard self.currentState == .waitingForUserConsent else { return }
			os_log("Inbound transfer timed out waiting for user consent: id=%{private}@", log: pyontaReceiveLog, type: .info, self.id)
			self.lastError=NearbyError.canceled(reason: .timedOut)
			self.rejectTransfer(with: .timedOut)
		}
		consentTimeoutWorkItem=workItem
		DispatchQueue.main.asyncAfter(deadline: .now()+Self.userConsentTimeout, execute: workItem)
	}

	private func cancelUserConsentTimeout(){
		consentTimeoutWorkItem?.cancel()
		consentTimeoutWorkItem=nil
	}
}

protocol InboundNearbyConnectionDelegate{
	func obtainUserConsent(for transfer:TransferMetadata, from device:RemoteDeviceInfo, connection:InboundNearbyConnection)
	func connectionWasTerminated(connection:InboundNearbyConnection, error:Error?)
}
