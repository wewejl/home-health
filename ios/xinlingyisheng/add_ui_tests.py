#!/usr/bin/env python3
"""
脚本: 为 Xcode 项目添加 UI Testing Target
适用于: Xcode 26.2 (objectVersion = 77) 使用 PBXFileSystemSynchronizedRootGroup
"""

import uuid
import re

# 生成唯一的 24 字符十六进制 ID (类似 Xcode 格式)
def generate_uuid():
    return f"9E{uuid.uuid4().hex[:22].upper()}"

# 项目文件路径
project_file = "xinlingyisheng.xcodeproj/project.pbxproj"

# 读取项目文件
with open(project_file, 'r', encoding='utf-8') as f:
    content = f.read()

# ===== 生成新的 UUID =====
uitests_target_uuid = generate_uuid()
uitests_product_uuid = generate_uuid()
uitests_fs_group_uuid = generate_uuid()
uitests_sources_uuid = generate_uuid()
uitests_config_list_uuid = generate_uuid()
uitests_debug_config_uuid = generate_uuid()
uitests_release_config_uuid = generate_uuid()
uitests_target_dependency_uuid = generate_uuid()

# 主应用 Target UUID (从文件中提取)
main_target_uuid = "9E28CE022EFEA293000EC906"

# ===== 1. 在 PBXFileReference section 添加 UI Tests 产品引用 =====
app_ref_line = '\t\t9E28CE032EFEA293000EC906 /* 灵犀医生.app */ = {isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = "灵犀医生.app"; sourceTree = BUILT_PRODUCTS_DIR; };'
new_app_ref = app_ref_line + '\n\t\t' + uitests_product_uuid + ' /* xinlingyishengUITests.xctest */ = {isa = PBXFileReference; explicitFileType = wrapper.cfbundle; includeInIndex = 0; path = xinlingyishengUITests.xctest; sourceTree = BUILT_PRODUCTS_DIR; };'
content = content.replace(app_ref_line, new_app_ref)

# ===== 2. 在 PBXFileSystemSynchronizedRootGroup section 添加 UI Tests 组 =====
old_fs_group = '\t\t9E28CE052EFEA293000EC906 /* xinlingyisheng */ = {\n\t\t\tisa = PBXFileSystemSynchronizedRootGroup;\n\t\t\texceptions = (\n\t\t\t\t9E28CE112EFEA295000EC906 /* Exceptions for "xinlingyisheng" folder in "灵犀医生" target */,\n\t\t\t);\n\t\t\tpath = xinlingyisheng;\n\t\t\tsourceTree = "<group>";\n\t\t};'

new_fs_group = '\t\t' + uitests_fs_group_uuid + ' /* xinlingyishengUITests */ = {\n\t\t\tisa = PBXFileSystemSynchronizedRootGroup;\n\t\t\texceptions = (\n\t\t\t);\n\t\t\tpath = xinlingyishengUITests;\n\t\t\tsourceTree = "<group>";\n\t\t};'

content = content.replace(old_fs_group, old_fs_group + '\n' + new_fs_group)

# ===== 3. 在 PBXGroup section 的 Products 组添加 UI Tests 产品 =====
products_group = '\t\t9E28CE042EFEA293000EC906 /* Products */ = {\n\t\t\tisa = PBXGroup;\n\t\t\tchildren = (\n\t\t\t\t9E28CE032EFEA293000EC906 /* 灵犀医生.app */,\n\t\t\t);\n\t\t\tname = Products;\n\t\t\tsourceTree = "<group>";\n\t\t};'

new_products_group = '\t\t9E28CE042EFEA293000EC906 /* Products */ = {\n\t\t\tisa = PBXGroup;\n\t\t\tchildren = (\n\t\t\t\t9E28CE032EFEA293000EC906 /* 灵犀医生.app */,\n\t\t\t\t' + uitests_product_uuid + ' /* xinlingyishengUITests.xctest */,\n\t\t\t);\n\t\t\tname = Products;\n\t\t\tsourceTree = "<group>";\n\t\t};'

content = content.replace(products_group, new_products_group)

# ===== 4. 在主组添加 xinlingyishengUITests 文件系统同步组 =====
main_group = '\t\t9E28CDFA2EFEA293000EC906 = {\n\t\t\tisa = PBXGroup;\n\t\t\tchildren = (\n\t\t\t\t9E28CE052EFEA293000EC906 /* xinlingyisheng */,\n\t\t\t\t9E28CE042EFEA293000EC906 /* Products */,\n\t\t\t);\n\t\t\tsourceTree = "<group>";\n\t\t};'

new_main_group = '\t\t9E28CDFA2EFEA293000EC906 = {\n\t\t\tisa = PBXGroup;\n\t\t\tchildren = (\n\t\t\t\t9E28CE052EFEA293000EC906 /* xinlingyisheng */,\n\t\t\t\t' + uitests_fs_group_uuid + ' /* xinlingyishengUITests */,\n\t\t\t\t9E28CE042EFEA293000EC906 /* Products */,\n\t\t\t);\n\t\t\tsourceTree = "<group>";\n\t\t};'

content = content.replace(main_group, new_main_group)

# ===== 5. 添加 PBXSourcesBuildPhase =====
sources_phase = '\t\t' + uitests_sources_uuid + ' /* Sources */ = {\n\t\t\tisa = PBXSourcesBuildPhase;\n\t\t\tbuildActionMask = 2147483647;\n\t\t\tfiles = (\n\t\t\t);\n\t\t\trunOnlyForDeploymentPostprocessing = 0;\n\t\t};'

resources_section_end = '/* End PBXResourcesBuildPhase section */'
content = content.replace(resources_section_end, resources_section_end + '\n\n/* Begin PBXSourcesBuildPhase section */\n' + sources_phase + '\n/* End PBXSourcesBuildPhase section */')

# ===== 6. 添加 PBXNativeTarget section =====
native_target = '\t\t' + uitests_target_uuid + ' /* xinlingyishengUITests */ = {\n\t\t\tisa = PBXNativeTarget;\n\t\t\tbuildConfigurationList = ' + uitests_config_list_uuid + ' /* Build configuration list for PBXNativeTarget "xinlingyishengUITests" */;\n\t\t\tbuildPhases = (\n\t\t\t\t' + uitests_sources_uuid + ' /* Sources */,\n\t\t\t);\n\t\t\tbuildRules = (\n\t\t\t);\n\t\t\tdependencies = (\n\t\t\t\t' + uitests_target_dependency_uuid + ' /* PBXTargetDependency */,\n\t\t\t);\n\t\t\tfileSystemSynchronizedGroups = (\n\t\t\t\t' + uitests_fs_group_uuid + ' /* xinlingyishengUITests */,\n\t\t\t);\n\t\t\tname = xinlingyishengUITests;\n\t\t\tproductName = xinlingyishengUITests;\n\t\t\tproductReference = ' + uitests_product_uuid + ' /* xinlingyishengUITests.xctest */;\n\t\t\tproductType = "com.apple.product-type.bundle.ui-testing";\n\t\t};'

# 在灵犀医生 target 结束后添加
old_native_target_end = '\t\t};\n/* End PBXNativeTarget section */'
content = content.replace(old_native_target_end, '\t\t};\n' + native_target + '\n/* End PBXNativeTarget section */')

# ===== 7. 添加 PBXTargetDependency =====
target_dependency = '\t\t' + uitests_target_dependency_uuid + ' /* PBXTargetDependency */ = {\n\t\t\tisa = PBXTargetDependency;\n\t\t\ttarget = ' + main_target_uuid + ' /* 灵犀医生 */;\n\t\t};'

project_section_start = '/* Begin PBXProject section */'
content = content.replace(project_section_start, '/* Begin PBXTargetDependency section */\n' + target_dependency + '\n/* End PBXTargetDependency section */\n\n' + project_section_start)

# ===== 8. 在 PBXProject 的 targets 数组添加 UI Tests target =====
targets_array = '\t\t\ttargets = (\n\t\t\t\t9E28CE022EFEA293000EC906 /* 灵犀医生 */,\n\t\t\t);'
new_targets_array = '\t\t\ttargets = (\n\t\t\t\t9E28CE022EFEA293000EC906 /* 灵犀医生 */,\n\t\t\t\t' + uitests_target_uuid + ' /* xinlingyishengUITests */,\n\t\t\t);'
content = content.replace(targets_array, new_targets_array)

# ===== 9. 添加 UI Tests 的 XCBuildConfiguration =====
# Debug 配置
uitests_debug_config = '\t\t' + uitests_debug_config_uuid + ' /* Debug */ = {\n\t\t\tisa = XCBuildConfiguration;\n\t\t\tbuildSettings = {\n\t\t\t\tALWAYS_EMBED_SWIFT_STANDARD_LIBRARIES = YES;\n\t\t\t\tCODE_SIGN_STYLE = Automatic;\n\t\t\t\tDEVELOPMENT_TEAM = YN6Y9MLCZR;\n\t\t\t\tENABLE_PREVIEWS = YES;\n\t\t\t\tGENERATE_INFOPLIST_FILE = YES;\n\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 18.0;\n\t\t\t\tMARKETING_VERSION = 1.0.3;\n\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = xinlin.xinlingyishengUITests;\n\t\t\t\tPRODUCT_NAME = "$(TARGET_NAME)";\n\t\t\t\tSWIFT_VERSION = 5.0;\n\t\t\t\tTARGETED_DEVICE_FAMILY = 1;\n\t\t\t\tTEST_TARGET_NAME = "灵犀医生";\n\t\t\t};\n\t\t\tname = Debug;\n\t\t};'

# Release 配置
uitests_release_config = '\t\t' + uitests_release_config_uuid + ' /* Release */ = {\n\t\t\tisa = XCBuildConfiguration;\n\t\t\tbuildSettings = {\n\t\t\t\tALWAYS_EMBED_SWIFT_STANDARD_LIBRARIES = YES;\n\t\t\t\tCODE_SIGN_STYLE = Automatic;\n\t\t\t\tDEVELOPMENT_TEAM = YN6Y9MLCZR;\n\t\t\t\tENABLE_PREVIEWS = YES;\n\t\t\t\tGENERATE_INFOPLIST_FILE = YES;\n\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 18.0;\n\t\t\t\tMARKETING_VERSION = 1.0.3;\n\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = xinlin.xinlingyishengUITests;\n\t\t\t\tPRODUCT_NAME = "$(TARGET_NAME)";\n\t\t\t\tSWIFT_VERSION = 5.0;\n\t\t\t\tTARGETED_DEVICE_FAMILY = 1;\n\t\t\t\tTEST_TARGET_NAME = "灵犀医生";\n\t\t\t};\n\t\t\tname = Release;\n\t\t};'

config_list_section_start = '/* Begin XCConfigurationList section */'
new_configs = '/* Begin XCBuildConfiguration section */\n' + uitests_debug_config + '\n' + uitests_release_config + '\n/* End XCBuildConfiguration section */\n\n' + config_list_section_start
content = content.replace(config_list_section_start, new_configs)

# ===== 10. 添加 UI Tests 的 XCConfigurationList =====
uitests_config_list = '\t\t' + uitests_config_list_uuid + ' /* Build configuration list for PBXNativeTarget "xinlingyishengUITests" */ = {\n\t\t\tisa = XCConfigurationList;\n\t\t\tbuildConfigurations = (\n\t\t\t\t' + uitests_debug_config_uuid + ' /* Debug */,\n\t\t\t\t' + uitests_release_config_uuid + ' /* Release */,\n\t\t\t);\n\t\t\tdefaultConfigurationIsVisible = 0;\n\t\t\tdefaultConfigurationName = Release;\n\t\t};'

config_list_section_end = '/* End XCConfigurationList section */'
content = content.replace(config_list_section_end, uitests_config_list + '\n' + config_list_section_end)

# 写入修改后的内容
with open(project_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ UI Test Target 添加成功!")
print("")
print("生成的 UUID:")
print(f"  - Target: {uitests_target_uuid}")
print(f"  - Product: {uitests_product_uuid}")
print(f"  - FS Group: {uitests_fs_group_uuid}")
print(f"  - Sources: {uitests_sources_uuid}")
print("")
print("下一步:")
print("1. 验证: xcodebuild -project xinlingyisheng.xcodeproj -list")
print("2. 测试: xcodebuild test -project xinlingyisheng.xcodeproj -scheme 灵犀医生 -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -only-testing:xinlingyishengUITests")
