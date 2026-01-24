import Foundation

// MARK: - MedLive 疾病数据模型
// 医脉通诊疗知识库 - 专业医学数据

struct MedLiveDiseaseModel: Codable, Identifiable {
    let id: Int  // 数据库ID
    let wikiId: String?  // 医脉通 wiki_id
    let name: String
    let source: String
    let url: String

    // 基础信息
    let department: String?

    // 内容区块
    let sections: [DiseaseSection]

    // 用于从列表模型转换
    init(from listModel: DiseaseListModel, sections: [DiseaseSection] = []) {
        self.id = listModel.id
        self.wikiId = nil
        self.name = listModel.name
        self.source = "医脉通"
        self.url = ""
        self.department = listModel.department_name ?? listModel.recommended_department
        self.sections = sections
    }

    // CodingKeys 用于 JSON 映射（后端返回 wiki_id 而非 wikiId）
    enum CodingKeys: String, CodingKey {
        case id
        case wikiId = "wiki_id"
        case name, source, url, department, sections
    }
}

struct EditorInfo: Codable, Identifiable {
    let id: String
    let name: String
    let role: String  // "编" 或 "审"
    let hospital: String?
}

// MARK: - 疾病内容区块
struct DiseaseSection: Codable, Identifiable {
    let id: String  // 区块唯一标识
    let title: String  // 显示标题
    let icon: String  // SF Symbol 图标名
    let content: String?  // 文本内容
    let items: [ContentItem]?  // 结构化子项
    let isExpanded: Bool?  // 默认是否展开（前端使用）

    // 便捷初始化器 - content 和 items 可选，isExpanded 有默认值
    init(id: String, title: String, icon: String, content: String? = nil, items: [ContentItem]? = nil, isExpanded: Bool? = nil) {
        self.id = id
        self.title = title
        self.icon = icon
        self.content = content
        self.items = items
        self.isExpanded = isExpanded
    }
}

// MARK: - 结构化内容项
struct ContentItem: Codable, Identifiable {
    let id: String
    let title: String?
    let content: String
    let level: Int  // 缩进层级 0-2

    // 便捷初始化器 - title 可选
    init(id: String, title: String? = nil, content: String, level: Int) {
        self.id = id
        self.title = title
        self.content = content
        self.level = level
    }
}

// MARK: - 示例数据（用于预览）
extension MedLiveDiseaseModel {
    static let sampleTricuspidValveDisease = MedLiveDiseaseModel(
        from: DiseaseListModel(
            id: 90,
            name: "三尖瓣疾病",
            department_id: 6,
            department_name: "心血管科",
            recommended_department: nil,
            is_hot: true,
            view_count: 100
        ),
        sections: [
            // 简介
            DiseaseSection(
                id: "overview",
                title: "疾病简介",
                icon: "info.circle",
                content: "三尖瓣疾病指三尖瓣的瓣膜、腱索、乳头肌和瓣环，以及右心房和右心室出现解剖结构和功能异常导致的血流动力学改变。三尖瓣不能完全闭合为三尖瓣关闭不全（TR），三尖瓣开放受限则为三尖瓣狭窄（TS）。",
                items: [
                    ContentItem(id: "1", title: "主要症状", content: "体循环淤血，三尖瓣关闭不全晚期发生右心衰竭，TS早期即可出现。表现为颈静脉充盈和搏动、食欲不振、恶心、呕吐、上腹饱胀感、黄疸、脚踝和小腿肿胀等。", level: 0),
                    ContentItem(id: "2", title: "分类", content: "根据病因把三尖瓣关闭不全分为原发性（器质性，三尖瓣结构异常）和继发性（功能性，继发于肺动脉高压和右心病变）。", level: 0),
                    ContentItem(id: "3", title: "病因", content: "风湿热是三尖瓣狭窄最常见的病因，其他原因少见。", level: 0),
                    ContentItem(id: "4", title: "诊断", content: "典型的体征和超声心动图表现可明确诊断。", level: 0),
                    ContentItem(id: "5", title: "治疗原则", content: "改善患者的症状和心肺功能情况，控制并发症，提高生活质量，增加预期寿命。", level: 0)
                ],
                isExpanded: true
            ),

            // 定义
            DiseaseSection(
                id: "definition",
                title: "定义",
                icon: "text.book.closed",
                content: "三尖瓣疾病指三尖瓣的瓣膜、腱索、乳头肌和瓣环，以及右心房和右心室出现解剖结构和功能异常导致的血流动力学改变。",
                items: [
                    ContentItem(id: "tr", title: "三尖瓣关闭不全 (TR)", content: "三尖瓣不能完全闭合，导致收缩期血液从右心室反流至右心房。", level: 1),
                    ContentItem(id: "ts", title: "三尖瓣狭窄 (TS)", content: "三尖瓣开放受限，导致舒张期血液从右心房流入右心室受阻。", level: 1)
                ],
                isExpanded: false
            ),

            // 症状
            DiseaseSection(
                id: "symptoms",
                title: "症状",
                icon: "stethoscope",
                content: "TR可长期无症状，TS早期即可出现症状。",
                items: [
                    ContentItem(id: "sys_symptoms", title: "体循环淤血症状", content: "TR晚期发生右心衰竭，TS早期即可出现。表现为：颈静脉充盈和搏动、食欲不振、恶心、呕吐、上腹饱胀感、黄疸、脚踝和小腿肿胀等。", level: 0)
                ],
                isExpanded: false
            )
        ]
    )
}
