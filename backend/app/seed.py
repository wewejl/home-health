from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from .models.department import Department
from .models.doctor import Doctor
from .models.disease import Disease
from .models.drug import Drug, DrugCategory


def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(Department).count() > 0:
            print("数据库已有数据，跳过初始化")
            return

        departments_data = [
            {"name": "皮肤科", "description": "皮肤病、过敏、湿疹、痤疮", "icon": "hand.raised", "sort_order": 1},
            {"name": "儿科", "description": "儿童疾病、生长发育、疫苗咨询", "icon": "figure.child", "sort_order": 2},
            {"name": "妇产科", "description": "妇科疾病、孕期保健、产后康复", "icon": "figure.dress.line.vertical.figure", "sort_order": 3},
            {"name": "消化内科", "description": "胃病、肠炎、肝胆疾病", "icon": "stomach", "sort_order": 4},
            {"name": "呼吸内科", "description": "感冒、咳嗽、哮喘、肺炎", "icon": "lungs", "sort_order": 5},
            {"name": "心血管内科", "description": "高血压、冠心病、心律失常", "icon": "heart", "sort_order": 6},
            {"name": "内分泌科", "description": "糖尿病、甲状腺疾病、肥胖", "icon": "drop", "sort_order": 7},
            {"name": "神经内科", "description": "头痛、失眠、中风、癫痫", "icon": "brain.head.profile", "sort_order": 8},
            {"name": "骨科", "description": "骨折、关节炎、颈椎病、腰椎病", "icon": "figure.walk", "sort_order": 9},
            {"name": "眼科", "description": "近视、白内障、青光眼、眼部炎症", "icon": "eye", "sort_order": 10},
            {"name": "耳鼻咽喉科", "description": "中耳炎、鼻炎、咽喉炎", "icon": "ear", "sort_order": 11},
            {"name": "口腔科", "description": "牙痛、龋齿、牙周病、口腔溃疡", "icon": "mouth", "sort_order": 12},
        ]

        departments = []
        for data in departments_data:
            dept = Department(**data)
            db.add(dept)
            departments.append(dept)

        db.commit()

        doctors_data = [
            {"name": "皮肤科AI智能体", "title": "AI专家团队", "department_id": 1, "hospital": "心灵医生AI智能诊疗平台", "specialty": "真菌性皮肤病、湿疹、痤疮、皮肤过敏、荨麻疹、银屑病、白癜风等各类皮肤疾病的智能诊断与治疗建议", "intro": "由多位资深皮肤科专家知识库训练的AI智能体，专注于皮肤疾病的诊断、治疗建议和健康咨询。支持皮肤影像分析和检查报告解读，为您提供专业、及时的皮肤健康管理服务。", "rating": 5.0, "monthly_answers": 1200, "avg_response_time": "即时响应", "can_prescribe": True, "is_top_hospital": True, "is_ai": True, "is_active": True, "ai_model": "qwen-plus", "ai_temperature": 0.7, "agent_type": "dermatology"},
            {"name": "儿科AI智能体", "title": "AI专家团队", "department_id": 2, "hospital": "心灵医生AI智能诊疗平台", "specialty": "小儿感冒、发热、腹泻、手足口病、小儿肺炎、小儿哮喘、生长发育等儿童常见疾病的智能诊断与健康管理", "intro": "由多位资深儿科专家知识库训练的AI智能体，专注于儿童疾病的诊断、治疗建议和生长发育咨询。为家长提供专业、贴心的儿童健康管理服务。", "rating": 5.0, "monthly_answers": 1500, "avg_response_time": "即时响应", "can_prescribe": True, "is_top_hospital": True, "is_ai": True, "is_active": True, "ai_model": "qwen-plus", "ai_temperature": 0.7, "agent_type": "general"},
            {"name": "妇产科AI智能体", "title": "AI专家团队", "department_id": 3, "hospital": "心灵医生AI智能诊疗平台", "specialty": "妇科炎症、月经不调、子宫肌瘤、盆腔炎、多囊卵巢综合征、孕期保健、产后康复等妇产科疾病的智能诊断与健康管理", "intro": "由多位资深妇产科专家知识库训练的AI智能体，专注于妇科疾病诊断、孕期保健和女性健康管理。为女性提供专业、私密的医疗咨询服务。", "rating": 5.0, "monthly_answers": 1100, "avg_response_time": "即时响应", "can_prescribe": True, "is_top_hospital": True, "is_ai": True, "is_active": True, "ai_model": "qwen-plus", "ai_temperature": 0.7, "agent_type": "general"},
            {"name": "消化内科AI智能体", "title": "AI专家团队", "department_id": 4, "hospital": "心灵医生AI智能诊疗平台", "specialty": "胃炎、胃溃疡、肠炎、脂肪肝、胆囊炎、消化不良等消化系统疾病的智能诊断与治疗建议", "intro": "由多位资深消化内科专家知识库训练的AI智能体，专注于消化系统疾病的诊断、治疗建议和饮食指导。为您提供专业的消化健康管理服务。", "rating": 5.0, "monthly_answers": 980, "avg_response_time": "即时响应", "can_prescribe": True, "is_top_hospital": True, "is_ai": True, "is_active": True, "ai_model": "qwen-plus", "ai_temperature": 0.7, "agent_type": "general"},
            {"name": "呼吸内科AI智能体", "title": "AI专家团队", "department_id": 5, "hospital": "心灵医生AI智能诊疗平台", "specialty": "感冒、支气管炎、肺炎、哮喘、慢性阻塞性肺疾病等呼吸系统疾病的智能诊断与治疗建议", "intro": "由多位资深呼吸内科专家知识库训练的AI智能体，专注于呼吸系统疾病的诊断、治疗建议和呼吸健康管理。为您提供专业的呼吸道疾病咨询服务。", "rating": 5.0, "monthly_answers": 1300, "avg_response_time": "即时响应", "can_prescribe": True, "is_top_hospital": True, "is_ai": True, "is_active": True, "ai_model": "qwen-plus", "ai_temperature": 0.7, "agent_type": "general"},
            {"name": "心血管科AI智能体", "title": "AI专家团队", "department_id": 6, "hospital": "心灵医生AI智能诊疗平台", "specialty": "高血压、冠心病、心律失常、心力衰竭、心肌炎等心血管疾病的智能诊断、风险评估与治疗建议", "intro": "由多位资深心血管专家知识库训练的AI智能体，专注于心血管疾病的诊断、风险评估和健康管理。支持心电图解读和心血管风险评估，为您提供专业的心脏健康管理服务。", "rating": 5.0, "monthly_answers": 850, "avg_response_time": "即时响应", "can_prescribe": True, "is_top_hospital": True, "is_ai": True, "is_active": True, "ai_model": "qwen-plus", "ai_temperature": 0.7, "agent_type": "cardiology"},
            {"name": "内分泌科AI智能体", "title": "AI专家团队", "department_id": 7, "hospital": "心灵医生AI智能诊疗平台", "specialty": "糖尿病、甲状腺功能亢进症、甲状腺功能减退症、骨质疏松症、痛风等内分泌代谢疾病的智能诊断与治疗建议", "intro": "由多位资深内分泌科专家知识库训练的AI智能体，专注于内分泌代谢疾病的诊断、治疗建议和健康管理。为您提供专业的内分泌健康咨询服务。", "rating": 5.0, "monthly_answers": 720, "avg_response_time": "即时响应", "can_prescribe": True, "is_top_hospital": True, "is_ai": True, "is_active": True, "ai_model": "qwen-plus", "ai_temperature": 0.7, "agent_type": "general"},
            {"name": "神经内科AI智能体", "title": "AI专家团队", "department_id": 8, "hospital": "心灵医生AI智能诊疗平台", "specialty": "头痛、失眠症、脑梗死、癫痫、帕金森病等神经系统疾病的智能诊断与治疗建议", "intro": "由多位资深神经内科专家知识库训练的AI智能体，专注于神经系统疾病的诊断、治疗建议和神经健康管理。为您提供专业的神经系统疾病咨询服务。", "rating": 5.0, "monthly_answers": 650, "avg_response_time": "即时响应", "can_prescribe": True, "is_top_hospital": True, "is_ai": True, "is_active": True, "ai_model": "qwen-plus", "ai_temperature": 0.7, "agent_type": "general"},
            {"name": "骨科AI智能体", "title": "AI专家团队", "department_id": 9, "hospital": "心灵医生AI智能诊疗平台", "specialty": "颈椎病、腰椎间盘突出症、骨关节炎、骨折、肩周炎等骨科疾病的智能诊断与治疗建议", "intro": "由多位资深骨科专家知识库训练的AI智能体，专注于骨科疾病的诊断、治疗建议和康复指导。支持X光片解读，为您提供专业的骨骼健康管理服务。", "rating": 5.0, "monthly_answers": 890, "avg_response_time": "即时响应", "can_prescribe": True, "is_top_hospital": True, "is_ai": True, "is_active": True, "ai_model": "qwen-plus", "ai_temperature": 0.7, "agent_type": "orthopedics"},
            {"name": "眼科AI智能体", "title": "AI专家团队", "department_id": 10, "hospital": "心灵医生AI智能诊疗平台", "specialty": "近视、白内障、青光眼、干眼症、结膜炎等眼科疾病的智能诊断与治疗建议", "intro": "由多位资深眼科专家知识库训练的AI智能体，专注于眼科疾病的诊断、治疗建议和视力健康管理。为您提供专业的眼部健康咨询服务。", "rating": 5.0, "monthly_answers": 760, "avg_response_time": "即时响应", "can_prescribe": True, "is_top_hospital": True, "is_ai": True, "is_active": True, "ai_model": "qwen-plus", "ai_temperature": 0.7, "agent_type": "general"},
            {"name": "耳鼻咽喉科AI智能体", "title": "AI专家团队", "department_id": 11, "hospital": "心灵医生AI智能诊疗平台", "specialty": "鼻炎、咽喉炎、中耳炎、鼻窦炎、扁桃体炎等耳鼻咽喉疾病的智能诊断与治疗建议", "intro": "由多位资深耳鼻咽喉科专家知识库训练的AI智能体，专注于耳鼻咽喉疾病的诊断、治疗建议和健康管理。为您提供专业的耳鼻喉健康咨询服务。", "rating": 5.0, "monthly_answers": 680, "avg_response_time": "即时响应", "can_prescribe": True, "is_top_hospital": True, "is_ai": True, "is_active": True, "ai_model": "qwen-plus", "ai_temperature": 0.7, "agent_type": "general"},
            {"name": "口腔科AI智能体", "title": "AI专家团队", "department_id": 12, "hospital": "心灵医生AI智能诊疗平台", "specialty": "龋齿、牙周炎、口腔溃疡、智齿冠周炎、牙髓炎等口腔疾病的智能诊断与治疗建议", "intro": "由多位资深口腔科专家知识库训练的AI智能体，专注于口腔疾病的诊断、治疗建议和口腔健康管理。为您提供专业的口腔健康咨询服务。", "rating": 4.9, "monthly_answers": 580, "avg_response_time": "即时响应", "can_prescribe": False, "is_top_hospital": True, "is_ai": True, "is_active": True, "ai_model": "qwen-plus", "ai_temperature": 0.7, "agent_type": "general"},
        ]

        for data in doctors_data:
            doctor = Doctor(**data)
            db.add(doctor)

        db.commit()

        # 疾病数据
        diseases_data = [
            # 皮肤科 (department_id=1)
            {"name": "湿疹", "pinyin": "shizhen", "pinyin_abbr": "sz", "department_id": 1, "is_hot": True, "view_count": 8520, "sort_order": 1, "overview": "湿疹是一种常见的过敏性皮肤病，表现为皮肤红斑、丘疹、水疱等。", "symptoms": "皮肤瘙痒、红肿、起水疱、渗液、结痂", "recommended_department": "皮肤科"},
            {"name": "痤疮", "pinyin": "cuochuang", "pinyin_abbr": "cc", "aliases": "青春痘,粉刺", "department_id": 1, "is_hot": True, "view_count": 7890, "sort_order": 2, "overview": "痤疮是毛囊皮脂腺的慢性炎症性疾病，多见于青少年。", "symptoms": "面部粉刺、丘疹、脓疱、结节、囊肿", "recommended_department": "皮肤科"},
            {"name": "荨麻疹", "pinyin": "xunmazhen", "pinyin_abbr": "xmz", "department_id": 1, "is_hot": True, "view_count": 6420, "sort_order": 3, "overview": "荨麻疹是一种常见的过敏性皮肤病，表现为风团和瘙痒。", "symptoms": "皮肤出现红色风团、剧烈瘙痒、时起时消", "recommended_department": "皮肤科"},
            {"name": "银屑病", "pinyin": "yinxiebing", "pinyin_abbr": "yxb", "aliases": "牛皮癣", "department_id": 1, "is_hot": False, "view_count": 4230, "sort_order": 4, "overview": "银屑病是一种慢性炎症性皮肤病，表现为红斑和银白色鳞屑。", "symptoms": "皮肤红斑、银白色鳞屑、瘙痒、关节疼痛", "recommended_department": "皮肤科"},
            {"name": "白癜风", "pinyin": "baidiānfeng", "pinyin_abbr": "bdf", "department_id": 1, "is_hot": False, "view_count": 3850, "sort_order": 5, "overview": "白癜风是一种色素脱失性皮肤病，表现为皮肤白斑。", "symptoms": "皮肤出现白色斑块、边界清楚、无痛无痒", "recommended_department": "皮肤科"},
            
            # 儿科 (department_id=2)
            {"name": "小儿感冒", "pinyin": "xiaoerganmao", "pinyin_abbr": "xegm", "department_id": 2, "is_hot": True, "view_count": 9520, "sort_order": 1, "overview": "小儿感冒是儿童最常见的疾病，多由病毒感染引起。", "symptoms": "发热、咳嗽、流鼻涕、打喷嚏、咽痛", "recommended_department": "儿科"},
            {"name": "小儿腹泻", "pinyin": "xiaoerfuxie", "pinyin_abbr": "xefx", "department_id": 2, "is_hot": True, "view_count": 8340, "sort_order": 2, "overview": "小儿腹泻是儿童常见的消化系统疾病。", "symptoms": "大便次数增多、稀便、水样便、腹痛、发热", "recommended_department": "儿科"},
            {"name": "手足口病", "pinyin": "shouzukoubing", "pinyin_abbr": "szkb", "department_id": 2, "is_hot": True, "view_count": 7120, "sort_order": 3, "overview": "手足口病是由肠道病毒引起的传染病，多发于5岁以下儿童。", "symptoms": "手、足、口腔出现疱疹、发热、食欲不振", "recommended_department": "儿科"},
            {"name": "小儿肺炎", "pinyin": "xiaoerfeiyan", "pinyin_abbr": "xefy", "department_id": 2, "is_hot": False, "view_count": 5890, "sort_order": 4, "overview": "小儿肺炎是儿童常见的呼吸系统疾病。", "symptoms": "发热、咳嗽、气促、呼吸困难", "recommended_department": "儿科"},
            {"name": "小儿哮喘", "pinyin": "xiaoerxiaochuan", "pinyin_abbr": "xexc", "department_id": 2, "is_hot": False, "view_count": 4670, "sort_order": 5, "overview": "小儿哮喘是儿童常见的慢性呼吸道疾病。", "symptoms": "反复喘息、咳嗽、胸闷、呼吸困难", "recommended_department": "儿科"},
            
            # 妇产科 (department_id=3)
            {"name": "阴道炎", "pinyin": "yindaoyan", "pinyin_abbr": "ydy", "department_id": 3, "is_hot": True, "view_count": 8920, "sort_order": 1, "overview": "阴道炎是女性常见的妇科炎症。", "symptoms": "阴道分泌物增多、外阴瘙痒、异味、灼热感", "recommended_department": "妇产科"},
            {"name": "月经不调", "pinyin": "yuejingbutiao", "pinyin_abbr": "yjbt", "department_id": 3, "is_hot": True, "view_count": 7650, "sort_order": 2, "overview": "月经不调是指月经周期、经期或经量异常。", "symptoms": "月经周期不规律、经量过多或过少、痛经", "recommended_department": "妇产科"},
            {"name": "子宫肌瘤", "pinyin": "zigongjiliu", "pinyin_abbr": "zgjl", "department_id": 3, "is_hot": True, "view_count": 6430, "sort_order": 3, "overview": "子宫肌瘤是女性生殖器官最常见的良性肿瘤。", "symptoms": "月经量增多、经期延长、腹部包块、压迫症状", "recommended_department": "妇产科"},
            {"name": "盆腔炎", "pinyin": "penqiangyan", "pinyin_abbr": "pqy", "department_id": 3, "is_hot": False, "view_count": 5120, "sort_order": 4, "overview": "盆腔炎是女性上生殖道的感染性疾病。", "symptoms": "下腹痛、发热、阴道分泌物增多", "recommended_department": "妇产科"},
            {"name": "多囊卵巢综合征", "pinyin": "duonangluanchao", "pinyin_abbr": "dnlc", "department_id": 3, "is_hot": False, "view_count": 4890, "sort_order": 5, "overview": "多囊卵巢综合征是育龄女性常见的内分泌代谢疾病。", "symptoms": "月经稀发、多毛、痤疮、肥胖、不孕", "recommended_department": "妇产科"},
            
            # 消化内科 (department_id=4)
            {"name": "胃炎", "pinyin": "weiyan", "pinyin_abbr": "wy", "department_id": 4, "is_hot": True, "view_count": 9230, "sort_order": 1, "overview": "胃炎是胃粘膜的炎症性疾病。", "symptoms": "上腹痛、恶心、呕吐、食欲不振、腹胀", "recommended_department": "消化内科"},
            {"name": "胃溃疡", "pinyin": "weikuiyang", "pinyin_abbr": "wky", "department_id": 4, "is_hot": True, "view_count": 7840, "sort_order": 2, "overview": "胃溃疡是消化性溃疡的一种。", "symptoms": "上腹痛、餐后痛、反酸、嗳气、黑便", "recommended_department": "消化内科"},
            {"name": "肠炎", "pinyin": "changyan", "pinyin_abbr": "cy", "department_id": 4, "is_hot": True, "view_count": 6920, "sort_order": 3, "overview": "肠炎是肠道的炎症性疾病。", "symptoms": "腹泻、腹痛、恶心、呕吐、发热", "recommended_department": "消化内科"},
            {"name": "脂肪肝", "pinyin": "zhifanggan", "pinyin_abbr": "zfg", "department_id": 4, "is_hot": False, "view_count": 5340, "sort_order": 4, "overview": "脂肪肝是肝细胞内脂肪堆积过多的病变。", "symptoms": "多数无症状、可有乏力、肝区不适", "recommended_department": "消化内科"},
            {"name": "胆囊炎", "pinyin": "dannangyan", "pinyin_abbr": "dny", "department_id": 4, "is_hot": False, "view_count": 4670, "sort_order": 5, "overview": "胆囊炎是胆囊的炎症性疾病。", "symptoms": "右上腹痛、发热、恶心、呕吐", "recommended_department": "消化内科"},
            
            # 呼吸内科 (department_id=5)
            {"name": "感冒", "pinyin": "ganmao", "pinyin_abbr": "gm", "aliases": "上呼吸道感染", "department_id": 5, "is_hot": True, "view_count": 10520, "sort_order": 1, "overview": "感冒是最常见的急性呼吸道感染性疾病。", "symptoms": "鼻塞、流涕、打喷嚏、咽痛、咳嗽、发热", "recommended_department": "呼吸内科"},
            {"name": "支气管炎", "pinyin": "zhiqiguanyan", "pinyin_abbr": "zqgy", "department_id": 5, "is_hot": True, "view_count": 8340, "sort_order": 2, "overview": "支气管炎是支气管粘膜的炎症。", "symptoms": "咳嗽、咳痰、气促、胸闷", "recommended_department": "呼吸内科"},
            {"name": "肺炎", "pinyin": "feiyan", "pinyin_abbr": "fy", "department_id": 5, "is_hot": True, "view_count": 7650, "sort_order": 3, "overview": "肺炎是肺部的感染性疾病。", "symptoms": "发热、咳嗽、咳痰、胸痛、呼吸困难", "recommended_department": "呼吸内科"},
            {"name": "哮喘", "pinyin": "xiaochuan", "pinyin_abbr": "xc", "department_id": 5, "is_hot": False, "view_count": 6120, "sort_order": 4, "overview": "哮喘是慢性气道炎症性疾病。", "symptoms": "反复喘息、气促、胸闷、咳嗽", "recommended_department": "呼吸内科"},
            {"name": "慢性阻塞性肺疾病", "pinyin": "manxingzusaixing", "pinyin_abbr": "mxzsx", "aliases": "慢阻肺,COPD", "department_id": 5, "is_hot": False, "view_count": 4890, "sort_order": 5, "overview": "慢阻肺是一种常见的慢性呼吸系统疾病。", "symptoms": "慢性咳嗽、咳痰、气促、呼吸困难", "recommended_department": "呼吸内科"},
            
            # 心血管内科 (department_id=6)
            {"name": "高血压", "pinyin": "gaoxueya", "pinyin_abbr": "gxy", "department_id": 6, "is_hot": True, "view_count": 11230, "sort_order": 1, "overview": "高血压是最常见的慢性病之一。", "symptoms": "头痛、头晕、心悸、胸闷、乏力", "recommended_department": "心血管内科"},
            {"name": "冠心病", "pinyin": "guanxinbing", "pinyin_abbr": "gxb", "department_id": 6, "is_hot": True, "view_count": 8920, "sort_order": 2, "overview": "冠心病是冠状动脉粥样硬化性心脏病。", "symptoms": "胸痛、胸闷、心悸、气短", "recommended_department": "心血管内科"},
            {"name": "心律失常", "pinyin": "xinlvshichang", "pinyin_abbr": "xlsc", "department_id": 6, "is_hot": True, "view_count": 7340, "sort_order": 3, "overview": "心律失常是心脏节律异常的统称。", "symptoms": "心悸、胸闷、头晕、乏力、晕厥", "recommended_department": "心血管内科"},
            {"name": "心力衰竭", "pinyin": "xinlishuaijie", "pinyin_abbr": "xlsj", "aliases": "心衰", "department_id": 6, "is_hot": False, "view_count": 5670, "sort_order": 4, "overview": "心力衰竭是各种心脏疾病的终末阶段。", "symptoms": "呼吸困难、乏力、水肿、咳嗽", "recommended_department": "心血管内科"},
            {"name": "心肌炎", "pinyin": "xinjiyan", "pinyin_abbr": "xjy", "department_id": 6, "is_hot": False, "view_count": 4230, "sort_order": 5, "overview": "心肌炎是心肌的炎症性疾病。", "symptoms": "胸痛、心悸、乏力、气促、发热", "recommended_department": "心血管内科"},
            
            # 内分泌科 (department_id=7)
            {"name": "糖尿病", "pinyin": "tangniaobing", "pinyin_abbr": "tnb", "department_id": 7, "is_hot": True, "view_count": 10890, "sort_order": 1, "overview": "糖尿病是一组以高血糖为特征的代谢性疾病。", "symptoms": "多饮、多尿、多食、体重下降、乏力", "recommended_department": "内分泌科"},
            {"name": "甲状腺功能亢进症", "pinyin": "jiazhuangxian", "pinyin_abbr": "jzx", "aliases": "甲亢", "department_id": 7, "is_hot": True, "view_count": 8120, "sort_order": 2, "overview": "甲亢是甲状腺激素分泌过多引起的疾病。", "symptoms": "心悸、多汗、怕热、消瘦、手抖、突眼", "recommended_department": "内分泌科"},
            {"name": "甲状腺功能减退症", "pinyin": "jiazhuangxian", "pinyin_abbr": "jzx", "aliases": "甲减", "department_id": 7, "is_hot": True, "view_count": 6890, "sort_order": 3, "overview": "甲减是甲状腺激素分泌不足引起的疾病。", "symptoms": "乏力、怕冷、便秘、体重增加、记忆力减退", "recommended_department": "内分泌科"},
            {"name": "骨质疏松症", "pinyin": "guzhisusong", "pinyin_abbr": "gzss", "department_id": 7, "is_hot": False, "view_count": 5340, "sort_order": 4, "overview": "骨质疏松症是以骨量减少为特征的代谢性骨病。", "symptoms": "腰背疼痛、身高变矮、驼背、易骨折", "recommended_department": "内分泌科"},
            {"name": "痛风", "pinyin": "tongfeng", "pinyin_abbr": "tf", "department_id": 7, "is_hot": False, "view_count": 4670, "sort_order": 5, "overview": "痛风是嘌呤代谢紊乱引起的疾病。", "symptoms": "关节红肿热痛、多发于大脚趾、夜间发作", "recommended_department": "内分泌科"},
            
            # 神经内科 (department_id=8)
            {"name": "头痛", "pinyin": "toutong", "pinyin_abbr": "tt", "department_id": 8, "is_hot": True, "view_count": 9670, "sort_order": 1, "overview": "头痛是神经内科最常见的症状之一。", "symptoms": "头部疼痛、可伴恶心、呕吐、畏光", "recommended_department": "神经内科"},
            {"name": "失眠症", "pinyin": "shimianzheng", "pinyin_abbr": "smz", "department_id": 8, "is_hot": True, "view_count": 8340, "sort_order": 2, "overview": "失眠症是常见的睡眠障碍。", "symptoms": "入睡困难、睡眠浅、早醒、多梦", "recommended_department": "神经内科"},
            {"name": "脑梗死", "pinyin": "naogengsi", "pinyin_abbr": "ngs", "aliases": "脑梗塞,中风", "department_id": 8, "is_hot": True, "view_count": 7120, "sort_order": 3, "overview": "脑梗死是脑血管病最常见的类型。", "symptoms": "突发肢体无力、言语不清、面瘫、头晕", "recommended_department": "神经内科"},
            {"name": "癫痫", "pinyin": "dianxian", "pinyin_abbr": "dx", "department_id": 8, "is_hot": False, "view_count": 5890, "sort_order": 4, "overview": "癫痫是大脑神经元异常放电引起的疾病。", "symptoms": "突然意识丧失、抽搐、口吐白沫", "recommended_department": "神经内科"},
            {"name": "帕金森病", "pinyin": "pajinsenbing", "pinyin_abbr": "pjsb", "department_id": 8, "is_hot": False, "view_count": 4230, "sort_order": 5, "overview": "帕金森病是常见的神经退行性疾病。", "symptoms": "静止性震颤、肌强直、运动迟缓、姿势步态异常", "recommended_department": "神经内科"},
            
            # 骨科 (department_id=9)
            {"name": "颈椎病", "pinyin": "jingzhuibing", "pinyin_abbr": "jzb", "department_id": 9, "is_hot": True, "view_count": 9890, "sort_order": 1, "overview": "颈椎病是颈椎退行性改变引起的疾病。", "symptoms": "颈肩痛、上肢麻木、头晕、头痛", "recommended_department": "骨科"},
            {"name": "腰椎间盘突出症", "pinyin": "yaozhuijianpan", "pinyin_abbr": "yzjp", "department_id": 9, "is_hot": True, "view_count": 8670, "sort_order": 2, "overview": "腰椎间盘突出症是常见的脊柱疾病。", "symptoms": "腰痛、下肢放射痛、麻木、肌力减退", "recommended_department": "骨科"},
            {"name": "骨关节炎", "pinyin": "guguanjieyan", "pinyin_abbr": "ggjy", "department_id": 9, "is_hot": True, "view_count": 7340, "sort_order": 3, "overview": "骨关节炎是关节软骨退行性改变。", "symptoms": "关节疼痛、僵硬、活动受限、肿胀", "recommended_department": "骨科"},
            {"name": "骨折", "pinyin": "guzhe", "pinyin_abbr": "gz", "department_id": 9, "is_hot": False, "view_count": 6120, "sort_order": 4, "overview": "骨折是骨的完整性或连续性中断。", "symptoms": "局部疼痛、肿胀、畸形、功能障碍", "recommended_department": "骨科"},
            {"name": "肩周炎", "pinyin": "jianzhouyan", "pinyin_abbr": "jzy", "aliases": "五十肩,冻结肩", "department_id": 9, "is_hot": False, "view_count": 5230, "sort_order": 5, "overview": "肩周炎是肩关节周围软组织的慢性炎症。", "symptoms": "肩部疼痛、活动受限、夜间痛", "recommended_department": "骨科"},
            
            # 眼科 (department_id=10)
            {"name": "近视", "pinyin": "jinshi", "pinyin_abbr": "js", "department_id": 10, "is_hot": True, "view_count": 10230, "sort_order": 1, "overview": "近视是最常见的屈光不正。", "symptoms": "远视力下降、视物模糊、眼疲劳", "recommended_department": "眼科"},
            {"name": "白内障", "pinyin": "bainezhang", "pinyin_abbr": "bnz", "department_id": 10, "is_hot": True, "view_count": 8120, "sort_order": 2, "overview": "白内障是晶状体混浊引起的视力障碍。", "symptoms": "视力下降、视物模糊、畏光、眩光", "recommended_department": "眼科"},
            {"name": "青光眼", "pinyin": "qingguangyan", "pinyin_abbr": "qgy", "department_id": 10, "is_hot": True, "view_count": 6890, "sort_order": 3, "overview": "青光眼是以视神经损害为特征的眼病。", "symptoms": "眼痛、视力下降、视野缺损、虹视", "recommended_department": "眼科"},
            {"name": "干眼症", "pinyin": "ganyanzheng", "pinyin_abbr": "gyz", "department_id": 10, "is_hot": False, "view_count": 5670, "sort_order": 4, "overview": "干眼症是泪液分泌或质量异常引起的眼表疾病。", "symptoms": "眼干、眼涩、异物感、烧灼感、视疲劳", "recommended_department": "眼科"},
            {"name": "结膜炎", "pinyin": "jiemoyan", "pinyin_abbr": "jmy", "aliases": "红眼病", "department_id": 10, "is_hot": False, "view_count": 4890, "sort_order": 5, "overview": "结膜炎是结膜的炎症性疾病。", "symptoms": "眼红、眼痒、分泌物增多、异物感", "recommended_department": "眼科"},
            
            # 耳鼻咽喉科 (department_id=11)
            {"name": "鼻炎", "pinyin": "biyan", "pinyin_abbr": "by", "department_id": 11, "is_hot": True, "view_count": 9340, "sort_order": 1, "overview": "鼻炎是鼻腔粘膜的炎症性疾病。", "symptoms": "鼻塞、流涕、打喷嚏、鼻痒", "recommended_department": "耳鼻咽喉科"},
            {"name": "咽喉炎", "pinyin": "yanhouyan", "pinyin_abbr": "yhy", "department_id": 11, "is_hot": True, "view_count": 8120, "sort_order": 2, "overview": "咽喉炎是咽喉部粘膜的炎症。", "symptoms": "咽痛、咽干、咽部异物感、声音嘶哑", "recommended_department": "耳鼻咽喉科"},
            {"name": "中耳炎", "pinyin": "zhongeryan", "pinyin_abbr": "zey", "department_id": 11, "is_hot": True, "view_count": 6780, "sort_order": 3, "overview": "中耳炎是中耳的炎症性疾病。", "symptoms": "耳痛、耳鸣、听力下降、耳流脓", "recommended_department": "耳鼻咽喉科"},
            {"name": "鼻窦炎", "pinyin": "bidouyan", "pinyin_abbr": "bdy", "department_id": 11, "is_hot": False, "view_count": 5450, "sort_order": 4, "overview": "鼻窦炎是鼻窦粘膜的炎症。", "symptoms": "鼻塞、流脓涕、头痛、嗅觉减退", "recommended_department": "耳鼻咽喉科"},
            {"name": "扁桃体炎", "pinyin": "biantaotiyan", "pinyin_abbr": "btty", "department_id": 11, "is_hot": False, "view_count": 4670, "sort_order": 5, "overview": "扁桃体炎是扁桃体的炎症性疾病。", "symptoms": "咽痛、发热、吞咽困难、扁桃体肿大", "recommended_department": "耳鼻咽喉科"},
            
            # 口腔科 (department_id=12)
            {"name": "龋齿", "pinyin": "quchi", "pinyin_abbr": "qc", "aliases": "蛀牙,虫牙", "department_id": 12, "is_hot": True, "view_count": 9120, "sort_order": 1, "overview": "龋齿是牙齿硬组织的细菌性疾病。", "symptoms": "牙痛、牙齿敏感、牙洞、食物嵌塞", "recommended_department": "口腔科"},
            {"name": "牙周炎", "pinyin": "yazhouyan", "pinyin_abbr": "yzy", "department_id": 12, "is_hot": True, "view_count": 7890, "sort_order": 2, "overview": "牙周炎是牙周组织的慢性炎症。", "symptoms": "牙龈出血、牙龈肿胀、牙齿松动、口臭", "recommended_department": "口腔科"},
            {"name": "口腔溃疡", "pinyin": "kouqiangkuiyang", "pinyin_abbr": "kqky", "department_id": 12, "is_hot": True, "view_count": 6670, "sort_order": 3, "overview": "口腔溃疡是口腔粘膜的溃疡性损害。", "symptoms": "口腔粘膜溃疡、疼痛、进食困难", "recommended_department": "口腔科"},
            {"name": "智齿冠周炎", "pinyin": "zhichiguanzhouyan", "pinyin_abbr": "zcgzy", "department_id": 12, "is_hot": False, "view_count": 5340, "sort_order": 4, "overview": "智齿冠周炎是智齿周围软组织的炎症。", "symptoms": "智齿区疼痛、肿胀、张口困难、发热", "recommended_department": "口腔科"},
            {"name": "牙髓炎", "pinyin": "yasuiyan", "pinyin_abbr": "ysy", "department_id": 12, "is_hot": False, "view_count": 4560, "sort_order": 5, "overview": "牙髓炎是牙髓组织的炎症。", "symptoms": "剧烈牙痛、夜间痛、冷热刺激痛", "recommended_department": "口腔科"},
        ]

        for data in diseases_data:
            disease = Disease(**data)
            db.add(disease)

        db.commit()
        
        # 药品分类数据
        drug_categories_data = [
            {"name": "热门药品", "icon": "flame", "description": "常用热门药品", "display_type": "grid", "sort_order": 1, "is_active": True},
            {"name": "感冒发烧", "icon": "thermometer", "description": "感冒发烧相关药品", "display_type": "grid", "sort_order": 2, "is_active": True},
            {"name": "消化系统", "icon": "pills", "description": "消化系统用药", "display_type": "grid", "sort_order": 3, "is_active": True},
            {"name": "皮肤用药", "icon": "hand.raised", "description": "皮肤病用药", "display_type": "grid", "sort_order": 4, "is_active": True},
            {"name": "心脑血管", "icon": "heart", "description": "心脑血管用药", "display_type": "grid", "sort_order": 5, "is_active": True},
            {"name": "孕期/哺乳期", "icon": "figure.and.child.holdinghands", "description": "孕期哺乳期安全用药", "display_type": "grid", "sort_order": 6, "is_active": True},
        ]
        
        categories = []
        for data in drug_categories_data:
            cat = DrugCategory(**data)
            db.add(cat)
            categories.append(cat)
        
        db.commit()
        
        # 药品数据
        drugs_data = [
            # 感冒发烧类
            {"name": "布洛芬", "pinyin": "buluofen", "pinyin_abbr": "blf", "common_brands": "芬必得、美林", "pregnancy_level": "C", "pregnancy_desc": "孕晚期禁用", "lactation_level": "L1", "lactation_desc": "哺乳期较安全", "children_usable": True, "children_desc": "6个月以上儿童可用", "indications": "用于缓解轻至中度疼痛如头痛、关节痛、偏头痛、牙痛、肌肉痛、神经痛、痛经。也用于普通感冒或流行性感冒引起的发热。", "contraindications": "对本品过敏者禁用；消化性溃疡患者禁用；严重肝肾功能不全者禁用。", "dosage": "成人：一次0.2g（1片），一日2-3次。儿童：按体重一次5-10mg/kg，每6-8小时一次。", "side_effects": "可见恶心、呕吐、胃烧灼感、轻度消化不良、皮疹、头痛、头晕等。", "precautions": "不得空腹服用；不得长期或大量使用；与其他解热镇痛药同用可增加胃肠道不良反应。", "storage": "遮光，密封保存。", "is_hot": True, "sort_order": 1, "view_count": 8520},
            {"name": "对乙酰氨基酚", "pinyin": "duiyixiananjifeng", "pinyin_abbr": "dyxajf", "common_brands": "泰诺、百服宁、必理通", "aliases": "扑热息痛", "pregnancy_level": "B", "pregnancy_desc": "孕期相对安全", "lactation_level": "L1", "lactation_desc": "哺乳期安全", "children_usable": True, "children_desc": "3个月以上儿童可用", "indications": "用于普通感冒或流行性感冒引起的发热，也用于缓解轻至中度疼痛如头痛、关节痛、偏头痛、牙痛、肌肉痛、神经痛、痛经。", "contraindications": "对本品过敏者禁用；严重肝肾功能不全者禁用。", "dosage": "成人：一次0.5g，每4-6小时一次，24小时内不超过2g。儿童：按体重一次10-15mg/kg，每4-6小时一次。", "side_effects": "偶见皮疹、荨麻疹、药热及粒细胞减少。长期大量用药可导致肝肾损害。", "precautions": "肝肾功能不全者慎用；不得同时服用含对乙酰氨基酚的其他药品；饮酒者慎用。", "storage": "遮光，密封保存。", "is_hot": True, "sort_order": 2, "view_count": 7890},
            {"name": "阿奇霉素", "pinyin": "aqimeisu", "pinyin_abbr": "aqms", "common_brands": "希舒美、舒美特", "pregnancy_level": "B", "pregnancy_desc": "孕期较安全", "lactation_level": "L2", "lactation_desc": "哺乳期较安全", "children_usable": True, "children_desc": "6个月以上儿童可用", "indications": "适用于敏感细菌所引起的呼吸道感染、皮肤软组织感染、沙眼衣原体所致单纯性生殖器感染等。", "contraindications": "对阿奇霉素、红霉素或其他大环内酯类药物过敏者禁用。", "dosage": "成人：一次0.5g，一日1次，连用3天。儿童：按体重一次10mg/kg，一日1次，连用3天。", "side_effects": "可见腹泻、恶心、腹痛、稀便、呕吐等胃肠道反应。", "precautions": "肝功能不全者慎用；不宜与抗酸药同时服用；饭前1小时或饭后2小时服用。", "storage": "遮光，密封，在干燥处保存。", "is_hot": True, "sort_order": 3, "view_count": 6420},
            {"name": "奥司他韦", "pinyin": "aositawei", "pinyin_abbr": "astw", "common_brands": "达菲、可威", "pregnancy_level": "C", "pregnancy_desc": "孕期权衡利弊使用", "lactation_level": "L2", "lactation_desc": "哺乳期较安全", "children_usable": True, "children_desc": "1岁以上儿童可用", "indications": "用于成人和1岁及1岁以上儿童的甲型和乙型流感治疗。用于成人和13岁及13岁以上青少年的甲型和乙型流感的预防。", "contraindications": "对本品任何成分过敏者禁用。", "dosage": "成人治疗：一次75mg，一日2次，连续5天。成人预防：一次75mg，一日1次，至少7天。儿童按体重调整剂量。", "side_effects": "常见恶心、呕吐、腹泻、腹痛、头痛等。", "precautions": "应在流感症状开始的48小时内使用；肾功能不全者需调整剂量。", "storage": "密封保存。", "is_hot": True, "sort_order": 4, "view_count": 5890},
            
            # 消化系统类
            {"name": "奥美拉唑", "pinyin": "aomeilazuo", "pinyin_abbr": "amlz", "common_brands": "洛赛克、奥克", "pregnancy_level": "C", "pregnancy_desc": "孕期权衡利弊使用", "lactation_level": "L2", "lactation_desc": "哺乳期较安全", "children_usable": True, "children_desc": "1岁以上儿童可用", "indications": "适用于胃溃疡、十二指肠溃疡、应激性溃疡、反流性食管炎和卓-艾综合征（胃泌素瘤）。", "contraindications": "对本品过敏者禁用。", "dosage": "成人：一次20mg，一日1-2次。十二指肠溃疡疗程通常为2-4周。", "side_effects": "可见腹泻、头痛、恶心、腹痛、便秘、胀气等。", "precautions": "不宜长期使用；肝功能不全者慎用；可能掩盖胃癌症状。", "storage": "遮光，密封保存。", "is_hot": True, "sort_order": 5, "view_count": 4670},
            {"name": "蒙脱石散", "pinyin": "mengtuoshisan", "pinyin_abbr": "mtss", "common_brands": "思密达、必奇", "pregnancy_level": "B", "pregnancy_desc": "孕期安全", "lactation_level": "L1", "lactation_desc": "哺乳期安全", "children_usable": True, "children_desc": "新生儿可用", "indications": "用于成人及儿童急、慢性腹泻。用于食道、胃、十二指肠疾病引起的相关疼痛症状的辅助治疗。", "contraindications": "对本品过敏者禁用。", "dosage": "成人：一次1袋（3g），一日3次。儿童：1岁以下一日1袋，1-2岁一日1-2袋，2岁以上一日2-3袋。", "side_effects": "可见便秘，通常减量后可消失。", "precautions": "空腹服用效果更佳；严重便秘者慎用；不影响其他药物吸收。", "storage": "密封保存。", "is_hot": True, "sort_order": 6, "view_count": 4230},
            
            # 皮肤用药类
            {"name": "莫匹罗星软膏", "pinyin": "mobiluoxing", "pinyin_abbr": "mplx", "common_brands": "百多邦", "pregnancy_level": "B", "pregnancy_desc": "孕期较安全", "lactation_level": "L1", "lactation_desc": "哺乳期安全", "children_usable": True, "children_desc": "儿童可用", "indications": "本品为局部外用抗生素，适用于革兰阳性球菌引起的皮肤感染，如脓疱病、疖肿、毛囊炎等原发性皮肤感染及湿疹合并感染、溃疡合并感染、创伤合并感染等继发性感染。", "contraindications": "对本品过敏者禁用。", "dosage": "外用。取适量本品涂于患处，一日3次，疗程5天。可根据病情适当延长，但不宜超过10天。", "side_effects": "偶见局部烧灼感、刺痛、瘙痒、干燥、红斑等。", "precautions": "避免接触眼睛和其他黏膜；不宜大面积使用；不宜长期使用。", "storage": "密封保存。", "is_hot": False, "sort_order": 7, "view_count": 3850},
            {"name": "炉甘石洗剂", "pinyin": "luganshixiji", "pinyin_abbr": "lgsxj", "pregnancy_level": "A", "pregnancy_desc": "孕期安全", "lactation_level": "L1", "lactation_desc": "哺乳期安全", "children_usable": True, "children_desc": "儿童可用", "indications": "用于急性瘙痒性皮肤病，如湿疹、痱子等。", "contraindications": "对本品过敏者禁用；有渗出液的皮肤部位禁用。", "dosage": "外用。用时摇匀，取适量涂于患处，一日2-3次。", "side_effects": "偶见过敏反应。", "precautions": "仅供外用，不得口服；避免接触眼睛和黏膜；用前摇匀。", "storage": "密封保存。", "is_hot": False, "sort_order": 8, "view_count": 3520},
            
            # 心脑血管类
            {"name": "阿司匹林", "pinyin": "asipiling", "pinyin_abbr": "aspl", "common_brands": "拜阿司匹灵、阿司匹林肠溶片", "pregnancy_level": "D", "pregnancy_desc": "孕期慎用", "lactation_level": "L3", "lactation_desc": "哺乳期慎用", "children_usable": False, "children_desc": "儿童慎用，可能引起瑞氏综合征", "indications": "用于预防心脑血管疾病；用于解热镇痛；用于抗风湿。", "contraindications": "对阿司匹林过敏者禁用；活动性溃疡病或其他原因引起的消化道出血禁用；血友病或血小板减少症禁用。", "dosage": "预防心脑血管疾病：一次75-100mg，一日1次。解热镇痛：一次0.3-0.6g，一日3次。", "side_effects": "可见胃肠道反应、出血倾向、过敏反应等。", "precautions": "餐后服用；不宜与抗凝药同用；定期检查凝血功能。", "storage": "遮光，密封保存。", "is_hot": True, "sort_order": 9, "view_count": 5670},
            {"name": "硝苯地平", "pinyin": "xiaobendeping", "pinyin_abbr": "xbdp", "common_brands": "拜新同、伲福达", "pregnancy_level": "C", "pregnancy_desc": "孕期权衡利弊使用", "lactation_level": "L2", "lactation_desc": "哺乳期较安全", "children_usable": False, "children_desc": "儿童用药安全性未确立", "indications": "用于治疗高血压、冠心病、心绞痛。", "contraindications": "对本品过敏者禁用；心源性休克禁用；急性心肌梗死禁用。", "dosage": "控释片：一次30mg，一日1次。缓释片：一次10-20mg，一日2-3次。", "side_effects": "可见头痛、面部潮红、心悸、踝部水肿等。", "precautions": "不宜突然停药；低血压患者慎用；肝功能不全者慎用。", "storage": "遮光，密封保存。", "is_hot": False, "sort_order": 10, "view_count": 4890},
        ]
        
        for drug_data in drugs_data:
            drug = Drug(**drug_data)
            db.add(drug)
            
            # 根据药品名称分配分类
            if drug.name in ["布洛芬", "对乙酰氨基酚", "阿奇霉素", "奥司他韦"]:
                drug.categories.append(categories[0])  # 热门药品
                drug.categories.append(categories[1])  # 感冒发烧
            elif drug.name in ["奥美拉唑", "蒙脱石散"]:
                drug.categories.append(categories[0])  # 热门药品
                drug.categories.append(categories[2])  # 消化系统
            elif drug.name in ["莫匹罗星软膏", "炉甘石洗剂"]:
                drug.categories.append(categories[3])  # 皮肤用药
            elif drug.name in ["阿司匹林", "硝苯地平"]:
                drug.categories.append(categories[4])  # 心脑血管
        
        db.commit()
        print("初始化数据完成！")

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
