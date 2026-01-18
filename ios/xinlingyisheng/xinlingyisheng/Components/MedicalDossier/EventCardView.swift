import SwiftUI

struct EventCardView: View {
    let event: MedicalEvent
    var onTap: (() -> Void)?
    
    @State private var isPressed = false
    
    var body: some View {
        Button(action: { onTap?() }) {
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(12)) {
                headerSection
                
                Divider()
                    .background(DossierColors.divider)
                
                summarySection
                
                attachmentSection
            }
            .padding(ScaleFactor.padding(16))
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
            .shadow(color: Color.black.opacity(0.06), radius: 12, x: 0, y: 4)
        }
        .buttonStyle(PlainButtonStyle())
        .scaleEffect(isPressed ? 0.98 : 1.0)
        .animation(.easeInOut(duration: 0.15), value: isPressed)
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in isPressed = true }
                .onEnded { _ in isPressed = false }
        )
    }
    
    private var headerSection: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            departmentIcon
            
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(2)) {
                Text(event.title)
                    .font(.system(size: AdaptiveFont.body, weight: .semibold))
                    .foregroundColor(DXYColors.textPrimary)
                    .lineLimit(1)
                
                Text("\(event.department.displayName) · \(event.dateRangeText)")
                    .font(.system(size: AdaptiveFont.footnote))
                    .foregroundColor(DXYColors.textTertiary)
            }
            
            Spacer()
            
            DossierRiskLevelBadge(riskLevel: event.riskLevel)
        }
    }
    
    private var departmentIcon: some View {
        Circle()
            .fill(event.department.color.opacity(0.15))
            .frame(width: ScaleFactor.size(36), height: ScaleFactor.size(36))
            .overlay(
                Image(systemName: event.department.icon)
                    .font(.system(size: AdaptiveFont.body))
                    .foregroundColor(event.department.color)
            )
    }
    
    private var summarySection: some View {
        Text(event.summary)
            .font(.system(size: AdaptiveFont.subheadline))
            .foregroundColor(DXYColors.textSecondary)
            .lineLimit(2)
            .lineSpacing(4)
    }
    
    @ViewBuilder
    private var attachmentSection: some View {
        if event.photoCount > 0 || event.reportCount > 0 {
            HStack(spacing: ScaleFactor.spacing(12)) {
                if event.photoCount > 0 {
                    AttachmentCountBadge(icon: "camera.fill", count: event.photoCount)
                }
                if event.reportCount > 0 {
                    AttachmentCountBadge(icon: "doc.text.fill", count: event.reportCount)
                }
                
                Spacer()
                
                if event.status == .exported {
                    HStack(spacing: ScaleFactor.spacing(4)) {
                        Image(systemName: "checkmark.circle.fill")
                            .font(.system(size: AdaptiveFont.caption))
                        Text("已导出")
                            .font(.system(size: AdaptiveFont.caption))
                    }
                    .foregroundColor(DossierColors.statusExported)
                }
            }
        }
    }
}

struct SwipeableEventCard: View {
    let event: MedicalEvent
    var onTap: (() -> Void)?
    var onArchive: (() -> Void)?
    var onDelete: (() -> Void)?
    
    @State private var offset: CGFloat = 0
    @State private var showingActions = false
    
    var body: some View {
        ZStack(alignment: .trailing) {
            HStack(spacing: 0) {
                Button(action: { onArchive?() }) {
                    VStack(spacing: 4) {
                        Image(systemName: "archivebox")
                            .font(.system(size: 20))
                        Text("归档")
                            .font(.system(size: 12))
                    }
                    .foregroundColor(.white)
                    .frame(width: 70)
                    .frame(maxHeight: .infinity)
                    .background(Color.orange)
                }
                
                Button(action: { onDelete?() }) {
                    VStack(spacing: 4) {
                        Image(systemName: "trash")
                            .font(.system(size: 20))
                        Text("删除")
                            .font(.system(size: 12))
                    }
                    .foregroundColor(.white)
                    .frame(width: 70)
                    .frame(maxHeight: .infinity)
                    .background(Color.red)
                }
            }
            .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius, style: .continuous))
            
            EventCardView(event: event, onTap: onTap)
                .offset(x: offset)
                .gesture(
                    DragGesture()
                        .onChanged { value in
                            if value.translation.width < 0 {
                                offset = value.translation.width
                            }
                        }
                        .onEnded { value in
                            withAnimation(.spring(response: 0.3)) {
                                if value.translation.width < -100 {
                                    offset = -140
                                    showingActions = true
                                } else {
                                    offset = 0
                                    showingActions = false
                                }
                            }
                        }
                )
                .onTapGesture {
                    if showingActions {
                        withAnimation(.spring(response: 0.3)) {
                            offset = 0
                            showingActions = false
                        }
                    }
                }
        }
    }
}

#Preview {
    let mockEvent = MedicalEvent(
        title: "皮肤红疹",
        department: .dermatology,
        status: .inProgress,
        createdAt: Date().addingTimeInterval(-259200),
        updatedAt: Date(),
        summary: "AI判断：过敏性皮炎，建议观察病情变化后就医",
        riskLevel: .medium,
        attachments: [
            Attachment(type: .image, url: "test1"),
            Attachment(type: .image, url: "test2"),
            Attachment(type: .image, url: "test3"),
            Attachment(type: .image, url: "test4"),
            Attachment(type: .report, url: "report1")
        ]
    )
    
    return VStack(spacing: 16) {
        EventCardView(event: mockEvent)
        SwipeableEventCard(event: mockEvent)
    }
    .padding()
    .background(DXYColors.background)
}
