import SwiftUI

// MARK: - Navigation Container (iOS 15 compatible)
/// A navigation container that uses NavigationStack on iOS 16+ and NavigationView on iOS 15
struct CompatibleNavigationStack<Content: View>: View {
    let content: Content
    
    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }
    
    var body: some View {
        if #available(iOS 16.0, *) {
            NavigationStack {
                content
            }
        } else {
            NavigationView {
                content
            }
            .navigationViewStyle(.stack)
        }
    }
}

// MARK: - Tab Bar Visibility Modifier (iOS 15 compatible)
struct TabBarHiddenModifier: ViewModifier {
    let hidden: Bool
    
    func body(content: Content) -> some View {
        if #available(iOS 16.0, *) {
            content
                .toolbar(hidden ? .hidden : .visible, for: .tabBar)
        } else {
            content
                .onAppear {
                    if hidden {
                        UITabBar.appearance().isHidden = true
                    }
                }
                .onDisappear {
                    if hidden {
                        UITabBar.appearance().isHidden = false
                    }
                }
        }
    }
}

extension View {
    func tabBarHidden(_ hidden: Bool = true) -> some View {
        modifier(TabBarHiddenModifier(hidden: hidden))
    }
}

// MARK: - Symbol Effect Modifier (iOS 15 compatible)
struct PulseEffectModifier: ViewModifier {
    let isActive: Bool
    @State private var scale: CGFloat = 1.0
    
    func body(content: Content) -> some View {
        if #available(iOS 17.0, *) {
            content
                .symbolEffect(.pulse, isActive: isActive)
        } else {
            content
                .scaleEffect(scale)
                .animation(
                    isActive ? Animation.easeInOut(duration: 0.6).repeatForever(autoreverses: true) : .default,
                    value: scale
                )
                .onChangeCompat(of: isActive) { newValue in
                    scale = newValue ? 1.15 : 1.0
                }
                .onAppear {
                    if isActive {
                        scale = 1.15
                    }
                }
        }
    }
}

extension View {
    func pulseEffect(isActive: Bool) -> some View {
        modifier(PulseEffectModifier(isActive: isActive))
    }
}

// MARK: - onChange Compatibility Extension (iOS 15 compatible)
extension View {
    /// iOS 15 compatible onChange that mirrors the iOS 17 API behavior
    @ViewBuilder
    func onChangeCompat<V: Equatable>(of value: V, perform action: @escaping (V) -> Void) -> some View {
        if #available(iOS 17.0, *) {
            self.onChange(of: value) { _, newValue in
                action(newValue)
            }
        } else {
            self.onChange(of: value) { newValue in
                action(newValue)
            }
        }
    }
}

// MARK: - Toolbar Background Hidden Modifier (iOS 15 compatible)
struct ToolbarBackgroundHiddenModifier: ViewModifier {
    func body(content: Content) -> some View {
        if #available(iOS 16.0, *) {
            content
                .toolbarBackground(.hidden, for: .navigationBar)
                .toolbar(.hidden, for: .navigationBar)
        } else {
            content
                .navigationBarHidden(true)
        }
    }
}

extension View {
    func navigationBarBackgroundHidden() -> some View {
        modifier(ToolbarBackgroundHiddenModifier())
    }
}

// MARK: - Navigation Destination Compatibility (iOS 15 compatible)
struct NavigationDestinationModifier<Destination: View>: ViewModifier {
    @Binding var isPresented: Bool
    let destination: () -> Destination
    
    func body(content: Content) -> some View {
        if #available(iOS 16.0, *) {
            content
                .navigationDestination(isPresented: $isPresented) {
                    destination()
                }
        } else {
            content
                .background(
                    NavigationLink(
                        destination: destination(),
                        isActive: $isPresented,
                        label: { EmptyView() }
                    )
                    .hidden()
                )
        }
    }
}

struct NavigationDestinationItemModifier<Item: Identifiable & Hashable, Destination: View>: ViewModifier {
    @Binding var item: Item?
    let destination: (Item) -> Destination
    
    @ViewBuilder
    func body(content: Content) -> some View {
        if #available(iOS 16.0, *) {
            content
                .navigationDestination(isPresented: Binding(
                    get: { item != nil },
                    set: { if !$0 { item = nil } }
                )) {
                    if let value = item {
                        destination(value)
                    }
                }
        } else {
            content
                .background(
                    NavigationLink(
                        destination: Group {
                            if let value = item {
                                destination(value)
                            }
                        },
                        isActive: Binding(
                            get: { item != nil },
                            set: { if !$0 { item = nil } }
                        ),
                        label: { EmptyView() }
                    )
                    .hidden()
                )
        }
    }
}

extension View {
    func navigationDestinationCompat<Destination: View>(
        isPresented: Binding<Bool>,
        @ViewBuilder destination: @escaping () -> Destination
    ) -> some View {
        modifier(NavigationDestinationModifier(isPresented: isPresented, destination: destination))
    }
    
    func navigationDestinationCompat<Item: Identifiable & Hashable, Destination: View>(
        item: Binding<Item?>,
        @ViewBuilder destination: @escaping (Item) -> Destination
    ) -> some View {
        modifier(NavigationDestinationItemModifier(item: item, destination: destination))
    }
}

// MARK: - Scroll Dismisses Keyboard Modifier (iOS 15 compatible)
struct ScrollDismissesKeyboardModifier: ViewModifier {
    func body(content: Content) -> some View {
        if #available(iOS 16.0, *) {
            content
                .scrollDismissesKeyboard(.interactively)
        } else {
            content
                .simultaneousGesture(
                    DragGesture().onChanged { _ in
                        UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
                    }
                )
        }
    }
}

extension View {
    func scrollDismissesKeyboardCompat() -> some View {
        modifier(ScrollDismissesKeyboardModifier())
    }
}
