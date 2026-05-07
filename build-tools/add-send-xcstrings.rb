#!/usr/bin/env ruby
# Adds Pyonta/Pyonta/mul.lproj/SendViewController.xcstrings into the existing
# SendViewController.xib PBXVariantGroup so the XIB picks up its localizations
# at build time. Idempotent.
require "xcodeproj"

PROJECT_PATH = File.expand_path("../Pyonta.xcodeproj", __dir__)
project = Xcodeproj::Project.open(PROJECT_PATH)

variant_group = project.objects.find do |obj|
  obj.is_a?(Xcodeproj::Project::Object::PBXVariantGroup) &&
    obj.display_name == "SendViewController.xib"
end

unless variant_group
  abort "ERROR: SendViewController.xib variant group not found"
end

if variant_group.children.any? { |c| c.display_name == "mul" }
  puts "Already linked: mul/SendViewController.xcstrings — nothing to do"
  exit 0
end

mul_ref = project.new(Xcodeproj::Project::Object::PBXFileReference)
mul_ref.last_known_file_type = "text.json.xcstrings"
mul_ref.name = "mul"
mul_ref.path = "mul.lproj/SendViewController.xcstrings"
mul_ref.source_tree = "<group>"

variant_group << mul_ref

project.save
puts "Linked Pyonta/mul.lproj/SendViewController.xcstrings to SendViewController.xib variant group"
