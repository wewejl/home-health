import SwiftUI

struct EventDetailView: View {
    let event: MedicalEvent
    @ObservedObject var viewModel: MedicalDossierViewModel

    @State private var showExportConfig = false
    @State private var showMoreActions = false
    @State private var showMergeSheet = false
    @State private var showNoteEditor = false
    @State private var selectedEventsForMerge: Set<String> = []
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        ZStack {
            DXYColors.background
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                ScrollView(.vertical, showsIndicators: false) {
                    VStack(spacing: ScaleFactor.spacing(20)) {
                        // AI 摘要卡片
                        aiSummarySection
                        
                        if let analysis = event.aiAnalysis {
                            AIAnalysisCardView(analysis: analysis)
                        }

                        // 备注卡片
                        if let notes = event.notes, !notes.isEmpty {
                            notesSection(notes: notes)
                        }

                        // 相关病历
                        relatedEventsSection
                        
                        timelineSectionHeader
                        
                        timelineSection
                    }
                    .padding(.horizontal, LayoutConstants.horizontalPadding)
                    .padding(.top, ScaleFactor.padding(16))
                    .padding(.bottom, ScaleFactor.padding(100))
                }
                
                exportButton
            }
        }
        .navigationTitle(event.title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Menu {
                    Button(action: {}) {
                        Label("编辑标题", systemImage: "pencil")
                    }
                    
                    Button(action: { showNoteEditor = true }) {
                        Label(event.notes == nil ? "添加备注" : "编辑备注", systemImage: "note.text.badge.plus")
                    }
                    
                    Divider()
                    
                    Button(action: {
                        viewModel.archiveEvent(event)
                        dismiss()
                    }) {
                        Label("归档", systemImage: "archivebox")
                    }
                    
                    Button(role: .destructive, action: {
                        viewModel.deleteEvent(event)
                        dismiss()
                    }) {
                        Label("删除", systemImage: "trash")
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                        .font(.system(size: AdaptiveFont.title3))
                        .foregroundColor(DXYColors.primaryPurple)
                }
            }
        }
        .sheet(isPresented: $showExportConfig) {
            ExportConfigView(event: event, viewModel: viewModel)
        }
        .sheet(isPresented: $showMergeSheet) {
            MergeEventsSheet(
                currentEventId: event.id,
                relatedEvents: viewModel.relatedEvents,
                viewModel: viewModel,
                onMerge: { eventIds, title in
                    Task {
                        await viewModel.mergeEvents(eventIds: eventIds, newTitle: title)
                        showMergeSheet = false
                    }
                }
            )
        }
        .sheet(isPresented: $showNoteEditor) {
            NoteEditorView(
                eventId: event.id,
                initialContent: event.notes ?? "",
                viewModel: viewModel,
                onSave: {
                    Task {
                        await viewModel.loadEventDetail(eventId: event.id)
                    }
                }
            )
        }
        .onAppear {
            Task {
                await viewModel.fetchAISummary(for: event.id)
                await viewModel.findRelatedEvents(for: event.id)
            }
        }
    }
    
    // MARK: - AI Summary Section
    
    private var aiSummarySection: some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            HStack {
                HStack(spacing: ScaleFactor.spacing(6)) {
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: AdaptiveFont.body))
                        .foregroundColor(DXYColors.primaryPurple)
                    Text("AI 智能摘要")
                        .font(.system(size: AdaptiveFont.body, weight: .semibold))
                        .foregroundColor(DXYColors.textPrimary)
                }
                
                Spacer()
                
                Button(action: {
                    Task {
                        await viewModel.generateAISummary(for: event.id, forceRegenerate: true)
                    }
                }) {
                    HStack(spacing: 4) {
                        if viewModel.isGeneratingSummary {
                            ProgressView()
                                .scaleEffect(0.7)
                        } else {
                            Image(systemName: "arrow.clockwise")
                        }
                        Text("刷新")
                    }
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.primaryPurple)
                }
                .disabled(viewModel.isGeneratingSummary)
            }
            
            if viewModel.isGeneratingSummary {
                HStack {
                    Spacer()
                    VStack(spacing: 8) {
                        ProgressView()
                        Text("正在生成摘要...")
                            .font(.system(size: AdaptiveFont.footnote))
                            .foregroundColor(DXYColors.textTertiary)
                    }
                    Spacer()
                }
                .padding(.vertical, ScaleFactor.padding(20))
            } else if let summary = viewModel.currentSummary {
                aiSummaryContent(summary)
            } else if let error = viewModel.summaryError {
                Text(error)
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(.red)
                    .padding(.vertical, ScaleFactor.padding(8))
            } else {
                Button(action: {
                    Task {
                        await viewModel.generateAISummary(for: event.id)
                    }
                }) {
                    HStack {
                        Image(systemName: "sparkles")
                        Text("生成 AI 摘要")
                    }
                    .font(.system(size: AdaptiveFont.subheadline, weight: .medium))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, ScaleFactor.padding(12))
                    .background(DXYColors.primaryPurple)
                    .clipShape(RoundedRectangle(cornerRadius: 8))
                }
            }
        }
        .padding(ScaleFactor.padding(16))
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
    }
    
    @ViewBuilder
    private func aiSummaryContent(_ summary: AISummaryResponse) -> some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            if let summaryText = summary.summary {
                Text(summaryText)
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.textPrimary)
                    .lineSpacing(4)
            }
            
            if let keyPoints = summary.key_points, !keyPoints.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("关键点")
                        .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                        .foregroundColor(DXYColors.textSecondary)
                    
                    ForEach(keyPoints, id: \.self) { point in
                        HStack(alignment: .top, spacing: 6) {
                            Circle()
                                .fill(DXYColors.teal)
                                .frame(width: 5, height: 5)
                                .padding(.top, 6)
                            Text(point)
                                .font(.system(size: AdaptiveFont.footnote))
                                .foregroundColor(DXYColors.textPrimary)
                        }
                    }
                }
            }
            
            if let symptoms = summary.symptoms, !symptoms.isEmpty {
                FlowLayout(spacing: 6) {
                    ForEach(symptoms, id: \.self) { symptom in
                        Text(symptom)
                            .font(.system(size: AdaptiveFont.caption))
                            .foregroundColor(DXYColors.teal)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 4)
                            .background(DXYColors.teal.opacity(0.1))
                            .clipShape(Capsule())
                    }
                }
            }
            
            if let riskLevel = summary.risk_level {
                HStack(spacing: 6) {
                    Image(systemName: riskIcon(for: riskLevel))
                        .foregroundColor(riskColor(for: riskLevel))
                    Text("风险等级: \(riskDisplayName(for: riskLevel))")
                        .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                        .foregroundColor(riskColor(for: riskLevel))
                }
            }
            
            if let recommendations = summary.recommendations, !recommendations.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    Text("建议")
                        .font(.system(size: AdaptiveFont.footnote, weight: .medium))
                        .foregroundColor(DXYColors.textSecondary)
                    
                    ForEach(Array(recommendations.enumerated()), id: \.offset) { index, rec in
                        HStack(alignment: .top, spacing: 6) {
                            Text("\(index + 1).")
                                .font(.system(size: AdaptiveFont.footnote))
                                .foregroundColor(DXYColors.textTertiary)
                            Text(rec)
                                .font(.system(size: AdaptiveFont.footnote))
                                .foregroundColor(DXYColors.textPrimary)
                        }
                    }
                }
            }
        }
    }
    
    // MARK: - Related Events Section
    
    private var relatedEventsSection: some View {
        Group {
            if viewModel.isLoadingRelated {
                HStack {
                    Spacer()
                    ProgressView()
                        .padding()
                    Spacer()
                }
                .background(Color.white)
                .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius))
            } else if !viewModel.relatedEvents.isEmpty {
                VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
                    HStack {
                        HStack(spacing: ScaleFactor.spacing(6)) {
                            Image(systemName: "link")
                                .font(.system(size: AdaptiveFont.body))
                                .foregroundColor(DXYColors.teal)
                            Text("相关病历")
                                .font(.system(size: AdaptiveFont.body, weight: .semibold))
                                .foregroundColor(DXYColors.textPrimary)
                        }
                        
                        Spacer()
                        
                        Button(action: { showMergeSheet = true }) {
                            HStack(spacing: 4) {
                                Image(systemName: "arrow.triangle.merge")
                                Text("合并")
                            }
                            .font(.system(size: AdaptiveFont.footnote))
                            .foregroundColor(DXYColors.primaryPurple)
                        }
                    }
                    
                    ForEach(viewModel.relatedEvents) { relatedEvent in
                        RelatedEventRow(relatedEvent: relatedEvent)
                    }
                }
                .padding(ScaleFactor.padding(16))
                .background(Color.white)
                .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
            }
        }
    }
    
    // MARK: - Helper Methods
    
    private func riskIcon(for level: String) -> String {
        switch level {
        case "low": return "checkmark.circle.fill"
        case "medium": return "exclamationmark.circle.fill"
        case "high": return "exclamationmark.triangle.fill"
        case "emergency": return "xmark.octagon.fill"
        default: return "questionmark.circle"
        }
    }
    
    private func riskColor(for level: String) -> Color {
        switch level {
        case "low": return DossierColors.riskLow
        case "medium": return DossierColors.riskMedium
        case "high": return DossierColors.riskHigh
        case "emergency": return DossierColors.riskEmergency
        default: return DXYColors.textTertiary
        }
    }
    
    private func riskDisplayName(for level: String) -> String {
        switch level {
        case "low": return "低风险"
        case "medium": return "中风险"
        case "high": return "高风险"
        case "emergency": return "紧急"
        default: return level
        }
    }
    
    private var timelineSectionHeader: some View {
        HStack {
            HStack(spacing: ScaleFactor.spacing(6)) {
                Image(systemName: "clock.arrow.circlepath")
                    .font(.system(size: AdaptiveFont.body))
                    .foregroundColor(DXYColors.teal)
                Text("时间轴")
                    .font(.system(size: AdaptiveFont.body, weight: .semibold))
                    .foregroundColor(DXYColors.textPrimary)
            }
            
            Spacer()
            
            Text("\(event.sessions.flatMap { $0.messages }.count) 条记录")
                .font(.system(size: AdaptiveFont.footnote))
                .foregroundColor(DXYColors.textTertiary)
        }
    }
    
    private var timelineSection: some View {
        let items = viewModel.generateTimelineItems(for: event)
        
        return VStack(spacing: 0) {
            if items.isEmpty {
                emptyTimelineView
            } else {
                ForEach(Array(items.enumerated()), id: \.element.id) { index, item in
                    TimelineItemView(
                        item: item,
                        isFirst: index == 0,
                        isLast: index == items.count - 1
                    )
                }
            }
        }
        .padding(ScaleFactor.padding(16))
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
    }
    
    private var emptyTimelineView: some View {
        VStack(spacing: ScaleFactor.spacing(12)) {
            Image(systemName: "bubble.left.and.bubble.right")
                .font(.system(size: ScaleFactor.size(32)))
                .foregroundColor(DXYColors.textTertiary)
            
            Text("暂无对话记录")
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.textTertiary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, ScaleFactor.padding(40))
    }

    // MARK: - Notes Section

    private func notesSection(notes: String) -> some View {
        VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
            HStack {
                HStack(spacing: ScaleFactor.spacing(6)) {
                    Image(systemName: "note.text")
                        .font(.system(size: AdaptiveFont.body))
                        .foregroundColor(DXYColors.primaryPurple)
                    Text("我的备注")
                        .font(.system(size: AdaptiveFont.body, weight: .semibold))
                        .foregroundColor(DXYColors.textPrimary)
                }

                Spacer()

                Button(action: { showNoteEditor = true }) {
                    HStack(spacing: 4) {
                        Image(systemName: "pencil")
                        Text("编辑")
                    }
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.primaryPurple)
                }
            }

            Text(notes)
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.textPrimary)
                .lineSpacing(4)
                .padding(ScaleFactor.padding(12))
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(DXYColors.background)
                .clipShape(RoundedRectangle(cornerRadius: 8))
        }
        .padding(ScaleFactor.padding(16))
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
    }

    private var exportButton: some View {
        VStack(spacing: 0) {
            Divider()
            
            Button(action: { showExportConfig = true }) {
                HStack(spacing: ScaleFactor.spacing(8)) {
                    Image(systemName: "square.and.arrow.up")
                        .font(.system(size: AdaptiveFont.body, weight: .semibold))
                    Text("导出病历给医生")
                        .font(.system(size: AdaptiveFont.body, weight: .semibold))
                }
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, ScaleFactor.padding(16))
                .background(DXYColors.primaryPurple)
                .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
            }
            .padding(.horizontal, LayoutConstants.horizontalPadding)
            .padding(.vertical, ScaleFactor.padding(12))
            .background(Color.white)
        }
    }
}

#Preview {
    let mockAnalysis = AIAnalysis(
        chiefComplaint: "手臂出现红色皮疹，伴有瘙痒",
        symptoms: ["红色斑疹", "轻度瘙痒", "局部肿胀"],
        possibleDiagnosis: [
            Diagnosis(name: "过敏性皮炎", confidence: 0.78),
            Diagnosis(name: "湿疹", confidence: 0.15)
        ],
        recommendations: ["避免搔抓患处", "保持皮肤清洁干燥"],
        riskLevel: .medium as DossierRiskLevel,
        needOfflineVisit: true,
        visitUrgency: "建议3天内到皮肤科门诊就诊"
    )
    
    let mockEvent = MedicalEvent(
        title: "皮肤红疹",
        department: .dermatology,
        status: .inProgress,
        summary: "AI判断：过敏性皮炎",
        riskLevel: .medium as DossierRiskLevel,
        aiAnalysis: mockAnalysis
    )
    
    CompatibleNavigationStack {
        EventDetailView(event: mockEvent, viewModel: MedicalDossierViewModel())
    }
}
