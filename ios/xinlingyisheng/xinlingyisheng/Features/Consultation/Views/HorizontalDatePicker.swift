import SwiftUI

// MARK: - 横向日期选择器

struct HorizontalDatePicker: View {
    @Binding var selectedDate: Date
    var onDateChanged: ((Date) -> Void)?

    private var calendar = Calendar.current
    private let daysToShow = 7

    init(selectedDate: Binding<Date>, onDateChanged: ((Date) -> Void)? = nil) {
        self._selectedDate = selectedDate
        self.onDateChanged = onDateChanged
    }

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(generateDates(), id: \.self) { date in
                    DateChip(
                        date: date,
                        isSelected: isSameDay(date, selectedDate)
                    ) {
                        withAnimation(.easeInOut(duration: 0.2)) {
                            selectedDate = date
                        }
                        onDateChanged?(date)
                    }
                }
            }
            .padding(.horizontal, ScaleFactor.padding(16))
        }
    }

    // MARK: - 生成日期列表

    private func generateDates() -> [Date] {
        var dates = [Date]()
        let currentDate = calendar.startOfDay(for: selectedDate)

        for i in -(daysToShow / 2)...(daysToShow / 2) {
            if let date = calendar.date(byAdding: .day, value: i, to: currentDate) {
                dates.append(date)
            }
        }
        return dates
    }

    // MARK: - 判断是否同一天

    private func isSameDay(_ date1: Date, _ date2: Date) -> Bool {
        calendar.isDate(date1, inSameDayAs: date2)
    }
}

// MARK: - 日期芯片

struct DateChip: View {
    let date: Date
    let isSelected: Bool
    let action: () -> Void

    private var calendar = Calendar.current

    init(date: Date, isSelected: Bool, action: @escaping () -> Void) {
        self.date = date
        self.isSelected = isSelected
        self.action = action
    }

    var body: some View {
        Button(action: action) {
            VStack(spacing: 6) {
                Text(monthDay)
                    .font(.system(size: UnifiedFont.caption1, weight: .medium))
                Text(weekday)
                    .font(.system(size: UnifiedFont.caption2))
            }
            .foregroundColor(isSelected ? .white : HealingColors.textSecondary)
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(chipBackground)
            .overlay(
                RoundedRectangle(cornerRadius: 14)
                    .stroke(strokeColor, lineWidth: isSelected ? 0 : 1)
            )
            .shadow(
                color: isSelected ? HealingColors.forestMist.opacity(0.3) : Color.black.opacity(0.05),
                radius: isSelected ? 6 : 3,
                y: 2
            )
        }
        .buttonStyle(.plain)
    }

    private var monthDay: String {
        let components = calendar.dateComponents([.day, .month], from: date)
        return "\(components.month!)/\(components.day!)"
    }

    private var weekday: String {
        let components = calendar.dateComponents([.weekday], from: date)
        let weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
        return weekdays[components.weekday! - 1]
    }

    @ViewBuilder
    private var chipBackground: some View {
        if isSelected {
            LinearGradient(
                colors: [HealingColors.forestMist, HealingColors.deepSage],
                startPoint: .leading,
                endPoint: .trailing
            )
        } else {
            Color(HealingColors.cardBackground)
        }
    }

    private var strokeColor: Color {
        isSelected ? .clear : HealingColors.textTertiary.opacity(0.2)
    }
}

// MARK: - Preview

#Preview {
    HorizontalDatePicker(
        selectedDate: .constant(Date()),
        onDateChanged: { date in
            print("Selected: \(date)")
        }
    )
    .padding()
    .background(HealingColors.background)
}
