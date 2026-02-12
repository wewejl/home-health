//
//  ViewTests.swift
//  xinlingyisheng
//
//  SwiftUI 视图单元测试
// 测试主要视图组件的渲染和交互逻辑
//

import XCTest
@testable import xinlingyisheng

@MainActor
final class ViewTests: XCTestCase {

    // MARK: - Setup

    var sut: HomeView!

    override func setUp() async throws {
        try await super.setUp()
        sut = HomeView()
    }

    override func tearDown() async throws {
        sut = nil
        try await super.tearDown()
    }

    // MARK: - HomeView Tests

    func testHomeViewInitialization() {
        // Given & When
        let view = HomeView()

        // Then
        XCTAssertNotNil(view)
    }

    func testHomeViewAdaptiveLayout() {
        // Given
        let compactWidth: CGFloat = 375
        let regularWidth: CGFloat = 390

        // When
        let compactLayout = AdaptiveLayout(screenWidth: compactWidth)
        let regularLayout = AdaptiveLayout(screenWidth: regularWidth)

        // Then
        XCTAssertTrue(compactLayout.isCompact)
        XCTAssertFalse(compactLayout.isRegular)
        XCTAssertTrue(regularLayout.isRegular)
        XCTAssertFalse(regularLayout.isCompact)
    }

    // MARK: - AskDoctorView Tests

    func testAskDoctorViewInitialization() {
        // Given
        let viewModel = AskDoctorViewModel()
        let view = AskDoctorView(viewModel: viewModel)

        // Then
        XCTAssertNotNil(view)
    }

    // MARK: - DiseaseListView Tests

    func testDiseaseListViewInitialization() {
        // Given
        let viewModel = DiseaseListViewModel()
        let view = DiseaseListView(viewModel: viewModel)

        // Then
        XCTAssertNotNil(view)
    }

    // MARK: - DrugListView Tests

    func testDrugListViewInitialization() {
        // Given
        let viewModel = DrugListViewModel()
        let view = DrugListView(viewModel: viewModel)

        // Then
        XCTAssertNotNil(view)
    }

    // MARK: - DepartmentDetailView Tests

    func testDepartmentDetailViewInitialization() {
        // Given
        let department = Department(
            id: 1,
            name: "皮肤科",
            description: "测试科室",
            icon: nil
        )
        let view = DepartmentDetailView(department: department)

        // Then
        XCTAssertNotNil(view)
    }

    // MARK: - DiseaseDetailView Tests

    func testDiseaseDetailViewInitialization() {
        // Given
        let disease = Disease(
            id: 1,
            name: "湿疹",
            departmentId: 1,
            description: "测试疾病",
            recommendedDepartment: "皮肤科",
            isHot: true
        )
        let view = DiseaseDetailView(disease: disease)

        // Then
        XCTAssertNotNil(view)
    }

    // MARK: - DrugDetailView Tests

    func testDrugDetailViewInitialization() {
        // Given
        let drug = Drug(
            id: 1,
            name: "阿莫西林",
            genericName: "Amoxicillin",
            specification: "250mg",
            manufacturer: "测试药厂",
            category: "抗生素"
        )
        let view = DrugDetailView(drug: drug)

        // Then
        XCTAssertNotNil(view)
    }

    // MARK: - MedicationListView Tests

    func testMedicationListViewInitialization() {
        // Given
        let medications = [
            MedicationItem(name: "阿莫西林", dosage: "250mg", frequency: "每日3次"),
            MedicationItem(name: "布洛芬", dosage: "200mg", frequency: "每日2次")
        ]
        let view = MedicationListView(medications: medications)

        // Then
        XCTAssertNotNil(view)
        XCTAssertEqual(view.medications.count, 2)
    }

    // MARK: - TaskCheckInView Tests

    func testTaskCheckInViewInitialization() {
        // Given
        let task = TaskInstance(
            id: 1,
            title: "测血压",
            dueDate: Date(),
            isCompleted: false
        )
        let view = TaskCheckInView(task: task)

        // Then
        XCTAssertNotNil(view)
    }

    // MARK: - MedicalDossier Tests

    func testMedicalDossierInitialization() {
        // Given
        let dossier = MedicalDossier(
            id: 1,
            patientName: "测试患者",
            events: [],
            summaries: []
        )
        let view = MedicalDossierView(dossier: dossier)

        // Then
        XCTAssertNotNil(view)
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
        let view = ConsultationView(consultation: consultation)

        // Then
        XCTAssertNotNil(view)
    }

    // MARK: - AdaptiveLayout Tests

    func testAdaptiveLayoutColorScaling() {
        // Given
        let layout = AdaptiveLayout(screenWidth: 390)

        // When & Then
        XCTAssertEqual(layout.iconScale, 1.0)
        XCTAssertEqual(layout.paddingScale, 1.0)
    }

    func testAdaptiveLayoutCardDimensions() {
        // Given
        let layout = AdaptiveLayout(screenWidth: 390)

        // When & Then
        XCTAssertEqual(layout.todayCardHeight, 120)
        XCTAssertEqual(layout.quickCardLargeHeight, 150)
        XCTAssertEqual(layout.quickCardSmallHeight, 66)
    }

    func testAdaptiveLayoutIconSizes() {
        // Given
        let layout = AdaptiveLayout(screenWidth: 390)

        // When & Then
        XCTAssertEqual(layout.iconLargeSize, 48)
        XCTAssertEqual(layout.iconSmallSize, 38)
    }

    // MARK: - HealingColors Tests

    func testHealingColorsExist() {
        // Then
        XCTAssertNotNil(HealingColors.softSage)
        XCTAssertNotNil(HealingColors.deepSage)
        XCTAssertNotNil(HealingColors.forestMist)
        XCTAssertNotNil(HealingColors.warmCream)
        XCTAssertNotNil(HealingColors.softPeach)
        XCTAssertNotNil(HealingColors.warmSand)
        XCTAssertNotNil(HealingColors.dustyBlue)
        XCTAssertNotNil(HealingColors.lavenderHaze)
    }

    func testHealingColorsFunctionalColors() {
        // Then
        XCTAssertNotNil(HealingColors.background)
        XCTAssertNotNil(HealingColors.cardBackground)
        XCTAssertNotNil(HealingColors.textPrimary)
        XCTAssertNotNil(HealingColors.textSecondary)
        XCTAssertNotNil(HealingColors.textTertiary)
    }

    // MARK: - UnifiedFont Tests

    func testUnifiedFontSizesExist() {
        // Then
        XCTAssertNotNil(UnifiedFont.largeTitle)
        XCTAssertNotNil(UnifiedFont.title)
        XCTAssertNotNil(UnifiedFont.body)
        XCTAssertNotNil(UnifiedFont.caption)
        XCTAssertNotNil(UnifiedFont.caption1)
        XCTAssertNotNil(UnifiedFont.footnote)
    }

    func testUnifiedFontAccessibility() {
        // Then
        XCTAssertTrue(UnifiedFont.largeTitle > UnifiedFont.title)
        XCTAssertTrue(UnifiedFont.title > UnifiedFont.body)
        XCTAssertTrue(UnifiedFont.body > UnifiedFont.caption)
        XCTAssertTrue(UnifiedFont.caption > UnifiedFont.caption1)
        XCTAssertTrue(UnifiedFont.caption1 > UnifiedFont.footnote)
    }
}
