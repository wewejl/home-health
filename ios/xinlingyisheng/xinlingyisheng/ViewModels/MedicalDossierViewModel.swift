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
    @Published var noteError: String?

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
    
    func markAsExported(_ event: MedicalEvent) {
        if let index = events.firstIndex(where: { $0.id == event.id }) {
            withAnimation {
                events[index].status = .exported
                events[index].exportedAt = Date()
                applyFilters(searchText: searchText, filter: selectedFilter)
            }
        }
    }
    
    // MARK: - AI Summary Methods
    
    /// 生成 AI 摘要
    func generateAISummary(for eventId: String, forceRegenerate: Bool = false) async {
        isGeneratingSummary = true
        summaryError = nil
        
        do {
            let response = try await AIService.shared.generateSummary(eventId: eventId, forceRegenerate: forceRegenerate)
            currentSummary = response
            isGeneratingSummary = false
        } catch {
            summaryError = error.localizedDescription
            isGeneratingSummary = false
        }
    }
    
    /// 获取已缓存的 AI 摘要
    func fetchAISummary(for eventId: String) async {
        isGeneratingSummary = true
        summaryError = nil
        
        do {
            let response = try await AIService.shared.getSummary(eventId: eventId)
            currentSummary = response
            isGeneratingSummary = false
        } catch {
            // 如果没有缓存，尝试生成新的
            await generateAISummary(for: eventId)
        }
    }
    
    // MARK: - Related Events Methods
    
    /// 查找相关病历事件
    func findRelatedEvents(for eventId: String, maxResults: Int = 5) async {
        isLoadingRelated = true
        
        do {
            let response = try await AIService.shared.findRelatedEvents(eventId: eventId, maxResults: maxResults)
            relatedEvents = response.related_events
            isLoadingRelated = false
        } catch {
            print("[ViewModel] Failed to find related events: \(error)")
            relatedEvents = []
            isLoadingRelated = false
        }
    }
    
    /// 分析两个事件的关联性
    func analyzeRelation(eventIdA: String, eventIdB: String) async -> AnalyzeRelationResponse? {
        do {
            return try await AIService.shared.analyzeRelation(eventIdA: eventIdA, eventIdB: eventIdB)
        } catch {
            print("[ViewModel] Failed to analyze relation: \(error)")
            return nil
        }
    }
    
    // MARK: - Event Merge Methods
    
    /// 合并多个事件
    func mergeEvents(eventIds: [String], newTitle: String? = nil) async {
        isMerging = true
        mergeResult = nil
        
        do {
            let response = try await AIService.shared.mergeEvents(eventIds: eventIds, newTitle: newTitle)
            mergeResult = response
            
            // 从列表中移除已合并的事件
            withAnimation {
                events.removeAll { eventIds.contains($0.id) }
                applyFilters(searchText: searchText, filter: selectedFilter)
            }
            
            isMerging = false
        } catch {
            errorMessage = "合并失败: \(error.localizedDescription)"
            isMerging = false
        }
    }
    
    // MARK: - Smart Aggregate Methods
    
    /// 智能聚合 - 判断新会话应归入哪个事件
    func smartAggregate(
        sessionId: String,
        sessionType: String,
        department: String? = nil,
        chiefComplaint: String? = nil
    ) async -> SmartAggregateResponse? {
        do {
            return try await AIService.shared.smartAggregate(
                sessionId: sessionId,
                sessionType: sessionType,
                department: department,
                chiefComplaint: chiefComplaint
            )
        } catch {
            print("[ViewModel] Smart aggregate failed: \(error)")
            return nil
        }
    }
    
    // MARK: - Load Event Detail
    func loadEventDetail(eventId: String) async {
        do {
            let detail = try await MedicalEventAPIService.shared.fetchEventDetail(eventId: eventId)
            let event = detail.toMedicalEvent()
            
            // Update the event in the list
            if let index = events.firstIndex(where: { $0.id == eventId }) {
                events[index] = event
            }
            selectedEvent = event
        } catch {
            print("[MedicalDossier] Failed to load event detail: \(error)")
        }
    }
    
    // MARK: - Timeline Generation
    func generateTimelineItems(for event: MedicalEvent) -> [TimelineItem] {
        var items: [TimelineItem] = []
        var dateGroups: [String: [TimelineContent]] = [:]
        
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        
        for session in event.sessions {
            for message in session.messages {
                let dateKey = dateFormatter.string(from: message.timestamp)
                let contentType: TimelineContentType = message.role == .user ? .userMessage : .aiMessage
                let content = TimelineContent(type: contentType, message: message)
                
                if dateGroups[dateKey] == nil {
                    dateGroups[dateKey] = []
                }
                dateGroups[dateKey]?.append(content)
            }
        }
        
        for attachment in event.attachments {
            let dateKey = dateFormatter.string(from: attachment.createdAt)
            let content = TimelineContent(type: .attachment, attachment: attachment)
            
            if dateGroups[dateKey] == nil {
                dateGroups[dateKey] = []
            }
            dateGroups[dateKey]?.append(content)
        }
        
        let sortedDates = dateGroups.keys.sorted(by: >)
        for dateKey in sortedDates {
            if let contents = dateGroups[dateKey],
               let date = dateFormatter.date(from: dateKey) {
                let sortedContents = contents.sorted { c1, c2 in
                    let t1 = c1.message?.timestamp ?? c1.attachment?.createdAt ?? Date()
                    let t2 = c2.message?.timestamp ?? c2.attachment?.createdAt ?? Date()
                    return t1 > t2
                }
                items.append(TimelineItem(date: date, contents: sortedContents))
            }
        }
        
        return items
    }

    // MARK: - Note Management

    /// 添加或更新事件备注
    func saveNote(for eventId: String, content: String, isImportant: Bool = false) async -> Bool {
        isSavingNote = true
        noteError = nil

        do {
            // 首先获取事件详情，查看是否已有备注
            let detail = try await MedicalEventAPIService.shared.fetchEventDetail(eventId: eventId)

            if let existingNote = detail.notes.first {
                // 更新现有备注
                _ = try await MedicalEventAPIService.shared.updateNote(
                    eventId: eventId,
                    noteId: String(existingNote.id),
                    content: content,
                    isImportant: isImportant
                )
            } else {
                // 创建新备注
                _ = try await MedicalEventAPIService.shared.addNote(
                    eventId: eventId,
                    content: content,
                    isImportant: isImportant
                )
            }

            // 刷新事件数据
            await loadEventDetail(eventId: eventId)

            isSavingNote = false
            return true
        } catch {
            noteError = "保存备注失败: \(error.localizedDescription)"
            isSavingNote = false
            return false
        }
    }

    /// 删除事件备注
    func deleteNote(for eventId: String, noteId: String) async -> Bool {
        do {
            try await MedicalEventAPIService.shared.deleteNote(eventId: eventId, noteId: noteId)
            await loadEventDetail(eventId: eventId)
            return true
        } catch {
            noteError = "删除备注失败: \(error.localizedDescription)"
            return false
        }
    }
}
