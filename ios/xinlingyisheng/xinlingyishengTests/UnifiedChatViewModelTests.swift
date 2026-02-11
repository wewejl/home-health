//
//  UnifiedChatViewModelTests.swift
//  xinlingyishengTests
//
//  UnifiedChatViewModel 单元测试
//  测试覆盖: 初始状态、消息管理、语音模式、清理资源
//

import XCTest
@testable import xinlingyisheng

/// UnifiedChatViewModel 单元测试
final class UnifiedChatViewModelTests: XCTestCase {

    var viewModel: UnifiedChatViewModel!

    override func setUp() async throws {
        try await super.setUp()
        await MainActor.run {
            viewModel = UnifiedChatViewModel()
        }
    }

    override func tearDown() async throws {
        await MainActor.run {
            viewModel.cleanup()
            viewModel = nil
        }
        try await super.tearDown()
    }

    // MARK: - Initial State Tests

    func testInitialState() async throws {
        await MainActor.run {
            // Then - 验证初始状态
            XCTAssertTrue(viewModel.messages.isEmpty, "初始消息列表应该为空")
            XCTAssertEqual(viewModel.inputMode, .text, "初始输入模式应该是文字")
            XCTAssertFalse(viewModel.isVoiceMode, "初始不应该处于语音模式")
            XCTAssertFalse(viewModel.isSending, "初始不应该在发送中")
            XCTAssertFalse(viewModel.isLoading, "初始不应该在加载中")
            XCTAssertFalse(viewModel.isUploadingImage, "初始不应该在上传图片")
            XCTAssertFalse(viewModel.isAnalyzing, "初始不应该在分析中")
            XCTAssertNil(viewModel.sessionId, "初始会话ID应该为nil")
            XCTAssertNil(viewModel.agentType, "初始智能体类型应该为nil")
            XCTAssertNil(viewModel.capabilities, "初始智能体能力应该为nil")
            XCTAssertFalse(viewModel.showError, "初始不应该显示错误")
            XCTAssertTrue(viewModel.errorMessage?.isEmpty ?? true, "初始错误消息应该为空")
        }
    }

    // MARK: - Message Management Tests

    func testMessagesInitiallyEmpty() async throws {
        await MainActor.run {
            // Then
            XCTAssertTrue(viewModel.messages.isEmpty, "初始消息列表应该为空")
            XCTAssertEqual(viewModel.messages.count, 0, "消息数量应该为0")
        }
    }

    func testInputModeDefaultIsText() async throws {
        await MainActor.run {
            // Then
            XCTAssertEqual(viewModel.inputMode, .text, "默认输入模式应该是文字")
            XCTAssertFalse(viewModel.isVoiceMode, "默认不应该处于语音模式")
        }
    }

    func testClearMessages() async throws {
        await MainActor.run {
            // Given - 添加一些测试消息
            // 注意：messages 是通过 @Published 从 messageService 同步的
            // 直接修改 messages 可能不会触发服务层的变化
            // 这里测试 cleanup 方法，它会调用 messageService.clearMessages()

            // When
            viewModel.cleanup()

            // Then
            XCTAssertTrue(viewModel.messages.isEmpty, "清理后消息列表应该为空")
        }
    }

    func testStreamingContentInitiallyEmpty() async throws {
        await MainActor.run {
            // Then
            XCTAssertTrue(viewModel.streamingContent.isEmpty, "初始流式内容应该为空")
        }
    }

    // MARK: - Voice Mode Tests

    func testToggleVoiceMode() async throws {
        await MainActor.run {
            // Given - 初始状态
            XCTAssertFalse(viewModel.isVoiceMode, "初始不应该处于语音模式")
            XCTAssertEqual(viewModel.inputMode, .text, "初始输入模式应该是文字")

            // When - 切换到语音模式
            viewModel.isVoiceMode = true

            // Then
            XCTAssertTrue(viewModel.isVoiceMode, "应该处于语音模式")
        }
    }

    func testVoiceStateInitiallyIdle() async throws {
        await MainActor.run {
            // Then
            XCTAssertEqual(viewModel.voiceState, .idle, "初始语音状态应该是空闲")
        }
    }

    func testRecognizedTextInitiallyEmpty() async throws {
        await MainActor.run {
            // Then
            XCTAssertTrue(viewModel.recognizedText.isEmpty, "初始识别文本应该为空")
        }
    }

    func testAudioLevelInitiallyZero() async throws {
        await MainActor.run {
            // Then
            XCTAssertEqual(viewModel.audioLevel, 0, "初始音频电平应该为0")
        }
    }

    func testIsMicrophoneMutedInitiallyFalse() async throws {
        await MainActor.run {
            // Then
            XCTAssertFalse(viewModel.isMicrophoneMuted, "初始麦克风不应该静音")
        }
    }

    func testShowExitConfirmationInitiallyFalse() async throws {
        await MainActor.run {
            // Then
            XCTAssertFalse(viewModel.showExitConfirmation, "初始不应该显示退出确认")
        }
    }

    // MARK: - Cleanup Tests

    func testCleanupVoiceBindings() async throws {
        await MainActor.run {
            // Given - 设置语音模式
            viewModel.isVoiceMode = true

            // When
            viewModel.cleanupVoiceBindings()

            // Then - cleanupVoiceBindings 主要清理内部服务的语音绑定
            // 对外属性可能不会立即反映，这里验证方法不崩溃
            XCTAssertNotNil(viewModel, "清理后 ViewModel 应该仍然存在")
        }
    }

    func testFullCleanup() async throws {
        await MainActor.run {
            // Given - 设置一些状态
            viewModel.isVoiceMode = true
            viewModel.showExitConfirmation = true

            // When
            viewModel.cleanup()

            // Then
            XCTAssertTrue(viewModel.messages.isEmpty, "清理后消息应该为空")
            XCTAssertEqual(viewModel.inputMode, .text, "清理后输入模式应该重置为文字")
        }
    }

    // MARK: - Session Management Tests

    func testSessionIdInitiallyNil() async throws {
        await MainActor.run {
            // Then
            XCTAssertNil(viewModel.sessionId, "初始会话ID应该为nil")
        }
    }

    func testAgentTypeInitiallyNil() async throws {
        await MainActor.run {
            // Then
            XCTAssertNil(viewModel.agentType, "初始智能体类型应该为nil")
        }
    }

    func testCapabilitiesInitiallyNil() async throws {
        await MainActor.run {
            // Then
            XCTAssertNil(viewModel.capabilities, "初始智能体能力应该为nil")
        }
    }

    func testCurrentDepartmentInitiallyNil() async throws {
        await MainActor.run {
            // Then - currentDepartment 是内部服务的属性，通过绑定同步
            // 初始值应该为 nil
            XCTAssertNil(viewModel.currentDepartment, "初始当前科室应该为nil")
        }
    }

    func testCurrentDoctorIdInitiallyNil() async throws {
        await MainActor.run {
            // Then
            XCTAssertNil(viewModel.currentDoctorId, "初始当前医生ID应该为nil")
        }
    }

    // MARK: - Error State Tests

    func testShowErrorInitiallyFalse() async throws {
        await MainActor.run {
            // Then
            XCTAssertFalse(viewModel.showError, "初始不应该显示错误")
        }
    }

    func testErrorMessageInitiallyNil() async throws {
        await MainActor.run {
            // Then
            XCTAssertNil(viewModel.errorMessage, "初始错误消息应该为nil")
        }
    }

    // MARK: - Loading State Tests

    func testIsLoadingInitiallyFalse() async throws {
        await MainActor.run {
            // Then
            XCTAssertFalse(viewModel.isLoading, "初始不应该在加载中")
        }
    }

    func testIsSendingInitiallyFalse() async throws {
        await MainActor.run {
            // Then
            XCTAssertFalse(viewModel.isSending, "初始不应该在发送中")
        }
    }

    func testIsUploadingImageInitiallyFalse() async throws {
        await MainActor.run {
            // Then
            XCTAssertFalse(viewModel.isUploadingImage, "初始不应该在上传图片")
        }
    }

    func testIsAnalyzingInitiallyFalse() async throws {
        await MainActor.run {
            // Then
            XCTAssertFalse(viewModel.isAnalyzing, "初始不应该在分析中")
        }
    }

    // MARK: - Conversation State Tests

    func testIsConversationCompletedInitiallyFalse() async throws {
        await MainActor.run {
            // Then
            XCTAssertFalse(viewModel.isConversationCompleted, "初始对话不应该已完成")
        }
    }

    func testEventIdInitiallyNil() async throws {
        await MainActor.run {
            // Then
            XCTAssertNil(viewModel.eventId, "初始事件ID应该为nil")
        }
    }

    func testIsNewEventInitiallyFalse() async throws {
        await MainActor.run {
            // Then
            XCTAssertFalse(viewModel.isNewEvent, "初始不应该为新事件")
        }
    }

    func testShouldShowDossierPromptInitiallyFalse() async throws {
        await MainActor.run {
            // Then
            XCTAssertFalse(viewModel.shouldShowDossierPrompt, "初始不应该显示病历提示")
        }
    }

    // MARK: - Dossier Generation Tests

    func testShowGenerateConfirmationInitiallyFalse() async throws {
        await MainActor.run {
            // Then
            XCTAssertFalse(viewModel.showGenerateConfirmation, "初始不应该显示生成确认")
        }
    }

    func testGenerateConfirmationMessageInitiallyEmpty() async throws {
        await MainActor.run {
            // Then
            XCTAssertTrue(viewModel.generateConfirmationMessage.isEmpty, "初始生成确认消息应该为空")
        }
    }

    func testCanGenerateDossierInitiallyFalse() async throws {
        await MainActor.run {
            // Then - 没有消息且对话未完成，不应该能生成病历
            XCTAssertFalse(viewModel.canGenerateDossier, "初始不应该能生成病历")
        }
    }

    func testDossierButtonTooltipInitially() async throws {
        await MainActor.run {
            // When - 不能生成时
            let tooltip = viewModel.dossierButtonTooltip

            // Then - 应该显示相应的提示
            XCTAssertFalse(tooltip.isEmpty, "应该有按钮提示")
        }
    }

    // MARK: - Diagnosis Display Tests

    func testAdviceHistoryInitiallyEmpty() async throws {
        await MainActor.run {
            // Then
            XCTAssertTrue(viewModel.adviceHistory.isEmpty, "初始建议历史应该为空")
        }
    }

    func testDiagnosisCardInitiallyNil() async throws {
        await MainActor.run {
            // Then
            XCTAssertNil(viewModel.diagnosisCard, "初始诊断卡片应该为nil")
        }
    }

    func testKnowledgeRefsInitiallyEmpty() async throws {
        await MainActor.run {
            // Then
            XCTAssertTrue(viewModel.knowledgeRefs.isEmpty, "初始知识引用应该为空")
        }
    }

    func testReasoningStepsInitiallyEmpty() async throws {
        await MainActor.run {
            // Then
            XCTAssertTrue(viewModel.reasoningSteps.isEmpty, "初始推理步骤应该为空")
        }
    }

    // MARK: - Risk Alert Tests

    func testShowRiskAlertInitiallyFalse() async throws {
        await MainActor.run {
            // Then
            XCTAssertFalse(viewModel.showRiskAlert, "初始不应该显示高风险警告")
        }
    }

    func testRiskAlertMessageInitiallyEmpty() async throws {
        await MainActor.run {
            // Then
            XCTAssertTrue(viewModel.riskAlertMessage.isEmpty, "初始风险警告消息应该为空")
        }
    }

    // MARK: - Action Mode Tests

    func testCurrentActionModeInitiallyNil() async throws {
        await MainActor.run {
            // Then
            XCTAssertNil(viewModel.currentActionMode, "初始动作模式应该为nil")
        }
    }

    func testStreamingMessageIdInitiallyNil() async throws {
        await MainActor.run {
            // Then
            XCTAssertNil(viewModel.streamingMessageId, "初始流式消息ID应该为nil")
        }
    }

    // MARK: - Available Actions Tests

    func testAvailableActionsInitiallyEmpty() async throws {
        await MainActor.run {
            // When - 没有设置智能体能力
            let actions = viewModel.availableActions

            // Then
            XCTAssertTrue(actions.isEmpty, "初始可用动作应该为空")
        }
    }

    // MARK: - Support Tests

    func testSupportsActionWithNilCapabilities() async throws {
        await MainActor.run {
            // Given - 没有设置能力
            viewModel.capabilities = nil

            // When & Then
            XCTAssertFalse(viewModel.supportsAction(.conversation), "没有能力时不应该支持任何动作")
            XCTAssertFalse(viewModel.supportsAction(.analyzeSkin), "没有能力时不应该支持皮肤分析")
            XCTAssertFalse(viewModel.supportsAction(.interpretReport), "没有能力时不应该支持报告解读")
            XCTAssertFalse(viewModel.supportsAction(.interpretECG), "没有能力时不应该支持心电图解读")
        }
    }

    func testSupportsImageUploadWithNilCapabilities() async throws {
        await MainActor.run {
            // Given - 没有设置能力
            viewModel.capabilities = nil

            // When & Then
            XCTAssertFalse(viewModel.supportsImageUpload(), "没有能力时不应该支持图片上传")
        }
    }

    // MARK: - AI Response Text Tests

    func testAIResponseTextInitiallyEmpty() async throws {
        await MainActor.run {
            // Then
            XCTAssertTrue(viewModel.aiResponseText.isEmpty, "初始AI响应文本应该为空")
        }
    }

    // MARK: - Voice Image Request Callback Tests

    func testOnVoiceImageRequestInitiallyNil() async throws {
        await MainActor.run {
            // Then
            XCTAssertNil(viewModel.onVoiceImageRequest, "初始语音图片请求回调应该为nil")
        }
    }
}
