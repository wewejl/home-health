import XCTest
@testable import xinlingyisheng

/// 虚拟医生功能 UI 测试
final class VirtualDoctorSelectionViewTests: XCTestCase {

    override func setUpWithError() throws {
        try super.setUpWithError()
    }

    override func tearDownWithError() throws {
        try super.tearDownWithError()
    }

    func testVirtualDoctorSelectionViewExists() {
        // 测试：VirtualDoctorSelectionView 可以被实例化
        let view = VirtualDoctorSelectionView()

        // 验证视图标题
        XCTAssertEqual(view.title, "选择医生")

        // 验证视图有 body
        let body = view.body
        XCTAssertNotNil(body)
    }

    func testPersonalityTypeEnum() {
        // 测试：所有性格类型都有正确的显示名称和描述
        for personality in PersonalityType.allCases {
            let name = personality.displayName
            XCTAssertFalse(name.isEmpty, "性格类型 \(personality.rawValue) 应该有显示名称")

            if personality == .formal {
                XCTAssertEqual(name, "专业严谨型")
                XCTAssertEqual(personality.description, "用词严谨专业，遵循医学标准")
            } else if personality == .friendly {
                XCTAssertEqual(name, "温和亲切型")
                XCTAssertEqual(personality.description, "像长辈一样温和，多用鼓励性语言")
            } else if personality == .concise {
                XCTAssertEqual(name, "干练直接型")
                XCTAssertEqual(personality.description, "直击问题要点，少用客套话")
            } else if personality == .detailed {
                XCTAssertEqual(name, "详细耐心型")
                XCTAssertEqual(personality.description, "解释详细，说明原因，提供背景知识")
            }
        }
    }

    func testVirtualDoctorModelEncoding() {
        // 测试：VirtualDoctor 模型可以正确编码
        let doctor = VirtualDoctor(
            id: 1,
            name: "测试医生",
            title: "AI 专家团队",
            departmentId: 2,
            specialty: "小儿感冒、发热、腹泻等",
            intro: "由多位资深儿科专家训练",
            personalityType: "formal",
            greetingTemplate: "您好，我是{name}。"
        )

        // 测试 JSON 编码
        let encoder = JSONEncoder()
        let data = try! encoder.encode(doctor)
        let string = String(data: data, encoding: .utf8)

        XCTAssertFalse(string.isEmpty, "编码后的字符串不应为空")
        XCTAssertTrue(string.contains("测试医生"), "应该包含医生姓名")
    }

    func testSpecialtyConfigModel() {
        // 测试：SpecialtyConfig 模型
        let specialty = SpecialtyConfig(
            code: "dermatology",
            name: "皮肤科",
            agentClass: "DermatologyReActAgent"
        )

        XCTAssertEqual(specialty.code, "dermatology")
        XCTAssertEqual(specialty.name, "皮肤科")
        XCTAssertEqual(specialty.agentClass, "DermatologyReActAgent")
    }

    func testPersonalityConfigModel() {
        // 测试：PersonalityConfig 模型
        let config = PersonalityConfig(
            code: "friendly",
            name: "温和亲切型",
            description: "像长辈一样温和，多用鼓励性语言",
            styleTags: ["耐心", "细致"],
            temperature: 0.8,
            greetingTemplate: "你好，我是{name}。"
        )

        XCTAssertEqual(config.code, "friendly")
        XCTAssertEqual(config.name, "温和亲切型")
        XCTAssertEqual(config.temperature, 0.8)
        XCTAssertEqual(config.styleTags.count, 2)
    }
}

    override func setUpWithError() throws {
        try super.setUpWithError()
        // 可以在这里进行登录等初始化
    }

    override func tearDownWithError() throws {
        try super.tearDownWithError()
    // 清理操作
    }

    func testVirtualDoctorSelectionViewExists() {
        // 测试：VirtualDoctorSelectionView 可以被实例化
        let view = VirtualDoctorSelectionView()

        // 验证视图标题
        XCTAssertEqual(view.title, "选择医生")

        // 验证视图有 body
        let body = view.body
        XCTAssertNotNil(body)
    }

    func testPersonalityTypeEnum() {
        // 测试：所有性格类型都有正确的显示名称和描述
        for personality in PersonalityType.allCases {
            let name = personality.displayName
            XCTAssertFalse(name.isEmpty, "性格类型 \(personality.rawValue) 应该有显示名称")

            if personality == .formal {
                XCTAssertEqual(name, "专业严谨型")
                XCTAssertEqual(personality.description, "用词严谨专业，遵循医学标准")
            } else if personality == .friendly {
                XCTAssertEqual(name, "温和亲切型")
                XCTAssertEqual(personality.description, "像长辈一样温和，多用鼓励性语言")
            } else if personality == .concise {
                XCTAssertEqual(name, "干练直接型")
                XCTAssertEqual(personality.description, "直击问题要点，少用客套话")
            } else if personality == .detailed {
                XCTAssertEqual(name, "详细耐心型")
                XCTAssertEqual(personality.description, "解释详细，说明原因，提供背景知识")
            }
        }
    }

    func testVirtualDoctorModelEncoding() {
        // 测试：VirtualDoctor 模型可以正确编码
        let doctor = VirtualDoctor(
            id: 1,
            name: "测试医生",
            title: "AI 专家团队",
            departmentId: 2,
            specialty: "小儿感冒、发热、腹泻等",
            intro: "由多位资深儿科专家训练",
            personalityType: "formal",
            greetingTemplate: "您好，我是{name}。"
        )

        // 测试 JSON 编码
        let encoder = JSONEncoder()
        let data = try! encoder.encode(doctor)
        let string = String(data: data, encoding: .utf8)

        XCTAssertFalse(string.isEmpty, "编码后的字符串不应为空")
        XCTAssertTrue(string.contains("测试医生"), "应该包含医生姓名")
    }

    func testSpecialtyConfigModel() {
        // 测试：SpecialtyConfig 模型
        let specialty = SpecialtyConfig(
            code: "dermatology",
            name: "皮肤科",
            agentClass: "DermatologyReActAgent"
        )

        XCTAssertEqual(specialty.code, "dermatology")
        XCTAssertEqual(specialty.name, "皮肤科")
        XCTAssertEqual(specialty.agentClass, "DermatologyReActAgent")
    }

    func testPersonalityConfigModel() {
        // 测试：PersonalityConfig 模型
        let config = PersonalityConfig(
            code: "friendly",
            name: "温和亲切型",
            description: "像长辈一样温和",
            styleTags: ["耐心", "细致"],
            temperature: 0.8,
            greetingTemplate: "你好，我是{name}。"
        )

        XCTAssertEqual(config.code, "friendly")
        XCTAssertEqual(config.name, "温和亲切型")
        XCTAssertEqual(config.temperature, 0.8)
        XCTAssertEqual(config.styleTags.count, 2)
    }
}
