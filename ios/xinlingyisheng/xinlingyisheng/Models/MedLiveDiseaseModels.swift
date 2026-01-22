import Foundation

// MARK: - MedLive 疾病数据模型
// 医脉通诊疗知识库 - 专业医学数据

struct MedLiveDiseaseModel: Codable, Identifiable {
    let id: String  // wiki_id
    let name: String
    let source: String
    let url: String

    // 基础信息
    let englishName: String?
    let aliases: String?
    let department: String?

    // 内容区块
    let sections: [DiseaseSection]
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
        id: "90",
        name: "三尖瓣疾病",
        source: "医脉通",
        url: "https://yzy.medlive.cn/pc/wikiDetail?wiki_id=90",
        englishName: "Tricuspid Valve Disease",
        aliases: "TR, TS",
        department: "心血管科",
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

            // 分类
            DiseaseSection(
                id: "classification",
                title: "疾病分类",
                icon: "square.grid.2x2",
                items: [
                    ContentItem(id: "primary", title: "原发性（器质性）TR", content: "三尖瓣结构异常，占TR的10%～30%", level: 0),
                    ContentItem(id: "secondary", title: "继发性（功能性）TR", content: "继发于肺动脉高压和右心病变，占TR的70%～90%。常见于左心疾病（冠心病、瓣膜性心脏病、心肌病等）晚期引发的肺动脉高压和右心室功能障碍。", level: 0)
                ],
                isExpanded: false
            ),

            // 流行病学
            DiseaseSection(
                id: "epidemiology",
                title: "流行病学",
                icon: "chart.bar",
                items: [
                    ContentItem(id: "incidence", title: "TR发病率", content: "TR非常常见，发生率为65%～85%。在结构正常的三尖瓣中，轻度TR可以认为是正常的。", level: 0),
                    ContentItem(id: "survival", title: "生存率", content: "无TR患者1年生存率为91.7%，轻度TR为90.3%，中度TR为78.9%，重度TR为63.9%。中度和重度TR的1年生存率明显下降。", level: 0),
                    ContentItem(id: "severe", title: "重度TR发生率", content: "在国内老年人中，重度TR发生率为1.1%。", level: 0),
                    ContentItem(id: "mortality", title: "死亡率", content: "重度TR患者中位随访时间2.9年里有42.1%的患者死亡。从症状出现后的平均生存时间为2.28±1.40年，心力衰竭（50%）是最主要的死亡原因。", level: 0)
                ],
                isExpanded: false
            ),

            // 病因
            DiseaseSection(
                id: "causes",
                title: "病因",
                icon: "cross.case",
                content: "三尖瓣疾病的病因多样，具体如下：",
                items: [
                    ContentItem(id: "tr_primary", title: "原发性TR病因", content: "三尖瓣脱垂、Ebstein畸形、类癌综合征、心内膜炎、起搏器/除颤器电极相关、外伤、风湿热、药物诱导（如芬氟拉明、麦角胺）", level: 1),
                    ContentItem(id: "tr_secondary", title: "继发性TR病因", content: "左心疾病导致的肺动脉高压、右心室梗死、右心室扩张、肺动脉栓塞、房颤", level: 1),
                    ContentItem(id: "ts_cause", title: "TS病因", content: "风湿热是TS最常见的病因，其他原因少见（如类癌综合征、系统性红斑狼疮、心内膜炎、先天性三尖瓣狭窄）", level: 1)
                ],
                isExpanded: false
            ),

            // 发生机制
            DiseaseSection(
                id: "mechanism",
                title: "发生机制",
                icon: "gearshape.2",
                content: "",
                items: [
                    ContentItem(id: "tr_mech", title: "TR机制", content: "可引起右心房和右心室增大，右心室容量超负荷使右心室重构，长期的右心室容量超负荷可导致右心室舒张功能障碍，伴随着右心室舒张末期压力升高，晚期导致右心衰竭，表现为体循环静脉压力升高和体循环淤血。", level: 0),
                    ContentItem(id: "ts_mech", title: "TS机制", content: "引起右心房增大，右心房压力上升，但右心室大小和功能正常，右心室、肺动脉和左心房压力均正常。当舒张期右心房和右心室平均压力差超过4mmHg时，即可出现体循环淤血症状。", level: 0)
                ],
                isExpanded: false
            ),

            // 症状与体征
            DiseaseSection(
                id: "symptoms",
                title: "症状与体征",
                icon: "stethoscope",
                content: "TR可长期无症状，TS早期即可出现症状。",
                items: [
                    ContentItem(id: "sys_symptoms", title: "体循环淤血症状", content: "TR晚期发生右心衰竭，TS早期即可出现。表现为：颈静脉充盈和搏动、食欲不振、恶心、呕吐、上腹饱胀感、黄疸、脚踝和小腿肿胀等。", level: 0),
                    ContentItem(id: "risk_factors", title: "危险因素", content: "老年、房颤、左心疾病（冠心病、心肌病、二尖瓣和主动脉瓣病变等）", level: 0),
                    ContentItem(id: "auscultation_tr", title: "TR听诊", content: "三尖瓣区全收缩期杂音，吸气和压迫肝脏后杂音可增强。三尖瓣脱垂可闻及三尖瓣区非喷射样喀喇音。", level: 0),
                    ContentItem(id: "auscultation_ts", title: "TS听诊", content: "三尖瓣区舒张中晚期低调隆隆样杂音，吸气末增强，呼气或Valsalva动作时减弱，可伴震颤。", level: 0)
                ],
                isExpanded: false
            ),

            // 辅助检查
            DiseaseSection(
                id: "examination",
                title: "辅助检查",
                icon: "waveform.path",
                content: "超声心动图是诊断和评估TS和TR反流程度的首选检查手段。",
                items: [
                    ContentItem(id: "echo_m", title: "M型超声", content: "TR：室间隔运动幅度低平或与左心室后壁呈同向运动，瓣叶活动曲线开放和关闭速度增快。\nTS：EF斜率减低，前后叶同向运动，后叶运动下降明显，瓣叶增厚，曲线增粗。", level: 1),
                    ContentItem(id: "echo_2d", title: "二维超声", content: "TR：三尖瓣原发性损害时，瓣缘增厚，呈「鼓槌状」；功能性改变时瓣环扩大，瓣叶活动幅度增强；可见收缩期瓣叶关闭对合不拢和裂隙。\nTS：风湿性可见瓣尖增厚和交界粘连，回声增强；舒张期开放受限，呈圆顶状改变。", level: 1),
                    ContentItem(id: "echo_doppler", title: "多普勒超声", content: "TR：彩色多普勒超声可见收缩期通过三尖瓣口流入右房的血流信号。连续多普勒测定收缩期三尖瓣跨瓣反流峰速简单计算三尖瓣跨瓣峰压差，并通过简化伯努利方程推算右心室收缩压及肺动脉收缩压。\nTS：彩色多普勒超声可见舒张期通过三尖瓣口的射流信号。连续多普勒测定三尖瓣口血流速度加快，可以测量跨瓣压差和评估三尖瓣口面积。", level: 1),
                    ContentItem(id: "cxr", title: "胸部X线", content: "TR可见右心房右心室增大，可见奇静脉扩张、胸腔积液、腹水引起的横膈上移。\nTS可见右心房增大，下腔静脉和静脉扩张，无肺动脉扩张。", level: 1),
                    ContentItem(id: "ecg", title: "心电图", content: "TR可见右心室肥大伴劳损、右心房扩大，常伴右束支传导阻滞表现。\nTS可见右心房扩大等。", level: 1)
                ],
                isExpanded: false
            ),

            // 诊断标准
            DiseaseSection(
                id: "diagnosis",
                title: "诊断标准",
                icon: "checkmark.seal",
                content: "超声心动图的单个参数并不能准确评估TR的严重程度，要使用多个参数对TR严重程度进行综合评估。",
                items: [
                    ContentItem(id: "mild", title: "轻度TR", content: "反流束面积＜5cm²，反流束缩径颈宽度＜0.3cm，VC宽度＜0.3cm，PISA半径＜0.5cm", level: 0),
                    ContentItem(id: "moderate", title: "中度TR", content: "反流束面积5-10cm²，反流束缩径颈宽度0.3-0.7cm，VC宽度0.3-0.7cm，PISA半径0.5-0.9cm", level: 0),
                    ContentItem(id: "severe", title: "重度TR", content: "反流束面积＞10cm²，反流束缩径颈宽度＞0.7cm，VC宽度＞0.7cm，PISA半径＞0.9cm", level: 0),
                    ContentItem(id: "ts_severe", title: "重度TS判断标准", content: "1.增厚、硬化、钙化的瓣叶\n2.瓣叶的运动受限\n3.三尖瓣平均跨瓣压差≥5mmHg\n4.三尖瓣速度-时间积分＞60cm\n5.压力减半时间≥190ms\n6.三尖瓣口瓣口面积≤1.0cm²\n7.伴右心房扩大或者下腔静脉明显扩张", level: 0)
                ],
                isExpanded: false
            ),

            // 鉴别诊断
            DiseaseSection(
                id: "differential",
                title: "鉴别诊断",
                icon: "eye",
                items: [
                    ContentItem(id: "vsd", title: "室间隔缺损", content: "胸骨左缘3、4肋间全收缩期响亮而粗糙的吹风样杂音，超声心动图和心导管检查可明确诊断。", level: 0),
                    ContentItem(id: "tumor", title: "右心房肿瘤（黏液瘤）", content: "可闻及三尖瓣区舒张期隆隆样杂音和全收缩期杂音，可随体位和呼吸变化。超声心动图和心导管检查可见右心房内边界清楚、形态不规则的团块。", level: 0),
                    ContentItem(id: "dcm", title: "扩张型心肌病", content: "心尖区和三尖瓣区可有收缩期杂音，可有心腔扩大征象。根据病史和核素心肌显像等检查鉴别诊断。", level: 0)
                ],
                isExpanded: false
            ),

            // 误诊防范
            DiseaseSection(
                id: "prevention",
                title: "误诊防范",
                icon: "exclamationmark.shield",
                items: [
                    ContentItem(id: "note1", title: "重视查体", content: "一般情况下，通过病史和查体可初步判断瓣膜性心脏病。", level: 0),
                    ContentItem(id: "note2", title: "及时检查", content: "在重度心力衰竭和其他一些特殊情况下，查体不能准确判断瓣膜性心脏病的情况可及时通过超声心动图予以明确诊断。", level: 0)
                ],
                isExpanded: false
            ),

            // 治疗
            DiseaseSection(
                id: "treatment",
                title: "治疗",
                icon: "pills",
                content: "治疗原则是改善患者的症状和心肺功能情况，控制并发症，提高生活质量，增加预期寿命。",
                items: [
                    ContentItem(id: "medical", title: "药物治疗", content: "主要针对右心衰竭症状进行治疗，包括利尿剂、醛固酮受体拮抗剂等。", level: 0),
                    ContentItem(id: "surgical", title: "手术治疗", content: "TR主要是药物控制右心衰竭。如果药物能控制好右心衰竭，不出现临床症状，不影响生活质量，那么不需要做手术。如果TR相关的右心衰竭不能控制，或者反复复发，那么经过外科手术团队评估后，没有手术禁忌证，而且手术可以改善右心衰竭，提高生活质量，那么可以进行外科手术治疗。", level: 0)
                ],
                isExpanded: false
            ),

            // 预防与康复
            DiseaseSection(
                id: "rehabilitation",
                title: "预防与康复",
                icon: "heart.circle",
                items: [
                    ContentItem(id: "prevention", title: "一级与二级预防", content: "主要针对病因（感染性心内膜炎、左心疾病等）进行预防。", level: 0),
                    ContentItem(id: "rehab", title: "康复", content: "针对并发症进行康复。", level: 0),
                    ContentItem(id: "education", title: "患者教育", content: "应当戒烟、戒酒，积极控制并发症，避免劳累。需要抗凝治疗的应当监测凝血指标，定期复查。", level: 0)
                ],
                isExpanded: false
            ),

            // 复诊与随访
            DiseaseSection(
                id: "followup",
                title: "复诊与随访",
                icon: "calendar",
                items: [
                    ContentItem(id: "mild_followup", title: "轻度TR和TS", content: "每2年临床随访，复查超声心动图和心电图。", level: 0),
                    ContentItem(id: "severe_followup", title: "中重度TR和TS", content: "每年临床随访，复查超声心动图。", level: 0),
                    ContentItem(id: "symptom_followup", title: "症状变化", content: "出现临床症状或症状发生改变及时临床随访。", level: 0)
                ],
                isExpanded: false
            ),

            // 参考文献
            DiseaseSection(
                id: "references",
                title: "参考文献",
                icon: "books.vertical",
                content: "本文内容参考以下权威文献：",
                items: [
                    ContentItem(id: "ref1", title: "", content: "[1] Arsalan M, Walther T, Smith RL, et al. Tricuspid regurgitation diagnosis and treatment[J]. Eur Heart J, 2017, 38(9): 634-638.", level: 0),
                    ContentItem(id: "ref2", title: "", content: "[2] Nath J, Foster E, Heidenreich PA. Impact of tricuspid regurgitation on long-term survival[J]. J Am Coll Cardiol, 2004, 43(3): 405-409.", level: 0),
                    ContentItem(id: "ref3", title: "", content: "[3] 2021 ESC/EACTS Guidelines for the management of valvular heart disease[J/OL]. Eur Heart J, 2021.", level: 0),
                    ContentItem(id: "ref4", title: "", content: "[4] 中国成人心脏瓣膜病超声心动图规范化检查专家共识[J]. 中国循环杂志, 2021, 36(2): 109-125.", level: 0)
                ],
                isExpanded: false
            )
        ]
    )
}

// MARK: - 从 MedLive JSON 数据解析
extension MedLiveDiseaseModel {
    static func from(json: [String: Any]) -> MedLiveDiseaseModel? {
        guard let wikiId = json["wiki_id"] as? String,
              let name = json["name"] as? String else {
            return nil
        }

        return MedLiveDiseaseModel(
            id: wikiId,
            name: name,
            source: json["source"] as? String ?? "医脉通",
            url: json["url"] as? String ?? "",
            englishName: json["en_name"] as? String,
            aliases: json["aliases"] as? String,
            department: json["department"] as? String,
            sections: []  // 需要根据实际解析逻辑填充
        )
    }
}
