import SwiftUI



struct MergeEventsSheet: View {

    let currentEventId: String

    let relatedEvents: [FindRelatedResponse.RelatedEvent]

    @ObservedObject var viewModel: MedicalDossierViewModel

    let onMerge: ([String], String?) -> Void

    

    @State private var selectedEventIds: Set<String> = []

    @State private var newTitle: String = ""

    @Environment(\.dismiss) private var dismiss

    

    var body: some View {

        NavigationStack {

            VStack(spacing: 0) {

                ScrollView {

                    VStack(alignment: .leading, spacing: ScaleFactor.spacing(20)) {

                        // 说明文字

                        VStack(alignment: .leading, spacing: 8) {

                            Text("合并病历事件")

                                .font(.system(size: AdaptiveFont.title3, weight: .bold))

                                .foregroundColor(DossierColors.textPrimary)

                            

                            Text("选择要合并的相关病历，合并后的事件将包含所有选中事件的记录。")

                                .font(.system(size: AdaptiveFont.subheadline))

                                .foregroundColor(DossierColors.textSecondary)

                        }

                        .padding(.horizontal, LayoutConstants.horizontalPadding)

                        .padding(.top, ScaleFactor.padding(16))

                        

                        // 当前事件

                        VStack(alignment: .leading, spacing: 8) {

                            Text("当前事件")

                                .font(.system(size: AdaptiveFont.footnote, weight: .medium))

                                .foregroundColor(DossierColors.textTertiary)

                            

                            HStack {

                                Image(systemName: "checkmark.circle.fill")

                                    .foregroundColor(DossierColors.primaryPurple)

                                Text(currentEventId.prefix(12) + "...")

                                    .font(.system(size: AdaptiveFont.subheadline))

                                    .foregroundColor(DossierColors.textPrimary)

                                Spacer()

                                Text("主事件")

                                    .font(.system(size: AdaptiveFont.caption1))

                                    .foregroundColor(.white)

                                    .padding(.horizontal, 8)

                                    .padding(.vertical, 4)

                                    .background(DossierColors.primaryPurple)

                                    .clipShape(Capsule())

                            }

                            .padding(ScaleFactor.padding(12))

                            .background(DossierColors.primaryPurple.opacity(0.1))

                            .clipShape(RoundedRectangle(cornerRadius: 8))

                        }

                        .padding(.horizontal, LayoutConstants.horizontalPadding)

                        

                        // 相关事件列表

                        VStack(alignment: .leading, spacing: 8) {

                            Text("选择要合并的事件")

                                .font(.system(size: AdaptiveFont.footnote, weight: .medium))

                                .foregroundColor(DossierColors.textTertiary)

                            

                            if relatedEvents.isEmpty {

                                HStack {

                                    Spacer()

                                    VStack(spacing: 8) {

                                        Image(systemName: "doc.on.doc")

                                            .font(.system(size: UnifiedFont.largeTitle))

                                            .foregroundColor(DossierColors.textTertiary)

                                        Text("没有找到相关事件")

                                            .font(.system(size: AdaptiveFont.subheadline))

                                            .foregroundColor(DossierColors.textTertiary)

                                    }

                                    Spacer()

                                }

                                .padding(.vertical, ScaleFactor.padding(30))

                            } else {

                                ForEach(relatedEvents) { event in

                                    SelectableEventRow(

                                        event: event,

                                        isSelected: selectedEventIds.contains(event.event_id),

                                        onTap: {

                                            if selectedEventIds.contains(event.event_id) {

                                                selectedEventIds.remove(event.event_id)

                                            } else {

                                                selectedEventIds.insert(event.event_id)

                                            }

                                        }

                                    )

                                }

                            }

                        }

                        .padding(.horizontal, LayoutConstants.horizontalPadding)

                        

                        // 新标题输入

                        VStack(alignment: .leading, spacing: 8) {

                            Text("合并后的标题（可选）")

                                .font(.system(size: AdaptiveFont.footnote, weight: .medium))

                                .foregroundColor(DossierColors.textTertiary)

                            

                            TextField("输入新标题...", text: $newTitle)

                                .font(.system(size: AdaptiveFont.body))

                                .padding(ScaleFactor.padding(12))

                                .background(DossierColors.background)

                                .clipShape(RoundedRectangle(cornerRadius: 8))

                        }

                        .padding(.horizontal, LayoutConstants.horizontalPadding)

                    }

                    .padding(.bottom, ScaleFactor.padding(100))

                }

                

                // 底部按钮

                VStack(spacing: 0) {

                    Divider()

                    

                    HStack(spacing: ScaleFactor.spacing(12)) {

                        Button(action: { dismiss() }) {

                            Text("取消")

                                .font(.system(size: AdaptiveFont.body, weight: .medium))

                                .foregroundColor(DossierColors.textSecondary)

                                .frame(maxWidth: .infinity)

                                .padding(.vertical, ScaleFactor.padding(14))

                                .background(DossierColors.background)

                                .clipShape(RoundedRectangle(cornerRadius: 8))

                        }

                        

                        Button(action: {

                            var eventIds = [currentEventId]

                            eventIds.append(contentsOf: selectedEventIds)

                            onMerge(eventIds, newTitle.isEmpty ? nil : newTitle)

                        }) {

                            HStack(spacing: 6) {

                                if viewModel.isMerging {

                                    ProgressView()

                                        .tint(.white)

                                        .scaleEffect(0.8)

                                } else {

                                    Image(systemName: "arrow.triangle.merge")

                                }

                                Text("合并 (\(selectedEventIds.count + 1))")

                            }

                            .font(.system(size: AdaptiveFont.body, weight: .semibold))

                            .foregroundColor(.white)

                            .frame(maxWidth: .infinity)

                            .padding(.vertical, ScaleFactor.padding(14))

                            .background(selectedEventIds.isEmpty ? DossierColors.textTertiary : DossierColors.primaryPurple)

                            .clipShape(RoundedRectangle(cornerRadius: 8))

                        }

                        .disabled(selectedEventIds.isEmpty || viewModel.isMerging)

                    }

                    .padding(.horizontal, LayoutConstants.horizontalPadding)

                    .padding(.vertical, ScaleFactor.padding(12))

                    .background(Color.white)

                }

            }

            .background(Color.white)

            .navigationBarTitleDisplayMode(.inline)

            .toolbar {

                ToolbarItem(placement: .navigationBarTrailing) {

                    Button(action: { dismiss() }) {

                        Image(systemName: "xmark.circle.fill")

                            .foregroundColor(DossierColors.textTertiary)

                    }

                }

            }

        }

    }

}



struct SelectableEventRow: View {

    let event: FindRelatedResponse.RelatedEvent

    let isSelected: Bool

    let onTap: () -> Void

    

    var body: some View {

        Button(action: onTap) {

            HStack(spacing: ScaleFactor.spacing(12)) {

                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")

                    .font(.system(size: UnifiedFont.title1))

                    .foregroundColor(isSelected ? DossierColors.primaryPurple : DossierColors.textTertiary)

                

                VStack(alignment: .leading, spacing: 4) {

                    Text(event.event_id.prefix(12) + "...")

                        .font(.system(size: AdaptiveFont.subheadline, weight: .medium))

                        .foregroundColor(DossierColors.textPrimary)

                    

                    if let reasoning = event.reasoning {

                        Text(reasoning)

                            .font(.system(size: AdaptiveFont.footnote))

                            .foregroundColor(DossierColors.textSecondary)

                            .lineLimit(1)

                    }

                }

                

                Spacer()

                

                if let relationType = event.relation_type {

                    Text(relationDisplayName(relationType))

                        .font(.system(size: AdaptiveFont.caption1))

                        .foregroundColor(relationColor(relationType))

                        .padding(.horizontal, 6)

                        .padding(.vertical, 2)

                        .background(relationColor(relationType).opacity(0.1))

                        .clipShape(Capsule())

                }

            }

            .padding(ScaleFactor.padding(12))

            .background(isSelected ? DossierColors.primaryPurple.opacity(0.05) : DossierColors.background)

            .clipShape(RoundedRectangle(cornerRadius: 8))

            .overlay(

                RoundedRectangle(cornerRadius: 8)

                    .stroke(isSelected ? DossierColors.primaryPurple : Color.clear, lineWidth: 1)

            )

        }

        .buttonStyle(PlainButtonStyle())

    }

    

    private func relationDisplayName(_ type: String) -> String {

        switch type {

        case "same_condition": return "同一病情"

        case "follow_up": return "随访"

        case "complication": return "并发症"

        default: return type

        }

    }

    

    private func relationColor(_ type: String) -> Color {

        switch type {

        case "same_condition": return DossierColors.primaryPurple

        case "follow_up": return DossierColors.teal

        case "complication": return Color.orange

        default: return DossierColors.textSecondary

        }

    }

}



#Preview {

    let mockEvents = [

        FindRelatedResponse.RelatedEvent(

            event_id: "event-001-abc",

            relation_type: "same_condition",

            confidence: 0.92,

            reasoning: "同一天的皮肤科问诊"

        ),

        FindRelatedResponse.RelatedEvent(

            event_id: "event-002-def",

            relation_type: "follow_up",

            confidence: 0.85,

            reasoning: "3天后的复诊记录"

        )

    ]

    ;



    VStack MergeEventsSheet(;

        currentEventId: "current-event-xyz",

        relatedEvents: mockEvents,

        viewModel: MedicalDossierViewModel(),

        onMerge: { _, _ in }

    )

}
