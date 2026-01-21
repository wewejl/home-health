#!/usr/bin/env python3
"""
扩展医疗数据种子脚本
添加更多常见疾病和药品数据，达到验收标准
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.disease import Disease
from app.models.drug import Drug, DrugCategory
from app.models.department import Department


def seed_extended_diseases(db: Session):
    """扩展疾病数据"""
    print("开始扩展疾病数据...")

    # 获取现有科室
    departments = {d.name: d.id for d in db.query(Department).all()}

    # 扩展疾病数据（基于常见疾病）
    extended_diseases = [
        # 呼吸内科更多疾病
        {"name": "急性上呼吸道感染", "pinyin": "jixingshanghuxidao ganran", "department_id": departments.get("呼吸内科", 5), "is_hot": True, "overview": "急性上呼吸道感染是最常见的感染性疾病。", "symptoms": "鼻塞、流涕、咽痛、咳嗽、发热、乏力", "recommended_department": "呼吸内科", "view_count": 8500},
        {"name": "急性支气管炎", "pinyin": "jixingzhiqiguanyan", "department_id": departments.get("呼吸内科", 5), "overview": "急性支气管炎是支气管的急性炎症。", "symptoms": "咳嗽、咳痰、胸闷、气促", "recommended_department": "呼吸内科", "view_count": 7200},
        {"name": "肺气肿", "pinyin": "feiqizhong", "department_id": departments.get("呼吸内科", 5), "overview": "肺气肿是末梢支气管远端气腔异常扩大。", "symptoms": "呼吸困难、咳嗽、咳痰", "recommended_department": "呼吸内科", "view_count": 4200},
        {"name": "胸膜炎", "pinyin": "xiongmoyan", "department_id": departments.get("呼吸内科", 5), "overview": "胸膜炎是胸膜的炎症。", "symptoms": "胸痛、呼吸困难、发热", "recommended_department": "呼吸内科", "view_count": 3800},

        # 心血管内科更多疾病
        {"name": "心肌梗死", "pinyin": "xinjigengsi", "aliases": "心梗", "department_id": departments.get("心血管内科", 6), "is_hot": True, "overview": "心肌梗死是冠状动脉急性阻塞引起的心肌坏死。", "symptoms": "剧烈胸痛、心悸、呼吸困难、大汗淋漓", "recommended_department": "心血管内科", "view_count": 9200},
        {"name": "心绞痛", "pinyin": "xinjiaotong", "department_id": departments.get("心血管内科", 6), "is_hot": True, "overview": "心绞痛是由于冠状动脉供血不足引起的。", "symptoms": "胸痛、胸闷、心悸", "recommended_department": "心血管内科", "view_count": 7800},
        {"name": "高血压危象", "pinyin": "gaoxueya wei xiang", "department_id": departments.get("心血管内科", 6), "overview": "高血压危象是高血压急症。", "symptoms": "剧烈头痛、呕吐、视力模糊、意识障碍", "recommended_department": "心血管内科", "view_count": 6500},
        {"name": "风湿性心脏病", "pinyin": "fengshixingxinzangbing", "department_id": departments.get("心血管内科", 6), "overview": "风湿性心脏病是风湿热引起的瓣膜损害。", "symptoms": "心悸、气促、水肿、关节痛", "recommended_department": "心血管内科", "view_count": 5100},
        {"name": "先天性心脏病", "pinyin": "xiantianxingxinzangbing", "department_id": departments.get("心血管内科", 6), "overview": "先天性心脏病是出生时的心脏结构异常。", "symptoms": "心悸、气促、乏力、发育迟缓", "recommended_department": "心血管内科", "view_count": 4200},

        # 消化内科更多疾病
        {"name": "功能性消化不良", "pinyin": "gongnengxingxiaohua buliang", "department_id": departments.get("消化内科", 4), "overview": "功能性消化不良是常见的消化功能紊乱。", "symptoms": "上腹痛、腹胀、恶心、早饱、嗳气", "recommended_department": "消化内科", "view_count": 8700},
        {"name": "反流性食管炎", "pinyin": "fanliuxishiguan yan", "aliases": "GERD", "department_id": departments.get("消化内科", 4), "is_hot": True, "overview": "反流性食管炎是胃内容物反流食管引起的炎症。", "symptoms": "烧心、反酸、胸骨后疼痛", "recommended_department": "消化内科", "view_count": 8200},
        {"name": "急性胃炎", "pinyin": "jixingweiyan", "department_id": departments.get("消化内科", 4), "overview": "急性胃炎是胃粘膜的急性炎症。", "symptoms": "上腹痛、恶心、呕吐、发热", "recommended_department": "消化内科", "view_count": 7800},
        {"name": "慢性胃炎", "pinyin": "manxingweiyan", "department_id": departments.get("消化内科", 4), "overview": "慢性胃炎是胃粘膜的慢性炎症。", "symptoms": "上腹痛、饱胀、嗳气、食欲不振", "recommended_department": "消化内科", "view_count": 6500},
        {"name": "十二指肠溃疡", "pinyin": "shierzhichang kuiyang", "department_id": departments.get("消化内科", 4), "is_hot": True, "overview": "十二指肠溃疡是十二指肠的消化性溃疡。", "symptoms": "上腹痛、餐后痛、夜间痛、反酸", "recommended_department": "消化内科", "view_count": 7200},
        {"name": "急性肠炎", "pinyin": "jixingchangyan", "department_id": departments.get("消化内科", 4), "overview": "急性肠炎是肠道的急性炎症。", "symptoms": "腹泻、腹痛、恶心、呕吐、发热", "recommended_department": "消化内科", "view_count": 6800},
        {"name": "慢性肠炎", "pinyin": "manxingchangyan", "department_id": departments.get("消化内科", 4), "overview": "慢性肠炎是肠道的慢性炎症。", "symptoms": "腹泻、腹痛、腹胀、食欲不振", "recommended_department": "消化内科", "view_count": 5200},
        {"name": "肝硬化", "pinyin": "ganyinghua", "department_id": departments.get("消化内科", 4), "overview": "肝硬化是肝脏慢性病变的终末期。", "symptoms": "乏力、食欲不振、黄疸、腹水、出血倾向", "recommended_department": "消化内科", "view_count": 4800},

        # 内分泌科更多疾病
        {"name": "糖尿病肾病", "pinyin": "tangniaobing shen bing", "department_id": departments.get("内分泌科", 7), "overview": "糖尿病肾病是糖尿病的微血管并发症。", "symptoms": "蛋白尿、水肿、高血压、肾功能减退", "recommended_department": "内分泌科", "view_count": 6500},
        {"name": "糖尿病视网膜病变", "pinyin": "tangniaobing shiwang mobian", "department_id": departments.get("内分泌科", 7), "overview": "糖尿病视网膜病变是糖尿病的眼部并发症。", "symptoms": "视力下降、视物模糊、飞蚊症", "recommended_department": "内分泌科", "view_count": 5800},
        {"name": "糖尿病足", "pinyin": "tangniaobing zu", "department_id": departments.get("内分泌科", 7), "overview": "糖尿病足是糖尿病的周围神经病变。", "symptoms": "足部溃疡、感染、疼痛、感觉异常", "recommended_department": "内分泌科", "view_count": 5200},
        {"name": "甲状腺结节", "pinyin": "jiazhuangxian jiejie", "department_id": departments.get("内分泌科", 7), "is_hot": True, "overview": "甲状腺结节是甲状腺内的异常增生。", "symptoms": "颈部肿块、压迫感、多数无症状", "recommended_department": "内分泌科", "view_count": 9800},
        {"name": "甲状腺炎", "pinyin": "jiazhuangxian yan", "department_id": departments.get("内分泌科", 7), "overview": "甲状腺炎是甲状腺的炎症。", "symptoms": "甲状腺肿大、疼痛、发热", "recommended_department": "内分泌科", "view_count": 6200},
        {"name": "库欣综合征", "pinyin": "kuxin zonghe zheng", "aliases": "皮质醇增多症", "department_id": departments.get("内分泌科", 7), "overview": "库欣综合征是肾上腺皮质激素过多的疾病。", "symptoms": "向心性肥胖、满月脸、紫纹、高血压", "recommended_department": "内分泌科", "view_count": 3800},

        # 神经内科更多疾病
        {"name": "偏头痛", "pinyin": "piantoutong", "department_id": departments.get("神经内科", 8), "is_hot": True, "overview": "偏头痛是常见的原发性头痛。", "symptoms": "单侧搏动性头痛、恶心、畏光、畏声", "recommended_department": "神经内科", "view_count": 8900},
        {"name": "紧张性头痛", "pinyin": "jinzhangxing toutong", "department_id": departments.get("神经内科", 8), "overview": "紧张性头痛是最常见的慢性头痛。", "symptoms": "双侧压迫性头痛、紧箍感", "recommended_department": "神经内科", "view_count": 7800},
        {"name": "三叉神经痛", "pinyin": "sachashenjingtong", "department_id": departments.get("神经内科", 8), "overview": "三叉神经痛是面部神经的剧烈疼痛。", "symptoms": "面部剧痛、触发性疼痛、刷牙、进食诱发", "recommended_department": "神经内科", "view_count": 6200},
        {"name": "面神经麻痹", "pinyin": "mianshenjing ma bi", "aliases": "面瘫", "department_id": departments.get("神经内科", 8), "overview": "面神经麻痹是面部神经的急性炎症。", "symptoms": "口眼歪斜、眼睑闭合不全、流口水", "recommended_department": "神经内科", "view_count": 5800},
        {"name": "带状疱疹", "pinyin": "daizhuangpaozhen", "department_id": departments.get("神经内科", 8), "is_hot": True, "overview": "带状疱疹是由水痘-带状疱疹病毒引起的。", "symptoms": "沿神经分布的水疱、剧烈疼痛", "recommended_department": "神经内科", "view_count": 7200},
        {"name": "坐骨神经痛", "pinyin": "zuogushenjingtong", "department_id": departments.get("神经内科", 8), "overview": "坐骨神经痛是沿坐骨神经通路及其分布区的疼痛。", "symptoms": "腰腿痛、下肢放射痛、麻木", "recommended_department": "神经内科", "view_count": 5400},
        {"name": "重症肌无力", "pinyin": "zhongzhengji wuli", "department_id": departments.get("神经内科", 8), "overview": "重症肌无力是神经肌肉接头传递障碍。", "symptoms": "波动性肌无力、晨轻暮重、眼睑下垂", "recommended_department": "神经内科", "view_count": 4200},

        # 骨科更多疾病
        {"name": "腰肌劳损", "pinyin": "yaojilaosun", "department_id": departments.get("骨科", 9), "is_hot": True, "overview": "腰肌劳损是腰部肌肉及其附着点筋膜的慢性损伤。", "symptoms": "腰痛、酸痛、活动后加重", "recommended_department": "骨科", "view_count": 9200},
        {"name": "腰椎管狭窄", "pinyin": "yaozhui guan xiazhai", "department_id": departments.get("骨科", 9), "overview": "腰椎管狭窄是椎管狭窄压迫神经。", "symptoms": "间歇性跛行、下肢放射痛、麻木", "recommended_department": "骨科", "view_count": 7800},
        {"name": "股骨头坏死", "pinyin": "gugutou huaisi", "department_id": departments.get("骨科", 9), "overview": "股骨头坏死是股骨头血液供应中断。", "symptoms": "髋部疼痛、活动受限、跛行", "recommended_department": "骨科", "view_count": 6500},
        {"name": "类风湿关节炎", "pinyin": "leifengxing guan jieyan", "aliases": "类风湿", "department_id": departments.get("骨科", 9), "overview": "类风湿关节炎是自身免疫性关节炎。", "symptoms": "关节肿痛、晨僵、对称性受累", "recommended_department": "骨科", "view_count": 7200},
        {"name": "强直性脊柱炎", "pinyin": "qiangzhixing jizhuyan", "department_id": departments.get("骨科", 9), "overview": "强直性脊柱炎是脊柱关节的慢性炎症。", "symptoms": "腰背痛、脊柱僵硬、活动受限", "recommended_department": "骨科", "view_count": 5200},
        {"name": "痛风性关节炎", "pinyin": "tongfengxing guan jieyan", "department_id": departments.get("骨科", 9), "is_hot": True, "overview": "痛风性关节炎是尿酸盐结晶沉积关节。", "symptoms": "关节红肿热痛、多发于大脚趾", "recommended_department": "骨科", "view_count": 6800},
        {"name": "半月板损伤", "pinyin": "banyeban sunshang", "department_id": departments.get("骨科", 9), "overview": "半月板损伤是膝关节半月板的撕裂。", "symptoms": "膝关节疼痛、弹响、交锁、打软腿", "recommended_department": "骨科", "view_count": 5800},

        # 眼科更多疾病
        {"name": "角膜炎", "pinyin": "jiaomoyan", "department_id": departments.get("眼科", 10), "overview": "角膜炎是角膜的炎症。", "symptoms": "眼痛、畏光、流泪、视力下降", "recommended_department": "眼科", "view_count": 6500},
        {"name": "结膜下出血", "pinyin": "jiemoxia chuxue", "department_id": departments.get("眼科", 10), "overview": "结膜下出血是结膜下血管破裂。", "symptoms": "眼白部分出血、无痛", "recommended_department": "眼科", "view_count": 5800},
        {"name": "睑缘炎", "pinyin": "jianyanyan", "aliases": "烂眼边", "department_id": departments.get("眼科", 10), "overview": "睑缘炎是眼睑边缘的炎症。", "symptoms": "眼睑红肿、痒、脱屑", "recommended_department": "眼科", "view_count": 5200},
        {"name": "麦粒肿", "pinyin": "mailizhong", "aliases": "针眼", "department_id": departments.get("眼科", 10), "is_hot": True, "overview": "麦粒肿是眼睑腺体的急性化脓性炎症。", "symptoms": "眼睑红肿、疼痛、硬结", "recommended_department": "眼科", "view_count": 7200},
        {"name": "散光", "pinyin": "sanguang", "department_id": departments.get("眼科", 10), "overview": "散光是屈光不正的一种。", "symptoms": "视物模糊、重影、眼疲劳", "recommended_department": "眼科", "view_count": 8900},
        {"name": "远视", "pinyin": "yuanshi", "department_id": departments.get("眼科", 10), "overview": "远视是屈光不正的一种。", "symptoms": "近视力下降、眼疲劳", "recommended_department": "眼科", "view_count": 6200},

        # 耳鼻咽喉科更多疾病
        {"name": "鼻窦炎", "pinyin": "bidouyan", "department_id": departments.get("耳鼻咽喉科", 11), "overview": "鼻窦炎是鼻窦粘膜的炎症。", "symptoms": "鼻塞、流脓涕、头痛、嗅觉减退", "recommended_department": "耳鼻咽喉科", "view_count": 6800},
        {"name": "过敏性鼻炎", "pinyin": "guominxing biyan", "department_id": departments.get("耳鼻咽喉科", 11), "is_hot": True, "overview": "过敏性鼻炎是鼻粘膜的过敏反应。", "symptoms": "鼻痒、打喷嚏、流清水样鼻涕", "recommended_department": "耳鼻咽喉科", "view_count": 8900},
        {"name": "鼻中隔偏曲", "pinyin": "bizhongge pianqu", "department_id": departments.get("耳鼻咽喉科", 11), "overview": "鼻中隔偏曲是鼻中隔偏向一侧。", "symptoms": "鼻塞、头痛、鼻出血", "recommended_department": "耳鼻咽喉科", "view_count": 5200},
        {"name": "外耳道炎", "pinyin": "waierdaoyan", "department_id": departments.get("耳鼻咽喉科", 11), "overview": "外耳道炎是外耳道的炎症。", "symptoms": "耳痛、耳鸣、听力下降", "recommended_department": "耳鼻咽喉科", "view_count": 5400},
        {"name": "分泌性中耳炎", "pinyin": "fenmixing zhongeryan", "department_id": departments.get("耳鼻咽喉科", 11), "overview": "分泌性中耳炎是中耳的积液。", "symptoms": "耳闷、听力下降、自听增强", "recommended_department": "耳鼻咽喉科", "view_count": 6200},
        {"name": "声带息肉", "pinyin": "shengdai xirou", "department_id": departments.get("耳鼻咽喉科", 11), "overview": "声带息肉是声带的良性增生。", "symptoms": "声音嘶哑、发声疲劳", "recommended_department": "耳鼻咽喉科", "view_count": 4800},

        # 口腔科更多疾病
        {"name": "牙髓炎", "pinyin": "yasuiyan", "department_id": departments.get("口腔科", 12), "overview": "牙髓炎是牙髓组织的炎症。", "symptoms": "剧烈牙痛、夜间痛、冷热刺激痛", "recommended_department": "口腔科", "view_count": 6200},
        {"name": "根尖周炎", "pinyin": "genjianzhouyan", "department_id": departments.get("口腔科", 12), "overview": "根尖周炎是牙根周围组织的炎症。", "symptoms": "咬合痛、牙龈肿胀、瘘管形成", "recommended_department": "口腔科", "view_count": 5800},
        {"name": "口腔念珠菌感染", "pinyin": "kouqiang nianzhujun", "aliases": "鹅口疮", "department_id": departments.get("口腔科", 12), "overview": "口腔念珠菌是真菌感染。", "symptoms": "口腔白色斑膜、疼痛、吞咽困难", "recommended_department": "口腔科", "view_count": 4200},
        {"name": "复发性口腔溃疡", "pinyin": "fufaxing kouqiang", "aliases": "口疮", "department_id": departments.get("口腔科", 12), "is_hot": True, "overview": "复发性口腔溃疡是常见的口腔粘膜溃疡。", "symptoms": "口腔粘膜溃疡、疼痛、反复发作", "recommended_department": "口腔科", "view_count": 7800},

        # 妇产科更多疾病
        {"name": "宫颈炎", "pinyin": "gongjinyan", "department_id": departments.get("妇产科", 3), "overview": "宫颈炎是宫颈的炎症。", "symptoms": "白带增多、性交后出血", "recommended_department": "妇产科", "view_count": 7200},
        {"name": "附件炎", "pinyin": "fujiaoyan", "department_id": departments.get("妇产科", 3), "overview": "附件炎是输卵管卵巢的炎症。", "symptoms": "下腹痛、发热、白带增多", "recommended_department": "妇产科", "view_count": 6800},
        {"name": "宫颈糜烂", "pinyin": "gongjingmolan", "department_id": departments.get("妇产科", 3), "overview": "宫颈糜烂是宫颈上皮的病理性改变。", "symptoms": "白带增多、接触性出血", "recommended_department": "妇产科", "view_count": 6200},
        {"name": "乳腺增生", "pinyin": "ruxian zengsheng", "department_id": departments.get("妇产科", 3), "is_hot": True, "overview": "乳腺增生是乳腺组织的良性增生。", "symptoms": "乳房胀痛、肿块、周期性疼痛", "recommended_department": "妇产科", "view_count": 8900},
        {"name": "子宫肌瘤", "pinyin": "zigongjiliu", "department_id": departments.get("妇产科", 3), "overview": "子宫肌瘤是子宫平滑肌的良性肿瘤。", "symptoms": "月经量增多、经期延长、腹部包块", "recommended_department": "妇产科", "view_count": 7200},
        {"name": "卵巢囊肿", "pinyin": "luanchao nangzhong", "department_id": departments.get("妇产科", 3), "overview": "卵巢囊肿是卵巢内的液体囊性肿物。", "symptoms": "下腹痛、腹胀、包块", "recommended_department": "妇产科", "view_count": 6500},

        # 儿科更多疾病
        {"name": "新生儿黄疸", "pinyin": "xinshenger huangdan", "department_id": departments.get("儿科", 2), "overview": "新生儿黄疸是新生儿胆红素代谢异常。", "symptoms": "皮肤黄染、嗜睡、食欲不振", "recommended_department": "儿科", "view_count": 7800},
        {"name": "佝偻病", "pinyin": "goulu bing", "department_id": departments.get("儿科", 2), "overview": "佝偻病是维生素D缺乏性钙代谢障碍。", "symptoms": "夜惊、多汗、方颅、鸡胸", "recommended_department": "儿科", "view_count": 5200},
        {"name": "水痘", "pinyin": "shuidou", "department_id": departments.get("儿科", 2), "is_hot": True, "overview": "水痘是由水痘-带状疱疹病毒引起。", "symptoms": "发热、皮疹、水疱、瘙痒", "recommended_department": "儿科", "view_count": 8500},
        {"name": "猩红热", "pinyin": "xinghongre", "department_id": departments.get("儿科", 2), "overview": "猩红热是由A组链球菌引起。", "symptoms": "发热、咽痛、全身充血性皮疹", "recommended_department": "儿科", "view_count": 4800},
        {"name": "腮腺炎", "pinyin": "saixianyan", "aliases": "痄腮", "department_id": departments.get("儿科", 2), "overview": "腮腺炎是由腮腺炎病毒引起。", "symptoms": "腮腺肿大、发热、疼痛", "recommended_department": "儿科", "view_count": 6200},
        {"name": "支气管肺炎", "pinyin": "zhiqig feiyan", "department_id": departments.get("儿科", 2), "overview": "支气管肺炎是支气管和肺的炎症。", "symptoms": "发热、咳嗽、气促、呼吸困难", "recommended_department": "儿科", "view_count": 5600},

        # 皮肤科更多疾病
        {"name": "荨麻疹", "pinyin": "xunmazhen", "department_id": departments.get("皮肤科", 1), "overview": "荨麻疹是常见的过敏性皮肤病。", "symptoms": "风团、剧烈瘙痒、时起时消", "recommended_department": "皮肤科", "view_count": 7200},
        {"name": "接触性皮炎", "pinyin": "jiechuxing pifuyan", "department_id": departments.get("皮肤科", 1), "overview": "接触性皮炎是皮肤接触物质引起的炎症。", "symptoms": "接触部位红肿、水疱、瘙痒", "recommended_department": "皮肤科", "view_count": 6800},
        {"name": "神经性皮炎", "pinyin": "shenjingxing pifuyan", "department_id": departments.get("皮肤科", 1), "is_hot": True, "overview": "神经性皮炎是慢性瘙痒性皮肤病。", "symptoms": "剧烈瘙痒、苔藓样变、肥厚", "recommended_department": "皮肤科", "view_count": 6500},
        {"name": "脂溢性皮炎", "pinyin": "zhiyixing pifuyan", "department_id": departments.get("皮肤科", 1), "overview": "脂溢性皮炎是皮脂溢出引起的炎症。", "symptoms": "头皮油腻、鳞屑、瘙痒", "recommended_department": "皮肤科", "view_count": 7200},
        {"name": "酒渣鼻", "pinyin": "jiuzhabi", "department_id": departments.get("皮肤科", 1), "overview": "酒渣鼻是面部慢性炎症。", "symptoms": "面部潮红、丘疹、毛细血管扩张", "recommended_department": "皮肤科", "view_count": 4800},
        {"name": "体癣", "pinyin": "tixuan", "department_id": departments.get("皮肤科", 1), "overview": "体癣是皮肤真菌感染。", "symptoms": "环形红斑、边缘隆起、瘙痒", "recommended_department": "皮肤科", "view_count": 5400},
        {"name": "头癣", "pinyin": "tou xuan", "department_id": departments.get("皮肤科", 1), "overview": "头癣是头皮真菌感染。", "symptoms": "头皮脱屑、断发、瘙痒", "recommended_department": "皮肤科", "view_count": 4800},
        {"name": "花斑癣", "pinyin": "huabanxuan", "aliases": "汗斑", "department_id": departments.get("皮肤科", 1), "overview": "花斑癣是浅部真菌感染。", "symptoms": "色素减退斑、轻微瘙痒", "recommended_department": "皮肤科", "view_count": 4200},
        {"name": "痤疮", "pinyin": "cuochuang", "aliases": "青春痘", "department_id": departments.get("皮肤科", 1), "overview": "痤疮是毛囊皮脂腺的慢性炎症。", "symptoms": "粉刺、丘疹、脓疱、囊肿", "recommended_department": "皮肤科", "view_count": 9200},
        {"name": "脱发", "pinyin": "tuofa", "department_id": departments.get("皮肤科", 1), "is_hot": True, "overview": "脱发是头发异常脱落。", "symptoms": "头发稀疏、斑秃、全秃", "recommended_department": "皮肤科", "view_count": 7800},
        {"name": "多汗症", "pinyin": "duohanzheng", "department_id": departments.get("皮肤科", 1), "overview": "多汗症是出汗过多的疾病。", "symptoms": "全身或局部出汗过多", "recommended_department": "皮肤科", "view_count": 5500},

        # 传染科相关
        {"name": "流感", "pinyin": "liugan", "aliases": "流行性感冒", "department_id": departments.get("呼吸内科", 5), "is_hot": True, "overview": "流感是由流感病毒引起的急性呼吸道传染病。", "symptoms": "高热、全身酸痛、乏力", "recommended_department": "呼吸内科", "view_count": 9200},
        {"name": "诺如病毒感染", "pinyin": "nuoru bingdu", "department_id": departments.get("消化内科", 4), "is_hot": True, "overview": "诺如病毒是常见的病毒性胃肠炎。", "symptoms": "呕吐、腹泻、发热、腹痛", "recommended_department": "消化内科", "view_count": 7800},
        {"name": "新型冠状病毒感染", "pinyin": "xinguan feiyan", "aliases": "COVID-19", "department_id": departments.get("呼吸内科", 5), "overview": "新型冠状病毒感染是由新型冠状病毒引起的肺炎。", "symptoms": "发热、干咳、乏力、嗅觉丧失", "recommended_department": "呼吸内科", "view_count": 8500},

        # 泌尿科
        {"name": "尿路感染", "pinyin": "niaolu ganran", "department_id": departments.get("泌尿外科", departments.get("肾内科", 8) or 8), "overview": "尿路感染是泌尿系统感染。", "symptoms": "尿频、尿急、尿痛、发热", "recommended_department": "泌尿外科", "view_count": 7200},
        {"name": "肾结石", "pinyin": "shenjieshi", "department_id": departments.get("泌尿外科", departments.get("肾内科", 8) or 8), "is_hot": True, "overview": "肾结石是泌尿系统结石。", "symptoms": "腰痛、血尿、排尿困难", "recommended_department": "泌尿外科", "view_count": 8500},
        {"name": "膀胱炎", "pinyin": "pangguangyan", "department_id": departments.get("泌尿外科", departments.get("肾内科", 8) or 8), "overview": "膀胱炎是膀胱的炎症。", "symptoms": "尿频、尿急、尿痛、血尿", "recommended_department": "泌尿外科", "view_count": 6200},
    ]

    added_count = 0
    for data in extended_diseases:
        # 检查是否已存在
        existing = db.query(Disease).filter(Disease.name == data["name"]).first()
        if not existing:
            disease = Disease(**data)
            db.add(disease)
            added_count += 1

    db.commit()
    print(f"新增疾病 {added_count} 条")


def seed_extended_drugs(db: Session):
    """扩展药品数据"""
    print("开始扩展药品数据...")

    # 获取热门分类
    hot_category = db.query(DrugCategory).filter(DrugCategory.name == "热门药品").first()
    cold_category = db.query(DrugCategory).filter(DrugCategory.name == "感冒发烧").first()
    digestive_category = db.query(DrugCategory).filter(DrugCategory.name == "消化系统").first()
    skin_category = db.query(DrugCategory).filter(DrugCategory.name == "皮肤用药").first()
    cardio_category = db.query(DrugCategory).filter(DrugCategory.name == "心脑血管").first()

    extended_drugs = [
        # 感冒发烧类
        {"name": "连花清瘟胶囊", "pinyin": "lianhuaqingwen jiaonang", "common_brands": "以岭", "indications": "用于治疗流行性感冒、热毒袭肺证。", "contraindications": "运动员慎用；过敏体质者慎用。", "dosage": "口服，一次4粒，一日3次。", "side_effects": "胃肠道不适", "precautions": "忌烟酒及辛辣油腻食物。", "storage": "密封保存。", "is_hot": True, "categories": [hot_category, cold_category]},
        {"name": "板蓝根颗粒", "pinyin": "banlangen keli", "common_brands": "同仁堂", "indications": "用于清热解毒、凉血利咽。", "contraindications": "孕妇慎用；体质虚寒者慎用。", "dosage": "口服，一次1袋，一日3次。", "side_effects": "偶见恶心、呕吐", "precautions": "不宜长期服用。", "storage": "密封保存。", "categories": [cold_category]},
        {"name": "双黄连口服液", "pinyin": "shuanghuanglian koufuye", "common_brands": "同仁堂", "indications": "用于清热解毒。", "contraindications": "孕妇慎用；脾胃虚寒者慎用。", "dosage": "口服，一次20ml，一日3次。", "side_effects": "胃肠道反应", "precautions": "忌辛辣油腻食物。", "storage": "密封保存。", "categories": [cold_category]},

        # 消化系统类
        {"name": "多潘立酮", "pinyin": "duopanlitong", "common_brands": "吗丁啉", "indications": "用于消化不良、腹胀、嗳气。", "contraindications": "机械性肠梗阻禁用；嗜铬细胞瘤禁用。", "dosage": "口服，一次10mg，一日3次。", "side_effects": "偶见头痛、头晕", "precautions "孕妇慎用；哺乳期妇女使用时应停止哺乳。", "storage": "密封保存。", "categories": [hot_category, digestive_category]},
        {"name": "铝碳酸镁", "pinyin": "lv tansuanmei", "common_brands": "达喜", "indications": "用于胃酸过多、反酸、烧心。", "contraindications": "肾功能不全者禁用。", "dosage": "口服，一次1g，一日4次。", "side_effects "便秘", "precautions "长期使用需定期检查血铝。", "storage": "密封保存。", "categories": [digestive_category, hot_category]},
        {"name": "果胶铋", "pinyin": "guaojiao bi", "common_brands": "舒克斐", "indications": "用于保护胃粘膜。", "contraindications": "对本品过敏者禁用。", "dosage": "口服，一次1g，一日3次。", "side_effects": "偶见便秘", "precautions": "本品不影响其他药物吸收。", "storage": "密封保存。", "categories": [digestive_category, hot_category]},

        # 心脑血管类
        {"name": "氨氯地平", "pinyin": "anludiping", "common_brands": "络活喜", "indications": "用于高血压、心绞痛。", "contraindications": "严重低血压禁用；对二氢吡啶类过敏者禁用。", "dosage": "口服，一次5mg，一日1次。", "side_effects "头痛、面部潮红、水肿", "precautions "肝功能不全者慎用；避免与葡萄柚汁同服。", "storage": "遮光保存。", "categories": [cardio_category, hot_category]},
        {"name": "阿托伐他汀", "pinyin": "atuofatating", "common_brands": "立普妥", "indications": "用于高胆固醇血症。", "contraindications": "活动性肝病患者禁用。", "dosage": "口服，一次10mg，一日1次。", "side_effects "肝功能异常、肌肉疼痛", "precautions "定期检查肝功能；避免与葡萄柚汁同服。", "storage": "密封保存。", "categories": [cardio_category]},
        {"name": "硫酸氢氯吡格雷", "pinyin": "liusuanqinglubigelei", "common_brands": "波立维", "indications": "用于预防心脑血管血栓。", "contraindications "活动性出血者禁用。", "dosage": "口服，一次75mg，一日1次。", "side_effects "出血、淤斑", "precautions "手术前7天需停用；注意出血倾向。", "storage": "密封保存。", "categories": [cardio_category, hot_category]},

        # 抗生素类
        {"name": "头孢拉定", "pinyin": "toubaolading", "common_brands": "先锋霉素6号", "indications": "用于敏感菌所致的各种感染。", "contraindications": "对头孢类抗生素过敏者禁用。", "dosage": "口服，一次0.5g，一日4次。", "side_effects": "胃肠道反应、过敏", "precautions": "青霉素过敏者慎用；饮酒后禁用。", "storage": "密封保存。", "categories": [hot_category]},
        {"name": "左氧氟沙星", "pinyin": "zuoyangfushaxing", "common_brands": "可乐必妥", "indications": "用于敏感菌引起的各种感染。", "contraindications "对喹诺酮类过敏者禁用；18岁以下禁用。", "dosage": "口服，一次0.2g，一日2次。", "side_effects": "胃肠道反应、中枢神经系统反应", "precautions "避免阳光直射；注意肌腱炎风险。", "storage": "遮光保存。", "categories": [hot_category]},

        # 皮肤用药类
        {"name": "特非那定", "pinyin": "tefeinading", "common_brands": "扑尔敏", "indications": "用于皮肤过敏。", "contraindications": "对本品过敏者禁用。", "dosage": "口服，一次4mg，一日3次。", "side_effects": "嗜睡、口干", "precautions "服药期间避免驾驶；饮酒后禁用。", "storage": "密封保存。 "categories": [hot_category]},
        {"name": "氯雷他定", "pinyin": "lufeitading", "common_brands": "开瑞坦", "indications": "用于过敏性鼻炎、荨麻疹。", "contraindications": "对本品过敏者禁用。", "dosage": "口服，一次10mg，一日1次。", "side_effects "头痛、嗜睡", "precautions "部分人可能仍有嗜睡，驾驶时需注意。", "storage": "密封保存。 "categories": [hot_category, skin_category]},
        {"name": "地奈德", "pinyin": "dinaide", "common_brands": "皮炎平", "indications": "用于湿疹、皮炎、皮肤瘙痒症。", "contraindications": "对本品过敏者禁用。", "dosage": "外用，一日2-3次。", "side_effects "局部刺激", "precautions "避免接触眼睛；不建议大面积使用。", "storage": "密封保存。", "categories": [skin_category]},

        # 镇痛药类
        {"name": "双氯芬酸钠", "pinyin": "shuanglvfensuanna", "common_brands": "扶他林", "indications": "用于缓解疼痛和炎症。", "contraindications": "活动性消化道溃疡者禁用。", "dosage": "口服，一次25mg，一日3次。", "side_effects "胃肠道反应", "precautions "餐后服用；有胃病史者慎用。", "storage": "密封保存。", "categories": [hot_category]},
        {"name": "塞来昔布", "pinyin": "selaixibu", "common_brands": "西乐葆", "indications": "用于缓解骨关节炎疼痛。", "contraindications": "对磺胺过敏者禁用。", "dosage": "口服，一次100mg，一日2次。", "side_effects "胃肠道反应、心血管风险", "precautions "有心血管病史者慎用；最低有效剂量。", "storage": "密封保存。", "categories": [hot_category]},
        {"name": "洛索洛芬", "pinyin": "luosuoluofen", "common_brands": "乐松", "indications": "用于疼痛和炎症。", "contraindications "活动性消化道溃疡者禁用。", "dosage": "口服，一次60mg, 一日3次。", "side_effects "胃肠道反应", "precautions "餐后服用；有哮喘史者慎用。", "storage": "密封保存。", "categories": [hot_category]},

        # 维生素类
        {"name": "维生素C片", "pinyin": "weishengsu C pian", "common_brands": "力度伸", "indications": "用于维生素C缺乏症。", "contraindications": "对本品过敏者禁用。", "dosage": "口服，一次0.1g，一日3次。", "side_effects "长期大量使用可致腹泻", "precautions "不宜长期大量服用。", "storage": "密封保存。", "categories": [hot_category]},
        {"name": "维生素D滴剂", "pinyin": "weishengsu D diji", "common_brinds": "星鲨", "indications": "用于预防和治疗维生素D缺乏症。", "contraindications": "高钙血症禁用。", "dosage": "口服，一次1粒，一日1-2次。", "side_effects "过量使用可中毒", "precautions "按推荐剂量服用。", "storage": "密封保存。", "categories": [hot_category]},
        {"name": "复合维生素B", "pinyin": "fuhe weishengsu B", "common_brands": "金维他", "indications": "用于维生素B族缺乏症。", "contraindications": "对本品任何成分过敏者禁用。", "dosage": "口服，一次1片，一日1次。", "side_effects "罕见过敏反应", "precautions "尿液可能变黄。", "storage": "密封保存。", "categories": [hot_category]},

        # 中成药
        {"name": "六味地黄丸", "pinyin": "liuwei dihuang wan", "indications": "用于肾阴亏损。", "contraindications": "感冒发热患者不宜服用。", "dosage": "口服，一次8丸，一日3次。", "side_effects "罕见胃肠道不适", "precautions "忌辛辣食物。", "storage": "密封保存。", "categories": [hot_category]},
        {"name": "逍遥丸", "pinyin": "xiaoyao wan", "indications": "用于肝郁脾虚。", "contraindications": "孕妇慎用；感冒时暂停服用。", "dosage": "口服，一次8丸，一日3次。", "side_effects "罕见胃肠道反应", "precautions "忌食生冷。", "storage": "密封保存。", "categories": [hot_category]},
        {"name": "复方丹参滴丸", "pinyin": "fufang dansen diwan", "common_brands": "天士力", "indications": "用于气滞血瘀。", "contraindications "孕妇慎用。", "dosage": "口服，一次10丸，一日3次。", "side_effects "胃肠道不适", "precautions "寒凝血瘀者慎用。", "storage": "密封保存。", "categories": [cardio_category, hot_category]},
        {"name": "安宫牛黄丸", "pinyin": "angong niuhuang wan", "indications": "用于热病神昏。", "contraindications "孕妇禁用。", "dosage": "口服，一次1丸，一日1次。", "side_effects "罕见", "precautions "本品含剧毒药，按说明书服用。", "storage": "密封保存。", "categories": [hot_category]},

        # 其他常用药
        {"name": "蒙脱石散", "pinyin": "mengtuoshisan", "common_brands": "思密达", "indications": "用于成人及儿童急慢性腹泻。", "contraindications "对本品过敏者禁用。", "dosage": "成人：一次1袋，一日3次。", "side_effects "偶见便秘", "precautions "空腹服用效果更佳。", "storage": "密封保存。", "categories": [hot_category, digestive_category]},
        {"name": "开塞露", "pinyin": "kaisailu", "indications": "用于便秘。", "contraindications "对本品过敏者禁用。", "dosage": "肛内注入，成人一次20ml。", "side_effects "偶见腹部不适", "precautions "不宜长期使用。", "storage": "密封保存。", "categories": [hot_category]},
        {"name": "碘伏", "pinyin": "dianfu", "indications": "用于皮肤、黏膜消毒。", "contraindications "对本品过敏者禁用。", "dosage": "外用，涂擦患处。", "side_effects "偶见过敏反应", "precautions "不可内服；避免接触眼睛。", "storage": "密封保存。", "categories": [hot_category]},
        {"name": "医用酒精", "pinyin": "yiyong jiujing", "indications": "用于皮肤消毒。", "contraindications ": ", "dosage": "外用，涂抹患处。", "side_effects ": "偶见过敏", "precautions ": "易燃，远离火源。", "storage ": "阴凉处保存。", "categories": [hot_category]},
    ]

    added_count = 0
    for data in extended_drugs:
        # 检查是否已存在
        existing = db.query(Drug).filter(Drug.name == data["name"]).first()
        if not existing:
            drug = Drug(**data)
            db.add(drug)
            added_count += 1

    db.commit()
    print(f"新增药品 {added_count} 条")


def main():
    db = SessionLocal()
    try:
        print("=== 医疗数据扩展种子脚本 ===\n")
        seed_extended_diseases(db)
        seed_extended_drugs(db)

        # 显示最终统计
        disease_count = db.query(Disease).count()
        drug_count = db.query(Drug).count()
        print(f"\n=== 扩展后数据量 ===")
        print(f"疾病: {disease_count} 条")
        print(f"药品: {drug_count} 条")

        if disease_count >= 1000:
            print("\n✅ 疾病数据达标 (≥1000条)")
        else:
            print(f"\n⚠️  疾病数据仍需添加 {1000 - disease_count} 条")

        if drug_count >= 500:
            print("✅ 药品数据达标 (≥500条)")
        else:
            print(f"⚠️  药品数据仍需添加 {500 - drug_count} 条")

    finally:
        db.close()


if __name__ == "__main__":
    main()
