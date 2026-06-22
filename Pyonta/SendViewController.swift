//
//  SendViewController.swift
//  Pyonta
//
//  ShareExtension/ShareViewController.swift をベースに、Mac→Android 送信 UI を
//  本体メニューバー (Send files… / Send clipboard…) からも使えるようにした版。
//  XIB レイアウトは ShareExtension の SendViewController.xib（コピー）を共有。
//

import Foundation
import Cocoa
import NearbyShare
import QRCode
import os.log

fileprivate let pyontaSendViewLog = OSLog(subsystem: "com.odiften.pyonta", category: "send-ui")

class SendViewController: NSViewController, ShareExtensionDelegate {

	enum Mode {
		case urls([URL])
		case text(String, isURL: Bool)
	}

	private let mode:Mode
	private var foundDevices:[RemoteDeviceInfo]=[]
	private var chosenDevice:RemoteDeviceInfo?
	private var lastError:Error?
	private var sheetWindow:NSWindow?
	private var discoveryActive=false

	@IBOutlet var filesIcon:NSImageView?
	@IBOutlet var filesLabel:NSTextField?
	@IBOutlet var loadingOverlay:NSStackView?
	@IBOutlet var largeProgress:NSProgressIndicator?
	@IBOutlet var listView:NSCollectionView?
	@IBOutlet var listViewWrapper:NSView?
	@IBOutlet var contentWrap:NSView?
	@IBOutlet var progressView:NSView?
	@IBOutlet var progressDeviceIcon:NSImageView?
	@IBOutlet var progressDeviceName:NSTextField?
	@IBOutlet var progressProgressBar:NSProgressIndicator?
	@IBOutlet var progressState:NSTextField?
	@IBOutlet var progressDeviceIconWrap:NSView?
	@IBOutlet var progressDeviceSecondaryIcon:NSImageView?
	@IBOutlet var qrCodeButton:NSButton?

	@IBOutlet var qrCodeSheetView:NSView?
	@IBOutlet var qrCodeView:NSImageView?
	@IBOutlet var qrCodeWrapView:NSView?

	override var nibName: NSNib.Name? {
		return NSNib.Name("SendViewController")
	}

	init(urls:[URL]) {
		self.mode = .urls(urls)
		super.init(nibName: nil, bundle: nil)
	}

	init(text:String, isURL:Bool) {
		self.mode = .text(text, isURL: isURL)
		super.init(nibName: nil, bundle: nil)
	}

	required init?(coder: NSCoder) {
		fatalError("init(coder:) has not been implemented")
	}

	override func loadView() {
		super.loadView()

		contentWrap!.addSubview(listViewWrapper!)
		contentWrap!.addSubview(loadingOverlay!)
		contentWrap!.addSubview(progressView!)
		progressView!.isHidden=true

		listViewWrapper!.translatesAutoresizingMaskIntoConstraints=false
		loadingOverlay!.translatesAutoresizingMaskIntoConstraints=false
		progressView!.translatesAutoresizingMaskIntoConstraints=false
		NSLayoutConstraint.activate([
			NSLayoutConstraint(item: listViewWrapper!, attribute: .width, relatedBy: .equal, toItem: contentWrap, attribute: .width, multiplier: 1, constant: 0),
			NSLayoutConstraint(item: listViewWrapper!, attribute: .height, relatedBy: .equal, toItem: contentWrap, attribute: .height, multiplier: 1, constant: 0),

			NSLayoutConstraint(item: loadingOverlay!, attribute: .width, relatedBy: .equal, toItem: contentWrap, attribute: .width, multiplier: 1, constant: 0),
			NSLayoutConstraint(item: loadingOverlay!, attribute: .centerY, relatedBy: .equal, toItem: contentWrap, attribute: .centerY, multiplier: 1, constant: 0),

			NSLayoutConstraint(item: progressView!, attribute: .width, relatedBy: .equal, toItem: contentWrap, attribute: .width, multiplier: 1, constant: 0),
			NSLayoutConstraint(item: progressView!, attribute: .centerY, relatedBy: .equal, toItem: contentWrap, attribute: .centerY, multiplier: 1, constant: 0)
		])

		largeProgress!.startAnimation(nil)
		let flowLayout=NSCollectionViewFlowLayout()
		flowLayout.itemSize=NSSize(width: 75, height: 90)
		flowLayout.sectionInset=NSEdgeInsets(top: 10, left: 10, bottom: 10, right: 10)
		flowLayout.minimumInteritemSpacing=10
		flowLayout.minimumLineSpacing=10
		listView!.collectionViewLayout=flowLayout
		listView!.dataSource=self

		progressDeviceIconWrap!.wantsLayer=true
		progressDeviceIconWrap!.layer!.masksToBounds=false

		qrCodeWrapView!.wantsLayer=true
		qrCodeWrapView!.layer!.masksToBounds=false
		qrCodeWrapView!.layer!.shadowColor = .black
		qrCodeWrapView!.layer!.shadowOpacity=0.3
		qrCodeWrapView!.layer!.shadowRadius=12
		qrCodeWrapView!.layer!.shadowOffset=CGSizeMake(0, -5)

		applyHeader()
	}

	override func viewDidLoad(){
		super.viewDidLoad()
		NearbyConnectionManager.shared.startDeviceDiscovery()
		discoveryActive=true
		NearbyConnectionManager.shared.addShareExtensionDelegate(self)
		scheduleAutomaticQrCodeView()
	}

	private func scheduleAutomaticQrCodeView() {
		DispatchQueue.main.asyncAfter(deadline: .now()+10.0) { [weak self] in
			guard let self=self else { return }
			if self.foundDevices.isEmpty && self.sheetWindow==nil && self.chosenDevice==nil {
				os_log("Auto-opening QR code after discovery fallback delay", log: pyontaSendViewLog, type: .info)
				self.useQrCode(nil)
			}
		}
	}

	override func viewWillDisappear() {
		if chosenDevice==nil{
			stopDiscoveryIfNeeded()
		}
		NearbyConnectionManager.shared.removeShareExtensionDelegate(self)
	}

	private func stopDiscoveryIfNeeded(){
		guard discoveryActive else { return }
		NearbyConnectionManager.shared.stopDeviceDiscovery()
		discoveryActive=false
	}

	@IBAction func cancel(_ sender: AnyObject?) {
		if let device=chosenDevice{
			NearbyConnectionManager.shared.cancelOutgoingTransfer(id: device.id!)
		}
		view.window?.close()
	}

	@IBAction func useQrCode(_ sender: AnyObject?) {
		os_log("Opening QR code sheet", log: pyontaSendViewLog, type: .info)
		let window=contentWrap!.window!
		let sheetWindow=NSWindow()
		sheetWindow.contentView=qrCodeSheetView!
		let size=NSSize(width: 380, height: 400)
		sheetWindow.contentMaxSize=size
		sheetWindow.contentMinSize=size
		sheetWindow.setContentSize(size)

		let qrKey=NearbyConnectionManager.shared.generateQrCodeKey()
		let qrCodeImage=try! QRCode.build
			.text("https://quickshare.google/qrcode#key=\(qrKey)")
			.backgroundColor(CGColor(srgbRed: 1, green: 1, blue: 1, alpha: 0))
			.quietZonePixelCount(3)
			.onPixels.shape(.circle())
			.eye.shape(.roundedPointing())
			.errorCorrection(.low)
			.generate.image(dimension: Int(qrCodeView!.frame.width)*2)
		qrCodeView!.image=NSImage(cgImage: qrCodeImage, size: qrCodeImage.size)

		self.sheetWindow=sheetWindow
		window.beginSheet(sheetWindow) { response in
			self.sheetWindow=nil
		}
	}

	@IBAction func dismissQrCodeSheet(_ sender: AnyObject?){
		contentWrap!.window!.endSheet(sheetWindow!)
		sheetWindow=nil
	}

	private func applyHeader(){
		switch mode {
		case .urls(let urls):
			if urls.count==1 {
				if urls[0].isFileURL {
					filesLabel!.stringValue=urls[0].lastPathComponent
					filesIcon!.image=NSWorkspace.shared.icon(forFile: urls[0].path)
				}else if urls[0].scheme=="http" || urls[0].scheme=="https" {
					filesLabel!.stringValue=urls[0].absoluteString
					filesIcon!.image=NSImage(named: NSImage.networkName)
				}
			}else{
				filesLabel!.stringValue=String.localizedStringWithFormat(NSLocalizedString("NFiles", value: "%d files", comment: ""), urls.count)
				filesIcon!.image=NSImage(named: NSImage.multipleDocumentsName)
			}
		case .text(let text, let isURL):
			let preview=text.replacingOccurrences(of: "\n", with: " ")
			filesLabel!.stringValue=preview.count > 60 ? String(preview.prefix(60))+"…" : preview
			if isURL {
				filesIcon!.image=NSImage(named: NSImage.networkName)
			}else if #available(macOS 11.0, *) {
				filesIcon!.image=NSImage(systemSymbolName: "doc.plaintext", accessibilityDescription: nil)
			}else{
				filesIcon!.image=NSImage(named: NSImage.multipleDocumentsName)
			}
		}
	}

	func addDevice(device: RemoteDeviceInfo) {
		if foundDevices.isEmpty{
			loadingOverlay?.animator().isHidden=true
		}
		foundDevices.append(device)
		listView?.animator().insertItems(at: [[0, foundDevices.count-1]])
	}

	func updateDevice(device: RemoteDeviceInfo) {
		for i in foundDevices.indices {
			if foundDevices[i].id==device.id {
				foundDevices[i]=device
				listView?.animator().reloadItems(at: [[0, i]])
				break
			}
		}
	}

	func removeDevice(id: String){
		if chosenDevice != nil{
			return
		}
		for i in foundDevices.indices{
			if foundDevices[i].id==id{
				foundDevices.remove(at: i)
				listView?.animator().deleteItems(at: [[0, i]])
				break
			}
		}
		if foundDevices.isEmpty{
			loadingOverlay?.animator().isHidden=false
		}
	}

	func startTransferWithQrCode(device: RemoteDeviceInfo){
		dismissQrCodeSheet(nil)
		selectDevice(device: device)
	}

	func connectionWasEstablished(pinCode: String) {
		progressState?.stringValue=String(format:NSLocalizedString("PinCode", value: "PIN: %@", comment: ""), arguments: [pinCode])
		progressProgressBar?.isIndeterminate=false
		progressProgressBar?.maxValue=1000
		progressProgressBar?.doubleValue=0
	}

	func connectionFailed(with error: Error) {
		progressProgressBar?.isIndeterminate=false
		progressProgressBar?.maxValue=1000
		progressProgressBar?.doubleValue=0
		lastError=error
		PyontaDiagnostics.recordOutgoing(kind: diagnosticContentKind, fileCount: diagnosticFileCount, error: error)
		if let ne=(error as? NearbyError), case let .canceled(reason)=ne{
			switch reason{
			case .userRejected:
				progressState?.stringValue=NSLocalizedString("TransferDeclined", value: "Declined", comment: "")
			case .userCanceled:
				progressState?.stringValue=NSLocalizedString("TransferCanceled", value: "Canceled", comment: "")
			case .notEnoughSpace:
				progressState?.stringValue=NSLocalizedString("NotEnoughSpace", value: "Not enough disk space", comment: "")
			case .unsupportedType:
				progressState?.stringValue=NSLocalizedString("UnsupportedType", value: "Attachment type not supported", comment: "")
			case .timedOut:
				progressState?.stringValue=NSLocalizedString("TransferTimedOut", value: "Timed out", comment: "")
			}
			progressDeviceSecondaryIcon?.isHidden=false
			dismissDelayed()
		}else{
			let alert=sendFailureAlert(for: error)
			alert.beginSheetModal(for: view.window!) { resp in
				self.view.window?.close()
			}
		}
	}

	func transferAccepted() {
		progressState?.stringValue=NSLocalizedString("Sending", value: "Sending...", comment: "")
	}

	func transferProgress(progress: Double) {
		progressProgressBar!.doubleValue=progress*progressProgressBar!.maxValue
	}

	func transferFinished() {
		progressState?.stringValue=NSLocalizedString("TransferFinished", value: "Transfer finished", comment: "")
		PyontaDiagnostics.recordOutgoing(kind: diagnosticContentKind, fileCount: diagnosticFileCount, error: nil)
		dismissDelayed()
	}

	func selectDevice(device:RemoteDeviceInfo){
		chosenDevice=device
		stopDiscoveryIfNeeded()
		listViewWrapper?.animator().isHidden=true
		progressView?.animator().isHidden=false
		qrCodeButton?.animator().isHidden=true
		progressDeviceName?.stringValue=device.name
		progressDeviceIcon?.image=imageForDeviceType(type: device.type)
		progressProgressBar?.startAnimation(nil)
		progressState?.stringValue=NSLocalizedString("Connecting", value: "Connecting...", comment: "")
		switch mode {
		case .urls(let urls):
			NearbyConnectionManager.shared.startOutgoingTransfer(deviceID: device.id!, delegate: self, urls: urls)
		case .text(let text, let isURL):
			NearbyConnectionManager.shared.startOutgoingTransfer(deviceID: device.id!, delegate: self, text: text, isURL: isURL)
		}
	}

	private func dismissDelayed(){
		DispatchQueue.main.asyncAfter(deadline: .now()+2.0){ [weak self] in
			self?.view.window?.close()
		}
	}

	private func sendFailureAlert(for error:Error) -> NSAlert {
		let alert=NSAlert()
		let deviceName=chosenDevice?.name ?? NSLocalizedString("UnknownAndroidDevice", value: "Android device", comment: "")
		alert.messageText=String(format: NSLocalizedString("SendError.Title", value: "Could not send to %@", comment: ""), arguments: [deviceName])
		alert.informativeText=userFacingSendFailureMessage(for: error)
		alert.addButton(withTitle: "OK")
		return alert
	}

	private func userFacingSendFailureMessage(for error:Error) -> String {
		if let nearbyError=error as? NearbyError {
			if case .canceled = nearbyError {
				return error.localizedDescription
			}
			return NSLocalizedString("SendError.RetryQuickShare", value: "Quick Share could not complete the transfer. Open Quick Share on the Android device and try again.", comment: "")
		}
		return error.localizedDescription
	}

	private var diagnosticContentKind: PyontaDiagnostics.ContentKind {
		switch mode {
		case .urls(let urls):
			if urls.count==1, let scheme=urls[0].scheme?.lowercased(), scheme=="http" || scheme=="https" {
				return .url
			}
			return .files
		case .text(_, let isURL):
			return isURL ? .url : .text
		}
	}

	private var diagnosticFileCount: Int {
		switch mode {
		case .urls(let urls):
			return diagnosticContentKind == .files ? urls.count : 0
		case .text:
			return 0
		}
	}
}

fileprivate func imageForDeviceType(type:RemoteDeviceInfo.DeviceType)->NSImage{
	let imageName:String
	switch type{
	case .tablet:
		imageName="com.apple.ipad"
	case .computer:
		imageName="com.apple.macbookpro-13-unibody"
	default: // also .phone
		imageName="com.apple.iphone"
	}
	return NSImage(contentsOfFile: "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/\(imageName).icns")!
}

extension SendViewController: NSCollectionViewDataSource{
	func numberOfSections(in collectionView: NSCollectionView) -> Int {
		return 1
	}

	func collectionView(_ collectionView: NSCollectionView, numberOfItemsInSection section: Int) -> Int {
		return foundDevices.count
	}

	func collectionView(_ collectionView: NSCollectionView, itemForRepresentedObjectAt indexPath: IndexPath) -> NSCollectionViewItem {
		let item=collectionView.makeItem(withIdentifier: NSUserInterfaceItemIdentifier(rawValue: "DeviceListCell"), for: indexPath)
		guard let collectionViewItem = item as? DeviceListCell else {return item}
		let device=foundDevices[indexPath[1]]
		collectionViewItem.textField?.stringValue=device.name
		collectionViewItem.imageView?.image=imageForDeviceType(type: device.type)
		collectionViewItem.clickHandler={
			self.selectDevice(device: device)
		}
		return collectionViewItem
	}
}
