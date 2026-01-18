import SwiftUI

struct MedicalDossierView: View {
    @StateObject private var viewModel = MedicalDossierViewModel()
    @State private var selectedEvent: MedicalEvent?
    
    var body: some View {
        ZStack {
            DXYColors.background
                .ignoresSafeArea()
            
            VStack(spacing: 0) {
                headerSection
                
                searchSection
                
                filterSection
                
                contentSection
            }
        }
        .navigationTitle("病历资料夹")
        .navigationBarTitleDisplayMode(.inline)
        .refreshable {
            await viewModel.refresh()
        }
        .navigationDestinationCompat(item: $selectedEvent) { event in
            EventDetailView(event: event, viewModel: viewModel)
        }
    }
    
    private var headerSection: some View {
        HStack {
            VStack(alignment: .leading, spacing: ScaleFactor.spacing(4)) {
                Text("我的病历")
                    .font(.system(size: AdaptiveFont.largeTitle, weight: .bold))
                    .foregroundColor(DXYColors.textPrimary)
                
                Text("AI 智能整理，一键导出")
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.textTertiary)
            }
            
            Spacer()
        }
        .padding(.horizontal, LayoutConstants.horizontalPadding)
        .padding(.top, ScaleFactor.padding(8))
        .padding(.bottom, ScaleFactor.padding(16))
    }
    
    private var searchSection: some View {
        HStack(spacing: ScaleFactor.spacing(8)) {
            HStack(spacing: ScaleFactor.spacing(8)) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: AdaptiveFont.body))
                    .foregroundColor(DXYColors.textTertiary)
                
                TextField("搜索病历", text: $viewModel.searchText)
                    .font(.system(size: AdaptiveFont.subheadline))
                    .foregroundColor(DXYColors.textPrimary)
                
                if !viewModel.searchText.isEmpty {
                    Button(action: { viewModel.searchText = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: AdaptiveFont.body))
                            .foregroundColor(DXYColors.textTertiary)
                    }
                }
            }
            .padding(.horizontal, ScaleFactor.padding(12))
            .padding(.vertical, ScaleFactor.padding(10))
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadiusSmall, style: .continuous))
        }
        .padding(.horizontal, LayoutConstants.horizontalPadding)
        .padding(.bottom, ScaleFactor.padding(12))
    }
    
    private var filterSection: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: ScaleFactor.spacing(12)) {
                ForEach(EventFilter.allCases, id: \.self) { filter in
                    FilterChip(
                        title: filter.displayName,
                        count: viewModel.eventCounts[filter] ?? 0,
                        isSelected: viewModel.selectedFilter == filter
                    ) {
                        withAnimation(.easeInOut(duration: 0.2)) {
                            viewModel.selectedFilter = filter
                        }
                    }
                }
            }
            .padding(.horizontal, LayoutConstants.horizontalPadding)
        }
        .padding(.bottom, ScaleFactor.padding(16))
    }
    
    @ViewBuilder
    private var contentSection: some View {
        if viewModel.isLoading {
            loadingView
        } else if viewModel.events.isEmpty {
            DossierEmptyStateView(onStartConsultation: nil)
        } else if viewModel.filteredEvents.isEmpty {
            SearchEmptyStateView(searchText: viewModel.searchText)
        } else {
            eventListView
        }
    }
    
    private var loadingView: some View {
        VStack(spacing: ScaleFactor.spacing(16)) {
            ProgressView()
                .scaleEffect(1.2)
            Text("加载中...")
                .font(.system(size: AdaptiveFont.subheadline))
                .foregroundColor(DXYColors.textTertiary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
    
    private var eventListView: some View {
        ScrollView(.vertical, showsIndicators: false) {
            LazyVStack(spacing: ScaleFactor.spacing(12)) {
                ForEach(viewModel.filteredEvents) { event in
                    SwipeableEventCard(
                        event: event,
                        onTap: {
                            selectedEvent = event
                        },
                        onArchive: {
                            viewModel.archiveEvent(event)
                        },
                        onDelete: {
                            viewModel.deleteEvent(event)
                        }
                    )
                    .transition(.asymmetric(
                        insertion: .opacity.combined(with: .move(edge: .top)),
                        removal: .opacity.combined(with: .move(edge: .trailing))
                    ))
                }
            }
            .padding(.horizontal, LayoutConstants.horizontalPadding)
            .padding(.bottom, ScaleFactor.padding(20))
        }
    }
}

struct FilterChip: View {
    let title: String
    let count: Int
    let isSelected: Bool
    var action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: ScaleFactor.spacing(4)) {
                Text(title)
                    .font(.system(size: AdaptiveFont.subheadline, weight: isSelected ? .semibold : .regular))
                
                if count > 0 {
                    Text("(\(count))")
                        .font(.system(size: AdaptiveFont.footnote))
                }
            }
            .foregroundColor(isSelected ? .white : DXYColors.textSecondary)
            .padding(.horizontal, ScaleFactor.padding(16))
            .padding(.vertical, ScaleFactor.padding(8))
            .background(isSelected ? DXYColors.primaryPurple : Color.white)
            .clipShape(Capsule())
            .shadow(color: isSelected ? DXYColors.primaryPurple.opacity(0.3) : Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

#Preview {
    CompatibleNavigationStack {
        MedicalDossierView()
    }
}
