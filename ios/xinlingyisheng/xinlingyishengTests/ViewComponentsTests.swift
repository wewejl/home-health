//
//  ViewComponentsTests.swift
//  xinlingyisheng
//
//  SwiftUI 视图组件单元测试 - 补全缺失的视图测试
//  测试主要视图组件的渲染和交互逻辑
//

import XCTest
@testable import xinlingyisheng

@MainActor
final class ViewComponentsTests: XCTestCase {

    // MARK: - Setup

    override func setUp() async throws {
        try await super.setUp()
    }

    override func tearDown() async throws {
        try await super.tearDown()
    }

    // MARK: - TaskCheckInView Tests

    func testTaskCheckInViewInitialization() {
        // Given
        let task = TaskInstance(
            id: 1,
            order_id: 1,
            patient_id: 1,
            scheduled_date: "2024-01-23",
            scheduled_time: "08:00",
            status: "pending",
            order_title: "早餐前注射胰岛素",
            order_type: "medication"
        )
        let viewModel = MedicalOrderViewModel()

        // When
        let view = TaskCheckInView(task: task, viewModel: viewModel)

        // Then
        XCTAssertNotNil(view)
    }

    func testTaskCheckInViewCompletionTypes() {
        // Given
        let checkType = CompletionType.check
        let photoType = CompletionType.photo
        let valueType = CompletionType.value
        let medicationType = CompletionType.medication

        // Then
        XCTAssertEqual(checkType.displayName, "打卡")
        XCTAssertEqual(photoType.displayName, "拍照")
        XCTAssertEqual(valueType.displayName, "数值")
        XCTAssertEqual(medicationType.displayName, "用药")
    }

    // MARK: - MedicationListView Tests

    func testMedicationListViewInitialization() {
        // Given
        let medications = [
            MedicationItem(name: "阿莫西林", dosage: "250mg", frequency: "每日3次"),
            MedicationItem(name: "布洛芬", dosage: "200mg", frequency: "每日2次"),
            MedicationItem(name: "维生素C", dosage: "100mg", frequency: "每日1次")
        ]

        // When
        let view = MedicationListView(medications: medications)

        // Then
        XCTAssertNotNil(view)
        XCTAssertEqual(view.medications.count, 3)
    }

    func testMedicationListViewEmptyState() {
        // Given
        let medications: [MedicationItem] = []

        // When
        let view = MedicationListView(medications: medications)

        // Then
        XCTAssertNotNil(view)
        XCTAssertEqual(view.medications.count, 0)
    }

    // MARK: - MedicalDossierView Tests

    func testMedicalDossierViewInitialization() {
        // Given
        let view = MedicalDossierView()

        // Then
        XCTAssertNotNil(view)
    }

    func testMedicalDossierViewModelInitialization() {
        // Given
        let viewModel = MedicalDossierViewModel()

        // Then
        XCTAssertNotNil(viewModel)
        XCTAssertEqual(viewModel.selectedFilter, .all)
    }

    func testEventFilterAllCases() {
        // Given & Then
        XCTAssertEqual(EventFilter.all.count, 6)
        XCTAssertEqual(EventFilter.allCases.first, .all)
        XCTAssertEqual(EventFilter.allCases.last, .exported)

        // Test display names
        XCTAssertEqual(EventFilter.all.displayName, "全部")
        XCTAssertEqual(EventFilter.consultations.displayName, "咨询")
        XCTAssertEqual(EventFilter.medications.displayName, "用药")
        XCTAssertEqual(EventFilter.monitoring.displayName, "监测")
        XCTAssertEqual(EventFilter.orders.displayName, "医嘱")
        XCTAssertEqual(EventFilter.exported.displayName, "已导出")
    }

    // MARK: - ConsultationView Tests

    func testConsultationViewInitialization() {
        // Given
        let consultation = Consultation(
            id: "1",
            patientId: 1,
            doctorName: "测试医生",
            startTime: Date(),
            status: .inProgress
        )

        // When
        let view = ConsultationView(consultation: consultation)

        // Then
        XCTAssertNotNil(view)
    }

    func testConsultationStatusValues() {
        // Given & Then
        XCTAssertEqual(ConsultationStatus.inProgress.displayName, "进行中")
        XCTAssertEqual(ConsultationStatus.completed.displayName, "已完成")
        XCTAssertEqual(ConsultationStatus.cancelled.displayName, "已取消")
        XCTAssertEqual(ConsultationStatus.scheduled.displayName, "已预约")
    }

    // MARK: - DiagnosisSummaryCard Tests

    func testDiagnosisSummaryCardInitialization() {
        // Given
        let card = DiagnosisCard(
            summary: "手臂出现红色皮疹，伴有瘙痒，已持续3天。",
            conditions: [
                DiagnosisCondition(name: "湿疹", confidence: 0.8, rationale: ["红疹", "瘙痒"])
            ],
            riskLevel: "low",
            needOfflineVisit: false,
            urgency: nil,
            carePlan: ["保持皮肤清洁", "避免抓挠"],
            references: [],
            reasoningSteps: ["收集症状", "分析特征"]
        )

        // When
        let view = DiagnosisSummaryCard(card: card) {
            // Empty action
        }

        // Then
        XCTAssertNotNil(view)
    }

    func testDiagnosisConditionModel() {
        // Given
        let condition = DiagnosisCondition(
            name: "湿疹",
            confidence: 0.8,
            rationale: ["红疹", "瘙痒", "对称分布"]
        )

        // Then
        XCTAssertEqual(condition.name, "湿疹")
        XCTAssertEqual(condition.confidence, 0.8)
        XCTAssertEqual(condition.rationale.count, 3)
    }

    func testDiagnosisCardModel() {
        // Given
        let card = DiagnosisCard(
            summary: "测试摘要",
            conditions: [],
            riskLevel: "high",
            needOfflineVisit: true,
            urgency: "尽快",
            carePlan: [],
            references: [],
            reasoningSteps: []
        )

        // Then
        XCTAssertEqual(card.summary, "测试摘要")
        XCTAssertEqual(card.riskLevel, "high")
        XCTAssertTrue(card.needOfflineVisit)
        XCTAssertEqual(card.urgency, "尽快")
    }

    // MARK: - SpecialtyDataView Tests

    func testSpecialtyDataViewInitialization() {
        // Given
        let specialtyData = SpecialtyData(
            symptoms: ["红疹", "瘙痒"],
            diagnosisCard: nil
        )

        // When
        let view = SpecialtyDataView(specialtyData: specialtyData, agentType: .dermatology)

        // Then
        XCTAssertNotNil(view)
    }

    func testAgentTypeValues() {
        // Given & Then
        XCTAssertEqual(AgentType.dermatology.displayName, "皮肤科")
        XCTAssertEqual(AgentType.cardiology.displayName, "心内科")
        XCTAssertEqual(AgentType.general.displayName, "全科")
        XCTAssertEqual(AgentType.orthopedics.displayName, "骨科")
    }

    func testSpecialtyDataModel() {
        // Given
        let diagnosisCard = DiagnosisCard(
            summary: "初步诊断",
            conditions: [],
            riskLevel: "low",
            needOfflineVisit: false,
            urgency: nil,
            carePlan: [],
            references: [],
            reasoningSteps: []
        )

        let specialtyData = SpecialtyData(
            symptoms: ["症状1", "症状2"],
            diagnosisCard: diagnosisCard
        )

        // Then
        XCTAssertEqual(specialtyData.symptoms.count, 2)
        XCTAssertNotNil(specialtyData.diagnosisCard)
    }

    func testSpecialtyDataViewWithCardiology() {
        // Given
        let specialtyData = SpecialtyData(
            symptoms: ["胸痛", "气短"],
            diagnosisCard: nil
        )

        // When
        let view = SpecialtyDataView(specialtyData: specialtyData, agentType: .cardiology)

        // Then
        XCTAssertNotNil(view)
    }

    func testSpecialtyDataViewWithGeneral() {
        // Given
        let specialtyData = SpecialtyData(
            symptoms: ["发热", "乏力"],
            diagnosisCard: nil
        )

        // When
        let view = SpecialtyDataView(specialtyData: specialtyData, agentType: .general)

        // Then
        XCTAssertNotNil(view)
    }

    // MARK: - SymptomsTagView Tests

    func testSymptomsTagViewInitialization() {
        // Given
        let symptoms = ["红疹", "瘙痒", "脱皮", "肿胀"]

        // When
        let view = SymptomsTagView(symptoms: symptoms)

        // Then
        XCTAssertNotNil(view)
    }

    func testSymptomsTagViewEmpty() {
        // Given
        let symptoms: [String] = []

        // When
        let view = SymptomsTagView(symptoms: symptoms)

        // Then
        XCTAssertNotNil(view)
    }

    // MARK: - RiskLevelBadge Tests

    func testRiskLevelBadgeInitialization() {
        // Given
        let badge = RiskLevelBadge(level: "high")

        // When
        let view = badge.body

        // Then
        XCTAssertNotNil(view)
    }

    func testRiskLevelBadgeColors() {
        // Given
        let emergencyBadge = RiskLevelBadge(level: "emergency")
        let highBadge = RiskLevelBadge(level: "high")
        let mediumBadge = RiskLevelBadge(level: "medium")
        let lowBadge = RiskLevelBadge(level: "low")

        // Then
        XCTAssertEqual(emergencyBadge.badgeColor, .red)
        XCTAssertEqual(highBadge.badgeColor, .orange)
        XCTAssertEqual(mediumBadge.badgeColor, .yellow)
        XCTAssertEqual(lowBadge.badgeColor, .green)
    }

    func testRiskLevelBadgeDisplayText() {
        // Given
        let emergencyBadge = RiskLevelBadge(level: "emergency")
        let highBadge = RiskLevelBadge(level: "high")
        let mediumBadge = RiskLevelBadge(level: "medium")
        let lowBadge = RiskLevelBadge(level: "low")

        // Then
        XCTAssertEqual(emergencyBadge.displayText, "紧急")
        XCTAssertEqual(highBadge.displayText, "高风险")
        XCTAssertEqual(mediumBadge.displayText, "中风险")
        XCTAssertEqual(lowBadge.displayText, "低风险")
    }

    // MARK: - ConditionRowView Tests

    func testConditionRowViewInitialization() {
        // Given
        let condition = DiagnosisCondition(
            name: "湿疹",
            confidence: 0.8,
            rationale: ["红疹", "瘙痒"]
        )

        // When
        let view = ConditionRowView(condition: condition)

        // Then
        XCTAssertNotNil(view)
    }

    func testConditionRowViewBarColor() {
        // Given
        let highConfidence = DiagnosisCondition(name: "高", confidence: 0.8, rationale: [])
        let mediumConfidence = DiagnosisCondition(name: "中", confidence: 0.5, rationale: [])
        let lowConfidence = DiagnosisCondition(name: "低", confidence: 0.3, rationale: [])

        // Then
        XCTAssertEqual(highConfidence.barColor, .orange)
        XCTAssertEqual(mediumConfidence.barColor, .yellow)
        XCTAssertEqual(lowConfidence.barColor, .green)
    }

    // MARK: - EvidenceListView Tests

    func testEvidenceListViewInitialization() {
        // Given
        let refs = [
            KnowledgeRef(id: "1", title: "参考文献1", snippet: "摘要1", source: "来源1"),
            KnowledgeRef(id: "2", title: "参考文献2", snippet: "摘要2", source: "来源2")
        ]

        // When
        let view = EvidenceListView(refs: refs)

        // Then
        XCTAssertNotNil(view)
    }

    func testKnowledgeRefModel() {
        // Given
        let ref = KnowledgeRef(
            id: "ref-001",
            title: "测试文献",
            snippet: "这是一篇测试文献的摘要",
            source: "测试医学期刊"
        )

        // Then
        XCTAssertEqual(ref.id, "ref-001")
        XCTAssertEqual(ref.title, "测试文献")
        XCTAssertEqual(ref.source, "测试医学期刊")
    }

    // MARK: - ReasoningTimelineView Tests

    func testReasoningTimelineViewInitialization() {
        // Given
        let steps = ["步骤一", "步骤二", "步骤三", "步骤四"]

        // When
        let view = ReasoningTimelineView(steps: steps)

        // Then
        XCTAssertNotNil(view)
    }

    func testReasoningTimelineViewEmpty() {
        // Given
        let steps: [String] = []

        // When
        let view = ReasoningTimelineView(steps: steps)

        // Then
        XCTAssertNotNil(view)
    }

    // MARK: - ConfidenceBadge Tests

    func testConfidenceBadgeInitialization() {
        // Given
        let badge = ConfidenceBadge(confidence: 0.75)

        // When
        let view = badge.body

        // Then
        XCTAssertNotNil(view)
    }

    func testConfidenceBadgeColors() {
        // Given
        let highConfidence = ConfidenceBadge(confidence: 0.8)
        let mediumConfidence = ConfidenceBadge(confidence: 0.5)
        let lowConfidence = ConfidenceBadge(confidence: 0.2)

        // Then
        XCTAssertEqual(highConfidence.color, .green)
        XCTAssertEqual(mediumConfidence.color, .yellow)
        XCTAssertEqual(lowConfidence.color, .gray)
    }

    // MARK: - FlowLayout Tests

    func testFlowLayoutInitialization() {
        // Given
        let layout = FlowLayout(spacing: 8)

        // Then
        XCTAssertNotNil(layout)
        XCTAssertEqual(layout.spacing, 8)
    }

    func testFlowLayoutDefaultSpacing() {
        // Given
        let layout = FlowLayout()

        // Then
        XCTAssertEqual(layout.spacing, 8)
    }

    // MARK: - ConsultationProgressView Tests

    func testConsultationProgressViewInitialization() {
        // Given
        let stage = ConsultationStage.diagnosing
        let progress = 75

        // When
        let view = ConsultationProgressView(stage: stage, progress: progress)

        // Then
        XCTAssertNotNil(view)
    }

    func testConsultationStageDisplayNames() {
        // Given & Then
        XCTAssertEqual(ConsultationStage.collecting.displayName, "收集中")
        XCTAssertEqual(ConsultationStage.diagnosing.displayName, "诊断中")
        XCTAssertEqual(ConsultationStage.completed.displayName, "已完成")
    }

    // MARK: - HealingFilterChip Tests

    func testHealingFilterChipInitialization() {
        // Given
        let chip = HealingFilterChip(
            title: "测试",
            count: 5,
            isSelected: true,
            layout: AdaptiveLayout(screenWidth: 390)
        ) {
            // Empty action
        }

        // Then
        XCTAssertNotNil(chip)
    }

    func testHealingFilterChipNotSelected() {
        // Given
        let chip = HealingFilterChip(
            title: "测试",
            count: 0,
            isSelected: false,
            layout: AdaptiveLayout(screenWidth: 390)
        ) {
            // Empty action
        }

        // Then
        XCTAssertNotNil(chip)
    }

    // MARK: - ErrorBannerView Tests

    func testErrorBannerViewInitialization() {
        // Given
        let banner = ErrorBannerView(
            message: "测试错误消息",
            onDismiss: {},
            layout: AdaptiveLayout(screenWidth: 390)
        )

        // Then
        XCTAssertNotNil(banner)
    }

    // MARK: - HealingDossierEmptyStateView Tests

    func testHealingDossierEmptyStateViewInitialization() {
        // Given
        let view = HealingDossierEmptyStateView(layout: AdaptiveLayout(screenWidth: 390))

        // Then
        XCTAssertNotNil(view)
    }

    // MARK: - HealingDossierSearchEmptyView Tests

    func testHealingDossierSearchEmptyViewInitialization() {
        // Given
        let view = HealingDossierSearchEmptyView(
            searchText: "测试搜索",
            layout: AdaptiveLayout(screenWidth: 390)
        )

        // Then
        XCTAssertNotNil(view)
    }

    // MARK: - HealingDossierLoadingView Tests

    func testHealingDossierLoadingViewInitialization() {
        // Given
        let view = HealingDossierLoadingView(layout: AdaptiveLayout(screenWidth: 390))

        // Then
        XCTAssertNotNil(view)
    }

    // MARK: - HealingDossierBackground Tests

    func testHealingDossierBackgroundInitialization() {
        // Given
        let view = HealingDossierBackground(layout: AdaptiveLayout(screenWidth: 390))

        // Then
        XCTAssertNotNil(view)
    }

    // MARK: - TaskInstance Model Tests

    func testTaskInstanceModel() {
        // Given
        let task = TaskInstance(
            id: 1,
            order_id: 2,
            patient_id: 3,
            scheduled_date: "2024-01-23",
            scheduled_time: "08:00",
            status: "pending",
            order_title: "测试任务",
            order_type: "monitoring"
        )

        // Then
        XCTAssertEqual(task.id, 1)
        XCTAssertEqual(task.order_id, 2)
        XCTAssertEqual(task.scheduled_date, "2024-01-23")
        XCTAssertEqual(task.scheduled_time, "08:00")
        XCTAssertEqual(task.order_title, "测试任务")
        XCTAssertEqual(task.order_type, "monitoring")
    }

    // MARK: - MedicationItem Model Tests

    func testMedicationItemModel() {
        // Given
        let medication = MedicationItem(
            name: "阿莫西林",
            dosage: "250mg",
            frequency: "每日3次"
        )

        // Then
        XCTAssertEqual(medication.name, "阿莫西林")
        XCTAssertEqual(medication.dosage, "250mg")
        XCTAssertEqual(medication.frequency, "每日3次")
    }

    // MARK: - Consultation Model Tests

    func testConsultationModel() {
        // Given
        let consultation = Consultation(
            id: "consult-001",
            patientId: 1,
            doctorName: "测试医生",
            startTime: Date(),
            status: .inProgress
        )

        // Then
        XCTAssertEqual(consultation.id, "consult-001")
        XCTAssertEqual(consultation.patientId, 1)
        XCTAssertEqual(consultation.doctorName, "测试医生")
        XCTAssertEqual(consultation.status, .inProgress)
    }

    // MARK: - Layout Tests for Different Screen Sizes

    func testLayoutForCompactScreen() {
        // Given
        let layout = AdaptiveLayout(screenWidth: 375)

        // Then
        XCTAssertTrue(layout.isCompact)
        XCTAssertFalse(layout.isRegular)
        XCTAssertFalse(layout.isLarge)
    }

    func testLayoutForRegularScreen() {
        // Given
        let layout = AdaptiveLayout(screenWidth: 390)

        // Then
        XCTAssertFalse(layout.isCompact)
        XCTAssertTrue(layout.isRegular)
        XCTAssertFalse(layout.isLarge)
    }

    func testLayoutForLargeScreen() {
        // Given
        let layout = AdaptiveLayout(screenWidth: 428)

        // Then
        XCTAssertFalse(layout.isCompact)
        XCTAssertFalse(layout.isRegular)
        XCTAssertTrue(layout.isLarge)
    }

    func testLayoutConsistencyAcrossSizes() {
        // Given
        let compactLayout = AdaptiveLayout(screenWidth: 375)
        let regularLayout = AdaptiveLayout(screenWidth: 390)
        let largeLayout = AdaptiveLayout(screenWidth: 428)

        // Then - Verify that iconScale and paddingScale are consistent (1.0)
        XCTAssertEqual(compactLayout.iconScale, 1.0)
        XCTAssertEqual(regularLayout.iconScale, 1.0)
        XCTAssertEqual(largeLayout.iconScale, 1.0)

        XCTAssertEqual(compactLayout.paddingScale, 1.0)
        XCTAssertEqual(regularLayout.paddingScale, 1.0)
        XCTAssertEqual(largeLayout.paddingScale, 1.0)
    }
}
