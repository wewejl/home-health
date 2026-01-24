import SwiftUI

// MARK: - 病历详情视图（治愈系风格）
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
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 治愈系背景
                HealingEventDetailBackground(layout: layout)

                VStack(spacing: 0) {
                    ScrollView(.vertical, showsIndicators: false) {
                        VStack(spacing: layout.cardSpacing) {
                            // AI 摘要卡片
                            HealingEventAISummaryCard(
                                event: event,
                                viewModel: viewModel,
                                layout: layout
                            )

                            // AI 分析卡片
                            if let analysis = event.aiAnalysis {
                                HealingEventAIAnalysisCard(
                                    analysis: analysis,
                                    layout: layout
                                )
                            }

                            // 备注卡片
                            if let notes = event.notes, !notes.isEmpty {
                                HealingEventNotesCard(
                                    notes: notes,
                                    layout: layout
                                ) {
                                    showNoteEditor = true
                                }
                            }

                            // 相关病历
                            HealingEventRelatedSection(
                                viewModel: viewModel,
                                layout: layout
                            ) {
                                showMergeSheet = true
                            }

                            // 时间轴
                            HealingEventTimelineSection(
                                event: event,
                                viewModel: viewModel,
                                layout: layout
                            )
                        }
                        .padding(.horizontal, layout.horizontalPadding)
                        .padding(.top, layout.cardInnerPadding)
                        .padding(.bottom, 100)
                    }

                    // 导出按钮
                    HealingEventExportButton(layout: layout) {
                        showExportConfig = true
                    }
                }
            }
        }
        .navigationTitle(event.title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                HealingEventMoreMenu(
                    event: event,
                    viewModel: viewModel,
                    onEditNote: { showNoteEditor = true }
                )
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
}

// MARK: - 治愈系病历详情背景
struct HealingEventDetailBackground: View {
    let layout: AdaptiveLayout

    var body: some View {
        ZStack {
            // 渐变背景
            LinearGradient(
                colors: [
                    HealingColors.warmCream,
                    HealingColors.softPeach.opacity(0.4),
                    HealingColors.softSage.opacity(0.2)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            GeometryReader { geo in
                // 顶部装饰光晕
                Circle()
                    .fill(HealingColors.softSage.opacity(0.08))
                    .frame(width: layout.decorativeCircleSize * 0.5, height: layout.decorativeCircleSize * 0.5)
                    .offset(x: geo.size.width * 0.3, y: -geo.size.height * 0.15)
                    .ignoresSafeArea()

                // 底部装饰光晕
                Circle()
                    .fill(HealingColors.mutedCoral.opacity(0.04))
                    .frame(width: layout.decorativeCircleSize * 0.4, height: layout.decorativeCircleSize * 0.4)
                    .offset(x: -geo.size.width * 0.4, y: geo.size.height * 0.2)
                    .ignoresSafeArea()
            }
        }
    }
}

// MARK: - 治愈系 AI 摘要卡片
struct HealingEventAISummaryCard: View {
    let event: MedicalEvent
    @ObservedObject var viewModel: MedicalDossierViewModel
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            // 标题栏
            HStack {
                HStack(spacing: layout.cardSpacing / 3) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.forestMist.opacity(0.15))
                            .frame(width: layout.iconSmallSize + 6, height: layout.iconSmallSize + 6)

                        Image(systemName: "brain.head.profile")
                            .font(.system(size: 14))
                            .foregroundColor(HealingColors.forestMist)
                    }

                    Text("AI 智能摘要")
                        .font(.system(size: layout.bodyFontSize, weight: .semibold))
                        .foregroundColor(HealingColors.textPrimary)
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
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.forestMist)
                }
                .disabled(viewModel.isGeneratingSummary)
            }

            // 内容区域
            Group {
                if viewModel.isGeneratingSummary {
                    HStack {
                        Spacer()
                        VStack(spacing: layout.cardSpacing / 2) {
                            ProgressView()
                                .tint(HealingColors.forestMist)
                            Text("正在生成摘要...")
                                .font(.system(size: layout.captionFontSize + 1))
                                .foregroundColor(HealingColors.textSecondary)
                        }
                        Spacer()
                    }
                    .padding(.vertical, layout.cardInnerPadding)
                } else if let summary = viewModel.currentSummary {
                    HealingAISummaryContent(summary: summary, layout: layout)
                } else if let error = viewModel.summaryError {
                    Text(error)
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.terracotta)
                        .padding(.vertical, layout.cardSpacing)
                } else {
                    Button(action: {
                        Task {
                            await viewModel.generateAISummary(for: event.id)
                        }
                    }) {
                        HStack(spacing: layout.cardSpacing / 2) {
                            Image(systemName: "sparkles")
                            Text("生成 AI 摘要")
                        }
                        .font(.system(size: layout.bodyFontSize - 1, weight: .semibold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, layout.cardInnerPadding)
                        .background(
                            LinearGradient(
                                colors: [HealingColors.forestMist, HealingColors.deepSage],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                        .shadow(color: HealingColors.forestMist.opacity(0.3), radius: 6, y: 3)
                    }
                }
            }
        }
        .padding(layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(HealingColors.softSage.opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - 治愈系 AI 摘要内容
struct HealingAISummaryContent: View {
    let summary: AISummaryResponse
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            // 摘要文本
            if let summaryText = summary.summary {
                Text(summaryText)
                    .font(.system(size: layout.captionFontSize + 1))
                    .foregroundColor(HealingColors.textPrimary)
                    .lineSpacing(4)
            }

            // 关键点
            if let keyPoints = summary.key_points, !keyPoints.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("关键点")
                        .font(.system(size: layout.captionFontSize, weight: .medium))
                        .foregroundColor(HealingColors.textSecondary)

                    ForEach(keyPoints, id: \.self) { point in
                        HStack(alignment: .top, spacing: 6) {
                            Circle()
                                .fill(HealingColors.dustyBlue)
                                .frame(width: 5, height: 5)
                                .padding(.top, 5)
                            Text(point)
                                .font(.system(size: layout.captionFontSize))
                                .foregroundColor(HealingColors.textPrimary)
                        }
                    }
                }
            }

            // 症状标签
            if let symptoms = summary.symptoms, !symptoms.isEmpty {
                FlowLayout(spacing: 6) {
                    ForEach(symptoms, id: \.self) { symptom in
                        Text(symptom)
                            .font(.system(size: layout.captionFontSize))
                            .foregroundColor(HealingColors.dustyBlue)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .background(HealingColors.dustyBlue.opacity(0.15))
                            .clipShape(Capsule())
                    }
                }
            }

            // 风险等级
            if let riskLevel = summary.risk_level {
                HStack(spacing: layout.cardSpacing / 3) {
                    ZStack {
                        Circle()
                            .fill(riskColor(for: riskLevel).opacity(0.15))
                            .frame(width: layout.iconSmallSize - 2, height: layout.iconSmallSize - 2)

                        Image(systemName: riskIcon(for: riskLevel))
                            .font(.system(size: 10))
                            .foregroundColor(riskColor(for: riskLevel))
                    }

                    Text("风险等级: \(riskDisplayName(for: riskLevel))")
                        .font(.system(size: layout.captionFontSize, weight: .medium))
                        .foregroundColor(riskColor(for: riskLevel))
                }
            }

            // 建议
            if let recommendations = summary.recommendations, !recommendations.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("建议")
                        .font(.system(size: layout.captionFontSize, weight: .medium))
                        .foregroundColor(HealingColors.textSecondary)

                    ForEach(Array(recommendations.enumerated()), id: \.offset) { index, rec in
                        HStack(alignment: .top, spacing: 6) {
                            Text("\(index + 1).")
                                .font(.system(size: layout.captionFontSize))
                                .foregroundColor(HealingColors.textTertiary)
                            Text(rec)
                                .font(.system(size: layout.captionFontSize))
                                .foregroundColor(HealingColors.textPrimary)
                        }
                    }
                }
            }
        }
    }

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
        case "low": return HealingColors.forestMist
        case "medium": return HealingColors.warmSand
        case "high": return HealingColors.terracotta
        case "emergency": return Color.red
        default: return HealingColors.textTertiary
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
}

// MARK: - 治愈系 AI 分析卡片
struct HealingEventAIAnalysisCard: View {
    let analysis: AIAnalysis
    let layout: AdaptiveLayout

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            // 标题
            HStack(spacing: layout.cardSpacing / 3) {
                ZStack {
                    Circle()
                        .fill(HealingColors.mutedCoral.opacity(0.15))
                        .frame(width: layout.iconSmallSize + 6, height: layout.iconSmallSize + 6)

                    Image(systemName: "stethoscope")
                        .font(.system(size: 14))
                        .foregroundColor(HealingColors.mutedCoral)
                }

                Text("AI 分析")
                    .font(.system(size: layout.bodyFontSize, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)
            }

            // 主诉
            if !analysis.chiefComplaint.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("主诉")
                        .font(.system(size: layout.captionFontSize, weight: .medium))
                        .foregroundColor(HealingColors.textSecondary)

                    Text(analysis.chiefComplaint)
                        .font(.system(size: layout.captionFontSize + 1))
                        .foregroundColor(HealingColors.textPrimary)
                        .padding(layout.cardInnerPadding - 2)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(HealingColors.warmCream.opacity(0.6))
                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                }
            }

            // 可能诊断
            if !analysis.possibleDiagnosis.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("可能诊断")
                        .font(.system(size: layout.captionFontSize, weight: .medium))
                        .foregroundColor(HealingColors.textSecondary)

                    ForEach(analysis.possibleDiagnosis, id: \.name) { diagnosis in
                        HStack {
                            Text(diagnosis.name)
                                .font(.system(size: layout.captionFontSize + 1))
                                .foregroundColor(HealingColors.textPrimary)

                            Spacer()

                            Text("\(Int(diagnosis.confidence * 100))%")
                                .font(.system(size: layout.captionFontSize, weight: .medium))
                                .foregroundColor(confidenceColor(diagnosis.confidence))
                        }
                        .padding(layout.cardInnerPadding - 2)
                        .background(HealingColors.warmCream.opacity(0.4))
                        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                    }
                }
            }

            // 风险等级
            HStack(spacing: layout.cardSpacing / 3) {
                Text("风险等级")
                    .font(.system(size: layout.captionFontSize, weight: .medium))
                    .foregroundColor(HealingColors.textSecondary)

                Spacer()

                HStack(spacing: 4) {
                    Image(systemName: riskIcon(for: analysis.riskLevel))
                        .font(.system(size: 12))
                    Text(riskDisplayName(for: analysis.riskLevel))
                        .font(.system(size: layout.captionFontSize, weight: .medium))
                }
                .foregroundColor(riskColor(for: analysis.riskLevel))
                .padding(.horizontal, 10)
                .padding(.vertical, 4)
                .background(riskColor(for: analysis.riskLevel).opacity(0.15))
                .clipShape(Capsule())
            }

            // 就医建议
            if let urgency = analysis.visitUrgency {
                HStack(spacing: layout.cardSpacing / 3) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.dustyBlue.opacity(0.15))
                            .frame(width: layout.iconSmallSize - 2, height: layout.iconSmallSize - 2)

                        Image(systemName: "calendar.badge.plus")
                            .font(.system(size: 10))
                            .foregroundColor(HealingColors.dustyBlue)
                    }

                    Text(urgency)
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.textPrimary)
                }
            }
        }
        .padding(layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(HealingColors.mutedCoral.opacity(0.2), lineWidth: 1)
        )
    }

    private func riskIcon(for level: DossierRiskLevel) -> String {
        switch level {
        case .low: return "checkmark.circle.fill"
        case .medium: return "exclamationmark.circle.fill"
        case .high: return "exclamationmark.triangle.fill"
        case .emergency: return "xmark.octagon.fill"
        }
    }

    private func riskColor(for level: DossierRiskLevel) -> Color {
        switch level {
        case .low: return HealingColors.forestMist
        case .medium: return HealingColors.warmSand
        case .high: return HealingColors.terracotta
        case .emergency: return Color.red
        }
    }

    private func riskDisplayName(for level: DossierRiskLevel) -> String {
        switch level {
        case .low: return "低风险"
        case .medium: return "中风险"
        case .high: return "高风险"
        case .emergency: return "紧急"
        }
    }

    private func confidenceColor(_ confidence: Double) -> Color {
        if confidence >= 0.7 { return HealingColors.forestMist }
        if confidence >= 0.4 { return HealingColors.warmSand }
        return HealingColors.textTertiary
    }
}

// MARK: - 治愈系备注卡片
struct HealingEventNotesCard: View {
    let notes: String
    let layout: AdaptiveLayout
    let onEdit: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: layout.cardSpacing) {
            HStack {
                HStack(spacing: layout.cardSpacing / 3) {
                    ZStack {
                        Circle()
                            .fill(HealingColors.dustyBlue.opacity(0.15))
                            .frame(width: layout.iconSmallSize + 6, height: layout.iconSmallSize + 6)

                        Image(systemName: "note.text")
                            .font(.system(size: 14))
                            .foregroundColor(HealingColors.dustyBlue)
                    }

                    Text("我的备注")
                        .font(.system(size: layout.bodyFontSize, weight: .semibold))
                        .foregroundColor(HealingColors.textPrimary)
                }

                Spacer()

                Button(action: onEdit) {
                    HStack(spacing: 4) {
                        Image(systemName: "pencil")
                        Text("编辑")
                    }
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.dustyBlue)
                }
            }

            Text(notes)
                .font(.system(size: layout.captionFontSize + 1))
                .foregroundColor(HealingColors.textPrimary)
                .lineSpacing(4)
                .padding(layout.cardInnerPadding - 2)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(HealingColors.warmCream.opacity(0.6))
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        }
        .padding(layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(HealingColors.dustyBlue.opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - 治愈系相关病历区域
struct HealingEventRelatedSection: View {
    @ObservedObject var viewModel: MedicalDossierViewModel
    let layout: AdaptiveLayout
    let onMergeTap: () -> Void

    var body: some View {
        Group {
            if viewModel.isLoadingRelated {
                VStack(spacing: layout.cardSpacing) {
                    ProgressView()
                        .tint(HealingColors.forestMist)
                    Text("加载相关病历...")
                        .font(.system(size: layout.captionFontSize + 1))
                        .foregroundColor(HealingColors.textSecondary)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, layout.cardInnerPadding * 2)
                .background(HealingColors.cardBackground)
                .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
            } else if !viewModel.relatedEvents.isEmpty {
                VStack(alignment: .leading, spacing: layout.cardSpacing) {
                    HStack {
                        HStack(spacing: layout.cardSpacing / 3) {
                            ZStack {
                                Circle()
                                    .fill(HealingColors.forestMist.opacity(0.15))
                                    .frame(width: layout.iconSmallSize + 6, height: layout.iconSmallSize + 6)

                                Image(systemName: "link")
                                    .font(.system(size: 14))
                                    .foregroundColor(HealingColors.forestMist)
                            }

                            Text("相关病历")
                                .font(.system(size: layout.bodyFontSize, weight: .semibold))
                                .foregroundColor(HealingColors.textPrimary)
                        }

                        Spacer()

                        Button(action: onMergeTap) {
                            HStack(spacing: 4) {
                                Image(systemName: "arrow.triangle.merge")
                                Text("合并")
                            }
                            .font(.system(size: layout.captionFontSize))
                            .foregroundColor(HealingColors.forestMist)
                        }
                    }

                    ForEach(viewModel.relatedEvents) { relatedEvent in
                        HealingRelatedEventRow(relatedEvent: relatedEvent, layout: layout)
                    }
                }
                .padding(layout.cardInnerPadding)
                .background(HealingColors.cardBackground)
                .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
                .overlay(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(HealingColors.softSage.opacity(0.2), lineWidth: 1)
                )
            }
        }
    }
}

// MARK: - 治愈系相关病历行
struct HealingRelatedEventRow: View {
    let relatedEvent: FindRelatedResponse.RelatedEvent
    let layout: AdaptiveLayout

    var body: some View {
        HStack(spacing: layout.cardSpacing / 2) {
            // 关系类型圆点
            ZStack {
                Circle()
                    .fill(relationColor.opacity(0.15))
                    .frame(width: layout.iconSmallSize + 10, height: layout.iconSmallSize + 10)

                Circle()
                    .fill(relationColor)
                    .frame(width: 8, height: 8)
            }

            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: layout.cardSpacing / 3) {
                    Text(relatedEvent.event_id.prefix(8) + "...")
                        .font(.system(size: layout.captionFontSize + 1, weight: .medium))
                        .foregroundColor(HealingColors.textPrimary)

                    if let relationType = relatedEvent.relation_type {
                        Text(relationDisplayName(relationType))
                            .font(.system(size: layout.captionFontSize - 1))
                            .foregroundColor(.white)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(relationColor)
                            .clipShape(Capsule())
                    }
                }

                if let reasoning = relatedEvent.reasoning {
                    Text(reasoning)
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.textSecondary)
                        .lineLimit(2)
                }

                if let confidence = relatedEvent.confidence {
                    HStack(spacing: 4) {
                        Image(systemName: "chart.bar.fill")
                            .font(.system(size: 10))
                        Text("置信度: \(Int(confidence * 100))%")
                            .font(.system(size: layout.captionFontSize - 1))
                    }
                    .foregroundColor(HealingColors.textTertiary)
                }
            }

            Spacer()

            Image(systemName: "chevron.right")
                .font(.system(size: layout.captionFontSize))
                .foregroundColor(HealingColors.textTertiary)
        }
        .padding(layout.cardInnerPadding - 2)
        .background(HealingColors.warmCream.opacity(0.5))
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    private var relationColor: Color {
        guard let relationType = relatedEvent.relation_type else {
            return HealingColors.textTertiary
        }

        switch relationType {
        case "same_condition": return HealingColors.forestMist
        case "follow_up": return HealingColors.dustyBlue
        case "complication": return HealingColors.terracotta
        case "unrelated": return HealingColors.textTertiary
        default: return HealingColors.textSecondary
        }
    }

    private func relationDisplayName(_ type: String) -> String {
        switch type {
        case "same_condition": return "同一病情"
        case "follow_up": return "随访"
        case "complication": return "并发症"
        case "unrelated": return "不相关"
        default: return type
        }
    }
}

// MARK: - 治愈系时间轴区域
struct HealingEventTimelineSection: View {
    let event: MedicalEvent
    @ObservedObject var viewModel: MedicalDossierViewModel
    let layout: AdaptiveLayout

    var body: some View {
        let items = viewModel.generateTimelineItems(for: event)

        return VStack(alignment: .leading, spacing: layout.cardSpacing) {
            // 标题
            HStack(spacing: layout.cardSpacing / 3) {
                ZStack {
                    Circle()
                        .fill(HealingColors.deepSage.opacity(0.15))
                        .frame(width: layout.iconSmallSize + 6, height: layout.iconSmallSize + 6)

                    Image(systemName: "clock.arrow.circlepath")
                        .font(.system(size: 14))
                        .foregroundColor(HealingColors.deepSage)
                }

                Text("时间轴")
                    .font(.system(size: layout.bodyFontSize, weight: .semibold))
                    .foregroundColor(HealingColors.textPrimary)

                Spacer()

                Text("\(event.sessions.flatMap { $0.messages }.count) 条记录")
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.textTertiary)
            }

            // 时间轴内容
            Group {
                if items.isEmpty {
                    VStack(spacing: layout.cardSpacing) {
                        Image(systemName: "bubble.left.and.bubble.right")
                            .font(.system(size: layout.bodyFontSize + 8, weight: .light))
                            .foregroundColor(HealingColors.textTertiary)

                        Text("暂无对话记录")
                            .font(.system(size: layout.captionFontSize + 1))
                            .foregroundColor(HealingColors.textTertiary)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, layout.cardInnerPadding * 2)
                } else {
                    VStack(spacing: 0) {
                        ForEach(Array(items.enumerated()), id: \.element.id) { index, item in
                            HealingTimelineItemRow(
                                item: item,
                                isFirst: index == 0,
                                isLast: index == items.count - 1,
                                layout: layout
                            )
                        }
                    }
                }
            }
        }
        .padding(layout.cardInnerPadding)
        .background(HealingColors.cardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(HealingColors.deepSage.opacity(0.2), lineWidth: 1)
        )
    }
}

// MARK: - 治愈系时间轴项
struct HealingTimelineItemRow: View {
    let item: TimelineItem
    let isFirst: Bool
    let isLast: Bool
    let layout: AdaptiveLayout

    var body: some View {
        HStack(alignment: .top, spacing: layout.cardSpacing / 2) {
            // 时间轴线
            VStack(spacing: 0) {
                if !isFirst {
                    Rectangle()
                        .fill(HealingColors.softSage.opacity(0.3))
                        .frame(width: 2)
                }

                ZStack {
                    Circle()
                        .fill(HealingColors.warmCream)
                        .frame(width: layout.iconSmallSize - 18, height: layout.iconSmallSize - 18)

                    Circle()
                        .fill(itemColor)
                        .frame(width: 8, height: 8)
                }

                if !isLast {
                    Rectangle()
                        .fill(HealingColors.softSage.opacity(0.3))
                        .frame(width: 2)
                }
            }
            .padding(.vertical, 4)

            // 内容
            VStack(alignment: .leading, spacing: 4) {
                Text(dateText)
                    .font(.system(size: layout.captionFontSize, weight: .medium))
                    .foregroundColor(HealingColors.textSecondary)

                ForEach(item.contents) { content in
                    contentItemView(for: content)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(.vertical, 8)
    }

    @ViewBuilder
    private func contentItemView(for content: TimelineContent) -> some View {
        switch content.type {
        case .userMessage:
            if let message = content.message {
                HStack(spacing: 4) {
                    Image(systemName: "person.circle.fill")
                        .font(.system(size: 12))
                        .foregroundColor(HealingColors.textTertiary)
                    Text(message.content)
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.textPrimary)
                        .lineLimit(3)
                }
            }
        case .aiMessage:
            if let message = content.message {
                HStack(spacing: 4) {
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 12))
                        .foregroundColor(HealingColors.forestMist)
                    Text(message.content)
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.textPrimary)
                        .lineLimit(3)
                }
            }
        case .attachment:
            HStack(spacing: 4) {
                Image(systemName: "paperclip")
                    .font(.system(size: 12))
                    .foregroundColor(HealingColors.dustyBlue)
                if let attachment = content.attachment {
                    Text(attachment.fileName ?? attachment.type.rawValue)
                        .font(.system(size: layout.captionFontSize))
                        .foregroundColor(HealingColors.textPrimary)
                }
            }
        case .sessionStart:
            HStack(spacing: 4) {
                Image(systemName: "play.circle.fill")
                    .font(.system(size: 12))
                    .foregroundColor(HealingColors.forestMist)
                Text("对话开始")
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.textSecondary)
            }
        case .sessionEnd:
            HStack(spacing: 4) {
                Image(systemName: "stop.circle.fill")
                    .font(.system(size: 12))
                    .foregroundColor(HealingColors.textTertiary)
                Text("对话结束")
                    .font(.system(size: layout.captionFontSize))
                    .foregroundColor(HealingColors.textSecondary)
            }
        }
    }

    private var itemColor: Color {
        if let firstContent = item.contents.first {
            switch firstContent.type {
            case .userMessage: return HealingColors.textTertiary
            case .aiMessage: return HealingColors.forestMist
            case .attachment: return HealingColors.dustyBlue
            case .sessionStart: return HealingColors.forestMist
            case .sessionEnd: return HealingColors.textTertiary
            }
        }
        return HealingColors.textTertiary
    }

    private var dateText: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "MM-dd HH:mm"
        formatter.locale = Locale(identifier: "zh_CN")
        return formatter.string(from: item.date)
    }
}

// MARK: - 治愈系导出按钮
struct HealingEventExportButton: View {
    let layout: AdaptiveLayout
    let action: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            Rectangle()
                .fill(HealingColors.softSage.opacity(0.3))
                .frame(height: 1)

            Button(action: action) {
                HStack(spacing: layout.cardSpacing / 2) {
                    Image(systemName: "square.and.arrow.up")
                        .font(.system(size: layout.bodyFontSize, weight: .semibold))

                    Text("导出病历给医生")
                        .font(.system(size: layout.bodyFontSize, weight: .semibold))
                }
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, layout.cardInnerPadding + 2)
                .background(
                    LinearGradient(
                        colors: [HealingColors.forestMist, HealingColors.deepSage],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                .shadow(color: HealingColors.forestMist.opacity(0.4), radius: 8, y: 3)
            }
            .padding(.horizontal, layout.horizontalPadding)
            .padding(.vertical, layout.cardSpacing)
            .background(HealingColors.cardBackground.opacity(0.9))
        }
    }
}

// MARK: - 治愈系更多操作菜单
struct HealingEventMoreMenu: View {
    let event: MedicalEvent
    @ObservedObject var viewModel: MedicalDossierViewModel
    let onEditNote: () -> Void
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        Menu {
            Button(action: {}) {
                Label("编辑标题", systemImage: "pencil")
            }

            Button(action: onEditNote) {
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
                .font(.system(size: layout.bodyFontSize + 2))
                .foregroundColor(HealingColors.forestMist)
        }
    }

    private var layout: AdaptiveLayout {
        AdaptiveLayout(screenWidth: UIScreen.main.bounds.width)
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
