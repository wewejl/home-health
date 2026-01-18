import SwiftUI

// MARK: - 录音指示器
struct RecordingIndicator: View {
    @State private var isAnimating = false
    
    var body: some View {
        Circle()
            .fill(Color.red)
            .frame(width: 10, height: 10)
            .scaleEffect(isAnimating ? 1.0 : 0.8)
            .animation(
                .easeInOut(duration: 0.75)
                .repeatForever(autoreverses: true),
                value: isAnimating
            )
            .onAppear {
                isAnimating = true
            }
    }
}

// MARK: - 播报指示器
struct SpeakingIndicator: View {
    var body: some View {
        Image(systemName: "speaker.wave.2.fill")
            .font(.system(size: 14))
            .foregroundColor(.blue)
    }
}

// MARK: - Preview
#Preview {
    VStack(spacing: 20) {
        HStack {
            Text("录音中")
            RecordingIndicator()
        }
        
        HStack {
            Text("播报中")
            SpeakingIndicator()
        }
    }
    .padding()
}
