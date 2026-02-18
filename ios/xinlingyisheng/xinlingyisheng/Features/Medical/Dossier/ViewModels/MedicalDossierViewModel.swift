import Foundation
import SwiftUI
import Combine

@MainActor
class MedicalDossierViewModel: ObservableObject {
    // MARK: - Published Properties
    @Published var events: [MedicalEvent] = []
    @Published var filteredEvents: [MedicalEvent] = []
    @Published var selectedFilter: EventFilter = .all
    @Published var searchText: String = ""
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    @Published var selectedEvent: MedicalEvent?

    // MARK: - AI Summary State
    @Published var isGeneratingSummary: Bool = false
    @Published var summaryError: String?
    @Published var currentSummary: AISummaryResponse?

    // MARK: - Related Events State
    @Published var relatedEvents: [FindRelatedResponse.RelatedEvent] = []
    @Published var isLoadingRelated: Bool = false

    // MARK: - Merge State
    @Published var isMerging: Bool = false
    @Published var mergeResult: MergeEventsResponse?

    // MARK: - Note State
    @Published var isSavingNote: Bool = false

    // MARK: - Private Properties
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Computed Properties
    var eventCounts: [EventFilter: Int] {
        var counts: [EventFilter: Int] = [:]
        counts[.all] = events.count
        counts[.inProgress] = events.filter { $0.status == .inProgress }.count
        counts[.exported] = events.filter { $0.status == .exported }.count
        return counts
    }

    var isEmpty: Bool {
        filteredEvents.isEmpty && !isLoading
    }

    // MARK: - Initialization
    init() {
        setupBindings()
        Task {
            await loadEvents()
        }
    }

    // MARK: - Setup
    private func setupBindings() {
        Publishers.CombineLatest($searchText, $selectedFilter)
            .debounce(for: .milliseconds(300), scheduler: DispatchQueue.main)
            .sink { [weak self] searchText, filter in
                self?.applyFilters(searchText: searchText, filter: filter)
            }
            .store(in: &cancellables)
    }

    // MARK: - Filter Logic
    private func applyFilters(searchText: String, filter: EventFilter) {
        var result = events

        switch filter {
        case .all:
            break
        case .inProgress:
            result = result.filter { $0.status == .inProgress }
        case .exported:
            result = result.filter { $0.status == .exported }
        }

        if !searchText.isEmpty {
            result = result.filter { event in
                event.title.localizedCaseInsensitiveContains(searchText) ||
                event.summary.localizedCaseInsensitiveContains(searchText) ||
                event.department.displayName.localizedCaseInsensitiveContains(searchText)
            }
        }

        result.sort { $0.updatedAt > $1.updatedAt }

        withAnimation(.easeInOut(duration: 0.2)) {
            filteredEvents = result
        }
    }

    // MARK: - Public Methods
    func refresh() async {
        await loadEvents()
    }

    // MARK: - Load Events from API
    private func loadEvents() async {
        isLoading = true
        errorMessage = nil

        do {
            let response = try await MedicalEventAPIService.shared.fetchEvents()
            events = response.events.map { $0.toMedicalEvent() }
            applyFilters(searchText: searchText, filter: selectedFilter)
            isLoading = false
        } catch {
            isLoading = false
            errorMessage = "加载失败: \(error.localizedDescription)"
            print("[MedicalDossier] Failed to load events: \(error)")
        }
    }

    func deleteEvent(_ event: MedicalEvent) {
        withAnimation {
            events.removeAll { $0.id == event.id }
            applyFilters(searchText: searchText, filter: selectedFilter)
        }
    }

    func archiveEvent(_ event: MedicalEvent) {
        if let index = events.firstIndex(where: { $0.id == event.id }) {
            withAnimation {
                events[index].status = .archived
                applyFilters(searchText: searchText, filter: selectedFilter)
            }
        }
    }

    // MARK: - Note Management
    func saveNote(for eventId: String, content: String, isImportant: Bool = false) async -> Bool {
        isSavingNote = true
        defer { isSavingNote = false }

        do {
            _ = try await MedicalEventAPIService.shared.addNote(
                eventId: eventId,
                content: content,
                isImportant: isImportant
            )
            await refresh()
            return true
        } catch {
            errorMessage = "保存备注失败: \(error.localizedDescription)"
            return false
        }
    }

    func deleteNote(for eventId: String, noteId: String) async -> Bool {
        do {
            try await MedicalEventAPIService.shared.deleteNote(
                eventId: eventId,
                noteId: noteId
            )
            await refresh()
            return true
        } catch {
            errorMessage = "删除备注失败: \(error.localizedDescription)"
            return false
        }
    }

    // MARK: - Event Detail Methods
    func loadEventDetail(eventId: String) async {
        isLoading = true
        defer { isLoading = false }

        do {
            let detail = try await MedicalEventAPIService.shared.fetchEventDetail(eventId: eventId)
            if let index = events.firstIndex(where: { $0.id == eventId }) {
                events[index] = detail.toMedicalEvent()
                applyFilters(searchText: searchText, filter: selectedFilter)
            }
        } catch {
            errorMessage = "加载详情失败: \(error.localizedDescription)"
        }
    }

    func fetchAISummary(for eventId: String) async {
        isGeneratingSummary = true
        summaryError = nil

        do {
            let summary = try await AIService.shared.getSummary(eventId: eventId)
            currentSummary = summary
            isGeneratingSummary = false
        } catch {
            isGeneratingSummary = false
            summaryError = "生成摘要失败: \(error.localizedDescription)"
        }
    }

    func generateAISummary(for eventId: String, forceRegenerate: Bool = false) async {
        isGeneratingSummary = true
        summaryError = nil

        do {
            let summary = try await AIService.shared.generateSummary(
                eventId: eventId,
                forceRegenerate: forceRegenerate
            )
            currentSummary = summary
            isGeneratingSummary = false
        } catch {
            isGeneratingSummary = false
            summaryError = "生成摘要失败: \(error.localizedDescription)"
        }
    }

    // MARK: - Merge Methods
    func mergeEvents(eventIds: [String], newTitle: String? = nil) async {
        isMerging = true

        do {
            let result = try await AIService.shared.mergeEvents(
                eventIds: eventIds,
                newTitle: newTitle
            )
            mergeResult = result
            isMerging = false
            await refresh()
        } catch {
            isMerging = false
            errorMessage = "合并失败: \(error.localizedDescription)"
        }
    }

    // MARK: - Export Methods
    func markAsExported(_ event: MedicalEvent) {
        if let index = events.firstIndex(where: { $0.id == event.id }) {
            events[index].status = .exported
            applyFilters(searchText: searchText, filter: selectedFilter)
        }
    }

    // MARK: - Utility Methods
    func clearError() {
        errorMessage = nil
    }

    func generateTimelineItems(for event: MedicalEvent) -> [TimelineItem] {
        // 生成时间线项目的实现
        return []
    }

    func findRelatedEvents(for eventId: String) async {
        isLoadingRelated = true

        do {
            let response = try await AIService.shared.findRelatedEvents(eventId: eventId)
            relatedEvents = response.related_events
            isLoadingRelated = false
        } catch {
            isLoadingRelated = false
            print("[MedicalDossier] Failed to find related events: \(error)")
        }
    }
}
