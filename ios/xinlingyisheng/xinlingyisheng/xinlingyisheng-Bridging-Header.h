//
//  xinlingyisheng-Bridging-Header.h
//  xinlingyisheng
//
//  Swift - Objective-C 桥接头文件
//  用于引入阿里云号码认证 SDK
//

#ifndef xinlingyisheng_Bridging_Header_h
#define xinlingyisheng_Bridging_Header_h

// 阿里云号码认证 SDK (ATAuthSDK)
// 注意：SDK 文件已复制到 frameworks 目录，需要在 Xcode 中添加到项目
#if __has_include(<ATAuthSDK/ATAuthSDK.h>)
#import <ATAuthSDK/ATAuthSDK.h>
#endif

// 阿里云号码认证 SDK (YTXOperators)
#if __has_include(<YTXOperators/YTXOperators.h>)
#import <YTXOperators/YTXOperators.h>
#endif

// 阿里云号码认证 SDK (YTXMonitor)
#if __has_include(<YTXMonitor/YTXMonitor.h>)
#import <YTXMonitor/YTXMonitor.h>
#endif

#endif /* xinlingyisheng_Bridging_Header_h */
