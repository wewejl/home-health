#!/usr/bin/env ruby
# frozen_string_literal: true

require 'xcodeproj'

# 项目路径
project_path = 'xinlingyisheng.xcodeproj'

# 打开项目
project = Xcodeproj::Project.open(project_path)

# 获取主 Target
main_target = project.targets.find { |t| t.name == '灵犀医生' }
raise "找不到主 Target '灵犀医生'" unless main_target

# UI Test Target 名称
ui_test_target_name = 'xinlingyishengUITests'

# 检查是否已存在
existing = project.targets.find { |t| t.name == ui_test_target_name }
if existing
  puts "UI Test Target '#{ui_test_target_name}' 已存在"
  exit 0
end

puts "正在添加 UI Test Target '#{ui_test_target_name}'..."

# 创建 UI Test Target
ui_test_target = project.new_target(:ui_test_bundle, ui_test_target_name, :ios)

# 配置 Debug build settings
debug_config = ui_test_target.build_configurations.find { |c| c.name == 'Debug' }
debug_config.build_settings['TARGETED_DEVICE_FAMILY'] = '1'
debug_config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '18.0'
debug_config.build_settings['TEST_TARGET_NAME'] = '灵犀医生'
debug_config.build_settings['PRODUCT_BUNDLE_IDENTIFIER'] = 'xinlin.xinlingyishengUITests'
debug_config.build_settings['SWIFT_VERSION'] = '5.0'

# 配置 Release build settings
release_config = ui_test_target.build_configurations.find { |c| c.name == 'Release' }
release_config.build_settings['TARGETED_DEVICE_FAMILY'] = '1'
release_config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '18.0'
release_config.build_settings['TEST_TARGET_NAME'] = '灵犀医生'
release_config.build_settings['PRODUCT_BUNDLE_IDENTIFIER'] = 'xinlin.xinlingyishengUITests'
release_config.build_settings['SWIFT_VERSION'] = '5.0'

# 添加依赖关系
ui_test_target.add_dependency(main_target)

# 创建 xinlingyishengUITests 文件组
ui_tests_group = project.main_group.find_subpath('xinlingyishengUITests')
if ui_tests_group.nil?
  ui_tests_group = project.main_group.new_group('xinlingyishengUITests')
end

# 为 UI Test Target 添加文件系统同步组
# 注意: Xcode 26.2 使用 PBXFileSystemSynchronizedRootGroup
ui_test_fs_group = project.new(Xcodeproj::Project::PBXFileSystemSynchronizedRootGroup)
ui_test_fs_group.name = 'xinlingyishengUITests'
ui_test_fs_group.path = 'xinlingyishengUITests'
ui_test_fs_group.source_tree = '<group>'

# 将文件系统同步组添加到主项目组
project.main_group << ui_test_fs_group

# 设置 UI Test Target 的 fileSystemSynchronizedGroups
ui_test_target.fileSystemSynchronizedGroups = [ui_test_fs_group]

# 保存项目
project.save

puts "✅ UI Test Target '#{ui_test_target_name}' 添加成功!"
puts ""
puts "下一步:"
puts "1. 运行: xcodebuild -project xinlingyisheng.xcodeproj -list"
puts "2. 运行测试: xcodebuild test -project xinlingyisheng.xcodeproj -scheme 灵犀医生 -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -only-testing:xinlingyishengUITests"
