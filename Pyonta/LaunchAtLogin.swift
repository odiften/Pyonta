//
//  LaunchAtLogin.swift
//  Pyonta
//
//  macOS 13.0+ の SMAppService.mainApp で「ログイン時に自動起動」を切り替える
//  最小ラッパー。永続化は OS 側 (SMAppService) が持つので UserDefaults は使わない。
//
//  Pyonta 自前実装（QuickDrop が依存している sindresorhus/LaunchAtLogin-Modern とは独立）。
//

import Foundation
import ServiceManagement

@available(macOS 13.0, *)
enum LaunchAtLogin {
	/// 現在の「ログイン時起動」設定状態。
	static var isEnabled: Bool {
		SMAppService.mainApp.status == .enabled
	}

	/// ログイン時起動を有効/無効に切り替える。SMAppService の例外は飲み込んでログだけ出す。
	static func setEnabled(_ enabled: Bool) {
		do {
			if enabled {
				// 既に登録済の場合は一度解除してから登録し直す（QuickDrop が依存している
				// LaunchAtLogin-Modern と同パターン、状態が壊れている時の復旧用）
				if SMAppService.mainApp.status == .enabled {
					try? SMAppService.mainApp.unregister()
				}
				try SMAppService.mainApp.register()
			} else {
				try SMAppService.mainApp.unregister()
			}
		} catch {
			NSLog("[Pyonta] LaunchAtLogin.setEnabled(\(enabled)) failed: \(error.localizedDescription)")
		}
	}
}
