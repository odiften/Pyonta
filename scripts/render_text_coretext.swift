#!/usr/bin/env swift
import AppKit
import Foundation

struct Options {
    var textFile = ""
    var output = ""
    var width: CGFloat = 800
    var fontSize: CGFloat = 48
    var weight = "regular"
    var color = "#18202A"
    var lineSpacing: CGFloat = 12
    var rtl = false
    var alignment = "natural"
}

func parseOptions() -> Options {
    var options = Options()
    var args = Array(CommandLine.arguments.dropFirst())
    while !args.isEmpty {
        let key = args.removeFirst()
        guard !args.isEmpty else { break }
        let value = args.removeFirst()
        switch key {
        case "--text-file": options.textFile = value
        case "--output": options.output = value
        case "--width": options.width = CGFloat(Double(value) ?? Double(options.width))
        case "--font-size": options.fontSize = CGFloat(Double(value) ?? Double(options.fontSize))
        case "--weight": options.weight = value
        case "--color": options.color = value
        case "--line-spacing": options.lineSpacing = CGFloat(Double(value) ?? Double(options.lineSpacing))
        case "--rtl": options.rtl = value == "1" || value.lowercased() == "true"
        case "--alignment": options.alignment = value
        default: break
        }
    }
    return options
}

func nsColor(hex: String) -> NSColor {
    let cleaned = hex.trimmingCharacters(in: CharacterSet(charactersIn: "#"))
    guard cleaned.count == 6, let value = Int(cleaned, radix: 16) else {
        return NSColor(calibratedRed: 0.09, green: 0.13, blue: 0.16, alpha: 1)
    }
    let r = CGFloat((value >> 16) & 0xff) / 255.0
    let g = CGFloat((value >> 8) & 0xff) / 255.0
    let b = CGFloat(value & 0xff) / 255.0
    return NSColor(calibratedRed: r, green: g, blue: b, alpha: 1)
}

func fontWeight(_ value: String) -> NSFont.Weight {
    switch value {
    case "bold": return .bold
    case "medium": return .medium
    default: return .regular
    }
}

let options = parseOptions()
guard !options.textFile.isEmpty, !options.output.isEmpty else {
    FileHandle.standardError.write(Data("Missing --text-file or --output\n".utf8))
    exit(2)
}

let text = (try NSString(contentsOfFile: options.textFile, encoding: String.Encoding.utf8.rawValue)) as String
let paragraph = NSMutableParagraphStyle()
paragraph.lineBreakMode = .byWordWrapping
paragraph.lineSpacing = options.lineSpacing
switch options.alignment {
case "center":
    paragraph.alignment = .center
case "right":
    paragraph.alignment = .right
case "left":
    paragraph.alignment = .left
default:
    paragraph.alignment = options.rtl ? .right : .natural
}
paragraph.baseWritingDirection = options.rtl ? .rightToLeft : .natural

let font = NSFont.systemFont(ofSize: options.fontSize, weight: fontWeight(options.weight))
let attrs: [NSAttributedString.Key: Any] = [
    .font: font,
    .foregroundColor: nsColor(hex: options.color),
    .paragraphStyle: paragraph,
]
let attributed = NSAttributedString(string: text, attributes: attrs)
let bounds = attributed.boundingRect(
    with: NSSize(width: options.width, height: CGFloat.greatestFiniteMagnitude),
    options: [.usesLineFragmentOrigin, .usesFontLeading]
)
let height = max(ceil(bounds.height + options.lineSpacing + 8), options.fontSize + 12)
let image = NSImage(size: NSSize(width: options.width, height: height))
image.lockFocus()
NSColor.clear.setFill()
NSRect(x: 0, y: 0, width: options.width, height: height).fill()
attributed.draw(
    with: NSRect(x: 0, y: 0, width: options.width, height: height),
    options: [.usesLineFragmentOrigin, .usesFontLeading]
)
image.unlockFocus()

guard
    let tiff = image.tiffRepresentation,
    let bitmap = NSBitmapImageRep(data: tiff),
    let png = bitmap.representation(using: .png, properties: [:])
else {
    FileHandle.standardError.write(Data("Could not render text image\n".utf8))
    exit(3)
}
try png.write(to: URL(fileURLWithPath: options.output))
