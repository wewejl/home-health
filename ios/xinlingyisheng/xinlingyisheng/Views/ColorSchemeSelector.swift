import SwiftUI

struct ColorSchemeSelector: View {
    @Binding var selectedScheme: ColorScheme
    @State private var showPicker = false
    
    var body: some View {
        VStack(spacing: 16) {
            Button(action: {
                withAnimation(.spring(response: 0.4, dampingFraction: 0.7)) {
                    showPicker.toggle()
                }
            }) {
                HStack {
                    Text("配色方案")
                        .font(.system(size: 14, weight: .medium, design: .rounded))
                    Spacer()
                    Text(selectedScheme.rawValue)
                        .font(.system(size: 14, weight: .regular, design: .rounded))
                        .foregroundColor(.secondary)
                    Image(systemName: "chevron.down")
                        .font(.system(size: 12, weight: .medium))
                        .rotationEffect(.degrees(showPicker ? 180 : 0))
                }
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(12)
            }
            .buttonStyle(.plain)
            
            if showPicker {
                VStack(spacing: 12) {
                    ForEach(ColorScheme.allCases, id: \.self) { scheme in
                        ColorSchemeOption(
                            scheme: scheme,
                            isSelected: selectedScheme == scheme,
                            action: {
                                withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                                    selectedScheme = scheme
                                    PremiumColorTheme.current = scheme
                                    showPicker = false
                                }
                            }
                        )
                    }
                }
                .transition(.opacity.combined(with: .scale(scale: 0.95)))
            }
        }
    }
}

struct ColorSchemeOption: View {
    let scheme: ColorScheme
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                HStack(spacing: 4) {
                    Circle()
                        .fill(scheme.primaryColor)
                        .frame(width: 20, height: 20)
                    Circle()
                        .fill(scheme.secondaryColor)
                        .frame(width: 20, height: 20)
                    Circle()
                        .fill(scheme.accentColor)
                        .frame(width: 20, height: 20)
                }
                
                Text(scheme.rawValue)
                    .font(.system(size: 15, weight: .medium, design: .rounded))
                
                Spacer()
                
                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(scheme.primaryColor)
                }
            }
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(isSelected ? scheme.primaryColor.opacity(0.1) : Color.gray.opacity(0.05))
            )
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    ColorSchemeSelector(selectedScheme: .constant(.deepOcean))
        .padding()
}
