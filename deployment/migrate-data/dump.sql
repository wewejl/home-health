-- PostgreSQL 数据库转储文件
-- 源数据库: SQLite (/Users/zhuxinye/Desktop/project/home-health/backend/app.db)
-- 导出时间: 2026-01-23 02:33:07
--
-- 使用方法:
--   psql -h 123.206.232.231 -U xinlin_prod -d xinlin_prod < dump.sql
--

-- 开始数据迁移
BEGIN;

-- Table: admin_users
DROP TABLE IF EXISTS admin_users CASCADE;
CREATE TABLE admin_users (
    id INTEGER NOT NULL,
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT,
    role TEXT,
    permissions TEXT,
    is_active BOOLEAN,
    last_login_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Data for table: admin_users
INSERT INTO admin_users (id, username, password_hash, email, role, permissions, is_active, last_login_at, created_at) VALUES
(1, 'admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin@xinlin.com', 'admin', NULL, TRUE, NULL, '2026-01-09 06:28:55');

-- Table: audit_logs
DROP TABLE IF EXISTS audit_logs CASCADE;
CREATE TABLE audit_logs (
    id INTEGER NOT NULL,
    admin_user_id INTEGER,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    changes TEXT,
    ip_address TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Table audit_logs: 无数据

-- Table: departments
DROP TABLE IF EXISTS departments CASCADE;
CREATE TABLE departments (
    id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    sort_order INTEGER,
    PRIMARY KEY (id)
);

-- Data for table: departments
INSERT INTO departments (id, name, description, icon, sort_order) VALUES
(1, '皮肤科', '皮肤病、过敏、湿疹、痤疮', 'hand.raised', 1),
(2, '儿科', '儿童疾病、生长发育、疫苗咨询', 'figure.child', 2),
(3, '妇产科', '妇科疾病、孕期保健、产后康复', 'figure.dress.line.vertical.figure', 3),
(4, '消化内科', '胃病、肠炎、肝胆疾病', 'stomach', 4),
(5, '呼吸内科', '感冒、咳嗽、哮喘、肺炎', 'lungs', 5),
(6, '心血管内科', '高血压、冠心病、心律失常', 'heart', 6),
(7, '内分泌科', '糖尿病、甲状腺疾病、肥胖', 'drop', 7),
(8, '神经内科', '头痛、失眠、中风、癫痫', 'brain.head.profile', 8),
(9, '骨科', '骨折、关节炎、颈椎病、腰椎病', 'figure.walk', 9),
(10, '眼科', '近视、白内障、青光眼、眼部炎症', 'eye', 10),
(11, '耳鼻咽喉科', '中耳炎、鼻炎、咽喉炎', 'ear', 11),
(12, '口腔科', '牙痛、龋齿、牙周病、口腔溃疡', 'mouth', 12);

-- Table: derma_sessions
DROP TABLE IF EXISTS derma_sessions CASCADE;
CREATE TABLE derma_sessions (
    id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    stage TEXT,
    progress INTEGER,
    questions_asked INTEGER,
    chief_complaint TEXT,
    symptoms TEXT,
    symptom_details TEXT,
    skin_location TEXT,
    duration TEXT,
    messages TEXT,
    current_response TEXT,
    quick_options TEXT,
    skin_analyses TEXT,
    latest_analysis TEXT,
    report_interpretations TEXT,
    latest_interpretation TEXT,
    possible_conditions TEXT,
    risk_level TEXT,
    care_advice TEXT,
    need_offline_visit BOOLEAN,
    current_task TEXT,
    awaiting_image BOOLEAN,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Table derma_sessions: 无数据

-- Table: diagnosis_sessions
DROP TABLE IF EXISTS diagnosis_sessions CASCADE;
CREATE TABLE diagnosis_sessions (
    id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    stage TEXT,
    progress INTEGER,
    questions_asked INTEGER,
    chief_complaint TEXT,
    symptoms TEXT,
    symptom_details TEXT,
    messages TEXT,
    current_question TEXT,
    quick_options TEXT,
    reasoning TEXT,
    possible_diseases TEXT,
    risk_level TEXT,
    recommendations TEXT,
    can_conclude BOOLEAN,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Table diagnosis_sessions: 无数据

-- Table: diseases
DROP TABLE IF EXISTS diseases CASCADE;
CREATE TABLE diseases (
    id INTEGER,
    name TEXT NOT NULL,
    pinyin TEXT,
    pinyin_abbr TEXT,
    department_id INTEGER NOT NULL,
    recommended_department TEXT,
    overview TEXT,
    symptoms TEXT,
    causes TEXT,
    diagnosis TEXT,
    treatment TEXT,
    prevention TEXT,
    care TEXT,
    author_name TEXT,
    author_title TEXT,
    author_avatar TEXT,
    reviewer_info TEXT,
    is_hot BOOLEAN,
    sort_order INTEGER,
    is_active BOOLEAN,
    view_count INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Data for table: diseases
INSERT INTO diseases (id, name, pinyin, pinyin_abbr, department_id, recommended_department, overview, symptoms, causes, diagnosis, treatment, prevention, care, author_name, author_title, author_avatar, reviewer_info, is_hot, sort_order, is_active, view_count, created_at, updated_at) VALUES
(1, '湿疹', 'shizhen', 'sz', 1, '皮肤科', '湿疹是一种常见的过敏性皮肤病，表现为皮肤红斑、丘疹、水疱等。', '皮肤瘙痒、红肿、起水疱、渗液、结痂', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 1, TRUE, 8520, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(2, '痤疮', 'cuochuang', 'cc', 1, '皮肤科', '痤疮是毛囊皮脂腺的慢性炎症性疾病，多见于青少年。', '面部粉刺、丘疹、脓疱、结节、囊肿', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 2, TRUE, 7890, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(3, '荨麻疹', 'xunmazhen', 'xmz', 1, '皮肤科', '荨麻疹是一种常见的过敏性皮肤病，表现为风团和瘙痒。', '皮肤出现红色风团、剧烈瘙痒、时起时消', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 3, TRUE, 6420, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(4, '银屑病', 'yinxiebing', 'yxb', 1, '皮肤科', '银屑病是一种慢性炎症性皮肤病，表现为红斑和银白色鳞屑。', '皮肤红斑、银白色鳞屑、瘙痒、关节疼痛', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 4, TRUE, 4230, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(5, '白癜风', 'baidiānfeng', 'bdf', 1, '皮肤科', '白癜风是一种色素脱失性皮肤病，表现为皮肤白斑。', '皮肤出现白色斑块、边界清楚、无痛无痒', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 5, TRUE, 3850, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(6, '小儿感冒', 'xiaoerganmao', 'xegm', 2, '儿科', '小儿感冒是儿童最常见的疾病，多由病毒感染引起。', '发热、咳嗽、流鼻涕、打喷嚏、咽痛', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 1, TRUE, 9520, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(7, '小儿腹泻', 'xiaoerfuxie', 'xefx', 2, '儿科', '小儿腹泻是儿童常见的消化系统疾病。', '大便次数增多、稀便、水样便、腹痛、发热', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 2, TRUE, 8340, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(8, '手足口病', 'shouzukoubing', 'szkb', 2, '儿科', '手足口病是由肠道病毒引起的传染病，多发于5岁以下儿童。', '手、足、口腔出现疱疹、发热、食欲不振', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 3, TRUE, 7120, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(9, '小儿肺炎', 'xiaoerfeiyan', 'xefy', 2, '儿科', '小儿肺炎是儿童常见的呼吸系统疾病。', '发热、咳嗽、气促、呼吸困难', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 4, TRUE, 5890, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(10, '小儿哮喘', 'xiaoerxiaochuan', 'xexc', 2, '儿科', '小儿哮喘是儿童常见的慢性呼吸道疾病。', '反复喘息、咳嗽、胸闷、呼吸困难', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 5, TRUE, 4670, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(11, '阴道炎', 'yindaoyan', 'ydy', 3, '妇产科', '阴道炎是女性常见的妇科炎症。', '阴道分泌物增多、外阴瘙痒、异味、灼热感', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 1, TRUE, 8920, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(12, '月经不调', 'yuejingbutiao', 'yjbt', 3, '妇产科', '月经不调是指月经周期、经期或经量异常。', '月经周期不规律、经量过多或过少、痛经', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 2, TRUE, 7650, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(13, '子宫肌瘤', 'zigongjiliu', 'zgjl', 3, '妇产科', '子宫肌瘤是女性生殖器官最常见的良性肿瘤。', '月经量增多、经期延长、腹部包块、压迫症状', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 3, TRUE, 6430, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(14, '盆腔炎', 'penqiangyan', 'pqy', 3, '妇产科', '盆腔炎是女性上生殖道的感染性疾病。', '下腹痛、发热、阴道分泌物增多', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 4, TRUE, 5120, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(15, '多囊卵巢综合征', 'duonangluanchao', 'dnlc', 3, '妇产科', '多囊卵巢综合征是育龄女性常见的内分泌代谢疾病。', '月经稀发、多毛、痤疮、肥胖、不孕', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 5, TRUE, 4890, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(16, '胃炎', 'weiyan', 'wy', 4, '消化内科', '胃炎是胃粘膜的炎症性疾病。', '上腹痛、恶心、呕吐、食欲不振、腹胀', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 1, TRUE, 9230, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(17, '胃溃疡', 'weikuiyang', 'wky', 4, '消化内科', '胃溃疡是消化性溃疡的一种。', '上腹痛、餐后痛、反酸、嗳气、黑便', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 2, TRUE, 7840, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(18, '肠炎', 'changyan', 'cy', 4, '消化内科', '肠炎是肠道的炎症性疾病。', '腹泻、腹痛、恶心、呕吐、发热', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 3, TRUE, 6920, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(19, '脂肪肝', 'zhifanggan', 'zfg', 4, '消化内科', '脂肪肝是肝细胞内脂肪堆积过多的病变。', '多数无症状、可有乏力、肝区不适', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 4, TRUE, 5340, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(20, '胆囊炎', 'dannangyan', 'dny', 4, '消化内科', '胆囊炎是胆囊的炎症性疾病。', '右上腹痛、发热、恶心、呕吐', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 5, TRUE, 4670, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(21, '感冒', 'ganmao', 'gm', 5, '呼吸内科', '感冒是最常见的急性呼吸道感染性疾病。', '鼻塞、流涕、打喷嚏、咽痛、咳嗽、发热', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 1, TRUE, 10520, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(22, '支气管炎', 'zhiqiguanyan', 'zqgy', 5, '呼吸内科', '支气管炎是支气管粘膜的炎症。', '咳嗽、咳痰、气促、胸闷', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 2, TRUE, 8340, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(23, '肺炎', 'feiyan', 'fy', 5, '呼吸内科', '肺炎是肺部的感染性疾病。', '发热、咳嗽、咳痰、胸痛、呼吸困难', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 3, TRUE, 7650, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(24, '哮喘', 'xiaochuan', 'xc', 5, '呼吸内科', '哮喘是慢性气道炎症性疾病。', '反复喘息、气促、胸闷、咳嗽', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 4, TRUE, 6120, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(25, '慢性阻塞性肺疾病', 'manxingzusaixing', 'mxzsx', 5, '呼吸内科', '慢阻肺是一种常见的慢性呼吸系统疾病。', '慢性咳嗽、咳痰、气促、呼吸困难', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 5, TRUE, 4890, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(26, '高血压', 'gaoxueya', 'gxy', 6, '心血管内科', '高血压是最常见的慢性病之一。', '头痛、头晕、心悸、胸闷、乏力', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 1, TRUE, 11230, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(27, '冠心病', 'guanxinbing', 'gxb', 6, '心血管内科', '冠心病是冠状动脉粥样硬化性心脏病。', '胸痛、胸闷、心悸、气短', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 2, TRUE, 8920, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(28, '心律失常', 'xinlvshichang', 'xlsc', 6, '心血管内科', '心律失常是心脏节律异常的统称。', '心悸、胸闷、头晕、乏力、晕厥', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 3, TRUE, 7340, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(29, '心力衰竭', 'xinlishuaijie', 'xlsj', 6, '心血管内科', '心力衰竭是各种心脏疾病的终末阶段。', '呼吸困难、乏力、水肿、咳嗽', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 4, TRUE, 5670, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(30, '心肌炎', 'xinjiyan', 'xjy', 6, '心血管内科', '心肌炎是心肌的炎症性疾病。', '胸痛、心悸、乏力、气促、发热', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 5, TRUE, 4230, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(31, '糖尿病', 'tangniaobing', 'tnb', 7, '内分泌科', '糖尿病是一组以高血糖为特征的代谢性疾病。', '多饮、多尿、多食、体重下降、乏力', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 1, TRUE, 10890, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(32, '甲状腺功能亢进症', 'jiazhuangxian', 'jzx', 7, '内分泌科', '甲亢是甲状腺激素分泌过多引起的疾病。', '心悸、多汗、怕热、消瘦、手抖、突眼', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 2, TRUE, 8120, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(33, '甲状腺功能减退症', 'jiazhuangxian', 'jzx', 7, '内分泌科', '甲减是甲状腺激素分泌不足引起的疾病。', '乏力、怕冷、便秘、体重增加、记忆力减退', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 3, TRUE, 6890, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(34, '骨质疏松症', 'guzhisusong', 'gzss', 7, '内分泌科', '骨质疏松症是以骨量减少为特征的代谢性骨病。', '腰背疼痛、身高变矮、驼背、易骨折', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 4, TRUE, 5340, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(35, '痛风', 'tongfeng', 'tf', 7, '内分泌科', '痛风是嘌呤代谢紊乱引起的疾病。', '关节红肿热痛、多发于大脚趾、夜间发作', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 5, TRUE, 4670, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(36, '头痛', 'toutong', 'tt', 8, '神经内科', '头痛是神经内科最常见的症状之一。', '头部疼痛、可伴恶心、呕吐、畏光', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 1, TRUE, 9670, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(37, '失眠症', 'shimianzheng', 'smz', 8, '神经内科', '失眠症是常见的睡眠障碍。', '入睡困难、睡眠浅、早醒、多梦', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 2, TRUE, 8340, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(38, '脑梗死', 'naogengsi', 'ngs', 8, '神经内科', '脑梗死是脑血管病最常见的类型。', '突发肢体无力、言语不清、面瘫、头晕', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 3, TRUE, 7120, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(39, '癫痫', 'dianxian', 'dx', 8, '神经内科', '癫痫是大脑神经元异常放电引起的疾病。', '突然意识丧失、抽搐、口吐白沫', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 4, TRUE, 5890, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(40, '帕金森病', 'pajinsenbing', 'pjsb', 8, '神经内科', '帕金森病是常见的神经退行性疾病。', '静止性震颤、肌强直、运动迟缓、姿势步态异常', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 5, TRUE, 4230, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(41, '颈椎病', 'jingzhuibing', 'jzb', 9, '骨科', '颈椎病是颈椎退行性改变引起的疾病。', '颈肩痛、上肢麻木、头晕、头痛', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 1, TRUE, 9890, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(42, '腰椎间盘突出症', 'yaozhuijianpan', 'yzjp', 9, '骨科', '腰椎间盘突出症是常见的脊柱疾病。', '腰痛、下肢放射痛、麻木、肌力减退', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 2, TRUE, 8670, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(43, '骨关节炎', 'guguanjieyan', 'ggjy', 9, '骨科', '骨关节炎是关节软骨退行性改变。', '关节疼痛、僵硬、活动受限、肿胀', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 3, TRUE, 7340, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(44, '骨折', 'guzhe', 'gz', 9, '骨科', '骨折是骨的完整性或连续性中断。', '局部疼痛、肿胀、畸形、功能障碍', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 4, TRUE, 6120, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(45, '肩周炎', 'jianzhouyan', 'jzy', 9, '骨科', '肩周炎是肩关节周围软组织的慢性炎症。', '肩部疼痛、活动受限、夜间痛', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 5, TRUE, 5230, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(46, '近视', 'jinshi', 'js', 10, '眼科', '近视是最常见的屈光不正。', '远视力下降、视物模糊、眼疲劳', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 1, TRUE, 10230, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(47, '白内障', 'bainezhang', 'bnz', 10, '眼科', '白内障是晶状体混浊引起的视力障碍。', '视力下降、视物模糊、畏光、眩光', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 2, TRUE, 8120, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(48, '青光眼', 'qingguangyan', 'qgy', 10, '眼科', '青光眼是以视神经损害为特征的眼病。', '眼痛、视力下降、视野缺损、虹视', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 3, TRUE, 6890, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(49, '干眼症', 'ganyanzheng', 'gyz', 10, '眼科', '干眼症是泪液分泌或质量异常引起的眼表疾病。', '眼干、眼涩、异物感、烧灼感、视疲劳', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 4, TRUE, 5670, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(50, '结膜炎', 'jiemoyan', 'jmy', 10, '眼科', '结膜炎是结膜的炎症性疾病。', '眼红、眼痒、分泌物增多、异物感', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 5, TRUE, 4890, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(51, '鼻炎', 'biyan', 'by', 11, '耳鼻咽喉科', '鼻炎是鼻腔粘膜的炎症性疾病。', '鼻塞、流涕、打喷嚏、鼻痒', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 1, TRUE, 9340, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(52, '咽喉炎', 'yanhouyan', 'yhy', 11, '耳鼻咽喉科', '咽喉炎是咽喉部粘膜的炎症。', '咽痛、咽干、咽部异物感、声音嘶哑', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 2, TRUE, 8120, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(53, '中耳炎', 'zhongeryan', 'zey', 11, '耳鼻咽喉科', '中耳炎是中耳的炎症性疾病。', '耳痛、耳鸣、听力下降、耳流脓', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 3, TRUE, 6780, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(54, '鼻窦炎', 'bidouyan', 'bdy', 11, '耳鼻咽喉科', '鼻窦炎是鼻窦粘膜的炎症。', '鼻塞、流脓涕、头痛、嗅觉减退', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 4, TRUE, 5450, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(55, '扁桃体炎', 'biantaotiyan', 'btty', 11, '耳鼻咽喉科', '扁桃体炎是扁桃体的炎症性疾病。', '咽痛、发热、吞咽困难、扁桃体肿大', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 5, TRUE, 4670, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(56, '龋齿', 'quchi', 'qc', 12, '口腔科', '龋齿是牙齿硬组织的细菌性疾病。', '牙痛、牙齿敏感、牙洞、食物嵌塞', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 1, TRUE, 9120, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(57, '牙周炎', 'yazhouyan', 'yzy', 12, '口腔科', '牙周炎是牙周组织的慢性炎症。', '牙龈出血、牙龈肿胀、牙齿松动、口臭', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 2, TRUE, 7890, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(58, '口腔溃疡', 'kouqiangkuiyang', 'kqky', 12, '口腔科', '口腔溃疡是口腔粘膜的溃疡性损害。', '口腔粘膜溃疡、疼痛、进食困难', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, TRUE, 3, TRUE, 6670, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(59, '智齿冠周炎', 'zhichiguanzhouyan', 'zcgzy', 12, '口腔科', '智齿冠周炎是智齿周围软组织的炎症。', '智齿区疼痛、肿胀、张口困难、发热', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 4, TRUE, 5340, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(60, '牙髓炎', 'yasuiyan', 'ysy', 12, '口腔科', '牙髓炎是牙髓组织的炎症。', '剧烈牙痛、夜间痛、冷热刺激痛', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, FALSE, 5, TRUE, 4560, '2026-01-09 06:28:16', '2026-01-09 06:28:16');

-- Table: doctors
DROP TABLE IF EXISTS doctors CASCADE;
CREATE TABLE doctors (
    id INTEGER NOT NULL,
    name TEXT NOT NULL,
    title TEXT,
    department_id INTEGER NOT NULL,
    hospital TEXT,
    specialty TEXT,
    intro TEXT,
    avatar_url TEXT,
    rating REAL,
    monthly_answers INTEGER,
    avg_response_time TEXT,
    can_prescribe BOOLEAN,
    is_top_hospital BOOLEAN,
    is_ai BOOLEAN,
    ai_persona_prompt TEXT,
    ai_model TEXT,
    ai_temperature REAL,
    ai_max_tokens INTEGER,
    knowledge_base_id TEXT,
    agent_type TEXT,
    agent_config TEXT,
    is_active BOOLEAN,
    verified_by INTEGER,
    verified_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Data for table: doctors
INSERT INTO doctors (id, name, title, department_id, hospital, specialty, intro, avatar_url, rating, monthly_answers, avg_response_time, can_prescribe, is_top_hospital, is_ai, ai_persona_prompt, ai_model, ai_temperature, ai_max_tokens, knowledge_base_id, agent_type, agent_config, is_active, verified_by, verified_at, created_at, updated_at) VALUES
(1, '刘武', '副主任医师', 1, '浙江大学医学院附属第一医院', '湿疹、痤疮、皮肤过敏、荨麻疹', NULL, NULL, 5.0, 617, '8分钟', TRUE, TRUE, TRUE, NULL, 'qwen-plus', 0.7, 500, NULL, 'simple', NULL, TRUE, NULL, NULL, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(2, '李明', '主任医师', 2, '北京儿童医院', '小儿感冒、发热、腹泻、生长发育', NULL, NULL, 5.0, 892, '10分钟', TRUE, TRUE, TRUE, NULL, 'qwen-plus', 0.7, 500, NULL, 'simple', NULL, TRUE, NULL, NULL, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(3, '张丽', '主任医师', 3, '北京协和医院', '妇科炎症、月经不调、不孕不育', NULL, NULL, 5.0, 723, '6分钟', TRUE, TRUE, TRUE, NULL, 'qwen-plus', 0.7, 500, NULL, 'simple', NULL, TRUE, NULL, NULL, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(4, '赵强', '主任医师', 4, '北京大学第一医院', '胃炎、胃溃疡、肠炎、肝病', NULL, NULL, 5.0, 634, '5分钟', TRUE, TRUE, TRUE, NULL, 'qwen-plus', 0.7, 500, NULL, 'simple', NULL, TRUE, NULL, NULL, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(5, '孙伟', '副主任医师', 5, '中日友好医院', '感冒、咳嗽、支气管炎、肺炎', NULL, NULL, 4.9, 521, '6分钟', TRUE, TRUE, TRUE, NULL, 'qwen-plus', 0.7, 500, NULL, 'simple', NULL, TRUE, NULL, NULL, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(6, '周华', '主任医师', 6, '北京阜外医院', '高血压、冠心病、心律失常、心衰', NULL, NULL, 5.0, 412, '8分钟', TRUE, TRUE, TRUE, NULL, 'qwen-plus', 0.7, 500, NULL, 'simple', NULL, TRUE, NULL, NULL, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(7, '吴敏', '副主任医师', 7, '北京协和医院', '糖尿病、甲亢、甲减、骨质疏松', NULL, NULL, 4.9, 378, '7分钟', TRUE, TRUE, TRUE, NULL, 'qwen-plus', 0.7, 500, NULL, 'simple', NULL, TRUE, NULL, NULL, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(8, '郑刚', '主任医师', 8, '首都医科大学宣武医院', '头痛、失眠、中风、帕金森病', NULL, NULL, 5.0, 289, '10分钟', TRUE, TRUE, TRUE, NULL, 'qwen-plus', 0.7, 500, NULL, 'simple', NULL, TRUE, NULL, NULL, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(9, '钱进', '副主任医师', 9, '北京积水潭医院', '骨折、关节炎、颈椎病、腰椎病', NULL, NULL, 4.9, 445, '6分钟', TRUE, TRUE, TRUE, NULL, 'qwen-plus', 0.7, 500, NULL, 'simple', NULL, TRUE, NULL, NULL, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(10, '冯雪', '主任医师', 10, '北京同仁医院', '近视、白内障、青光眼、干眼症', NULL, NULL, 5.0, 356, '8分钟', TRUE, TRUE, TRUE, NULL, 'qwen-plus', 0.7, 500, NULL, 'simple', NULL, TRUE, NULL, NULL, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(11, '蒋云', '副主任医师', 11, '北京同仁医院', '中耳炎、鼻炎、咽喉炎、耳鸣', NULL, NULL, 4.9, 298, '7分钟', TRUE, TRUE, TRUE, NULL, 'qwen-plus', 0.7, 500, NULL, 'simple', NULL, TRUE, NULL, NULL, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(12, '沈洁', '主治医师', 12, '北京口腔医院', '牙痛、龋齿、牙周病、智齿', NULL, NULL, 4.8, 234, '5分钟', FALSE, TRUE, TRUE, NULL, 'qwen-plus', 0.7, 500, NULL, 'simple', NULL, TRUE, NULL, NULL, '2026-01-09 06:28:16', '2026-01-09 06:28:16');

-- Table: drug_categories
DROP TABLE IF EXISTS drug_categories CASCADE;
CREATE TABLE drug_categories (
    id INTEGER NOT NULL,
    name TEXT NOT NULL,
    icon TEXT,
    description TEXT,
    display_type TEXT,
    sort_order INTEGER,
    is_active BOOLEAN,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Data for table: drug_categories
INSERT INTO drug_categories (id, name, icon, description, display_type, sort_order, is_active, created_at, updated_at) VALUES
(1, '热门药品', 'flame', '常用热门药品', 'grid', 1, TRUE, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(2, '感冒发烧', 'thermometer', '感冒发烧相关药品', 'grid', 2, TRUE, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(3, '消化系统', 'pills', '消化系统用药', 'grid', 3, TRUE, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(4, '皮肤用药', 'hand.raised', '皮肤病用药', 'grid', 4, TRUE, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(5, '心脑血管', 'heart', '心脑血管用药', 'grid', 5, TRUE, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(6, '孕期/哺乳期', 'figure.and.child.holdinghands', '孕期哺乳期安全用药', 'grid', 6, TRUE, '2026-01-09 06:28:16', '2026-01-09 06:28:16');

-- Table: drug_category_association
DROP TABLE IF EXISTS drug_category_association CASCADE;
CREATE TABLE drug_category_association (
    drug_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (drug_id, category_id)
);

-- Data for table: drug_category_association
INSERT INTO drug_category_association (drug_id, category_id) VALUES
(9, 5),
(10, 5),
(1, 1),
(2, 1),
(3, 1),
(4, 1),
(5, 1),
(6, 1),
(1, 2),
(2, 2),
(3, 2),
(4, 2),
(7, 4),
(8, 4),
(5, 3),
(6, 3);

-- Table: drugs
DROP TABLE IF EXISTS drugs CASCADE;
CREATE TABLE drugs (
    id INTEGER NOT NULL,
    name TEXT NOT NULL,
    pinyin TEXT,
    pinyin_abbr TEXT,
    aliases TEXT,
    common_brands TEXT,
    pregnancy_level TEXT,
    pregnancy_desc TEXT,
    lactation_level TEXT,
    lactation_desc TEXT,
    children_usable BOOLEAN,
    children_desc TEXT,
    indications TEXT,
    contraindications TEXT,
    dosage TEXT,
    side_effects TEXT,
    precautions TEXT,
    interactions TEXT,
    storage TEXT,
    author_name TEXT,
    author_title TEXT,
    author_avatar TEXT,
    reviewer_info TEXT,
    is_hot BOOLEAN,
    sort_order INTEGER,
    is_active BOOLEAN,
    view_count INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Data for table: drugs
INSERT INTO drugs (id, name, pinyin, pinyin_abbr, aliases, common_brands, pregnancy_level, pregnancy_desc, lactation_level, lactation_desc, children_usable, children_desc, indications, contraindications, dosage, side_effects, precautions, interactions, storage, author_name, author_title, author_avatar, reviewer_info, is_hot, sort_order, is_active, view_count, created_at, updated_at) VALUES
(1, '布洛芬', 'buluofen', 'blf', NULL, '芬必得、美林', 'C', '孕晚期禁用', 'L1', '哺乳期较安全', TRUE, '6个月以上儿童可用', '用于缓解轻至中度疼痛如头痛、关节痛、偏头痛、牙痛、肌肉痛、神经痛、痛经。也用于普通感冒或流行性感冒引起的发热。', '对本品过敏者禁用；消化性溃疡患者禁用；严重肝肾功能不全者禁用。', '成人：一次0.2g（1片），一日2-3次。儿童：按体重一次5-10mg/kg，每6-8小时一次。', '可见恶心、呕吐、胃烧灼感、轻度消化不良、皮疹、头痛、头晕等。', '不得空腹服用；不得长期或大量使用；与其他解热镇痛药同用可增加胃肠道不良反应。', NULL, '遮光，密封保存。', NULL, NULL, NULL, NULL, TRUE, 1, TRUE, 8520, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(2, '对乙酰氨基酚', 'duiyixiananjifeng', 'dyxajf', '扑热息痛', '泰诺、百服宁、必理通', 'B', '孕期相对安全', 'L1', '哺乳期安全', TRUE, '3个月以上儿童可用', '用于普通感冒或流行性感冒引起的发热，也用于缓解轻至中度疼痛如头痛、关节痛、偏头痛、牙痛、肌肉痛、神经痛、痛经。', '对本品过敏者禁用；严重肝肾功能不全者禁用。', '成人：一次0.5g，每4-6小时一次，24小时内不超过2g。儿童：按体重一次10-15mg/kg，每4-6小时一次。', '偶见皮疹、荨麻疹、药热及粒细胞减少。长期大量用药可导致肝肾损害。', '肝肾功能不全者慎用；不得同时服用含对乙酰氨基酚的其他药品；饮酒者慎用。', NULL, '遮光，密封保存。', NULL, NULL, NULL, NULL, TRUE, 2, TRUE, 7890, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(3, '阿奇霉素', 'aqimeisu', 'aqms', NULL, '希舒美、舒美特', 'B', '孕期较安全', 'L2', '哺乳期较安全', TRUE, '6个月以上儿童可用', '适用于敏感细菌所引起的呼吸道感染、皮肤软组织感染、沙眼衣原体所致单纯性生殖器感染等。', '对阿奇霉素、红霉素或其他大环内酯类药物过敏者禁用。', '成人：一次0.5g，一日1次，连用3天。儿童：按体重一次10mg/kg，一日1次，连用3天。', '可见腹泻、恶心、腹痛、稀便、呕吐等胃肠道反应。', '肝功能不全者慎用；不宜与抗酸药同时服用；饭前1小时或饭后2小时服用。', NULL, '遮光，密封，在干燥处保存。', NULL, NULL, NULL, NULL, TRUE, 3, TRUE, 6420, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(4, '奥司他韦', 'aositawei', 'astw', NULL, '达菲、可威', 'C', '孕期权衡利弊使用', 'L2', '哺乳期较安全', TRUE, '1岁以上儿童可用', '用于成人和1岁及1岁以上儿童的甲型和乙型流感治疗。用于成人和13岁及13岁以上青少年的甲型和乙型流感的预防。', '对本品任何成分过敏者禁用。', '成人治疗：一次75mg，一日2次，连续5天。成人预防：一次75mg，一日1次，至少7天。儿童按体重调整剂量。', '常见恶心、呕吐、腹泻、腹痛、头痛等。', '应在流感症状开始的48小时内使用；肾功能不全者需调整剂量。', NULL, '密封保存。', NULL, NULL, NULL, NULL, TRUE, 4, TRUE, 5890, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(5, '奥美拉唑', 'aomeilazuo', 'amlz', NULL, '洛赛克、奥克', 'C', '孕期权衡利弊使用', 'L2', '哺乳期较安全', TRUE, '1岁以上儿童可用', '适用于胃溃疡、十二指肠溃疡、应激性溃疡、反流性食管炎和卓-艾综合征（胃泌素瘤）。', '对本品过敏者禁用。', '成人：一次20mg，一日1-2次。十二指肠溃疡疗程通常为2-4周。', '可见腹泻、头痛、恶心、腹痛、便秘、胀气等。', '不宜长期使用；肝功能不全者慎用；可能掩盖胃癌症状。', NULL, '遮光，密封保存。', NULL, NULL, NULL, NULL, TRUE, 5, TRUE, 4670, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(6, '蒙脱石散', 'mengtuoshisan', 'mtss', NULL, '思密达、必奇', 'B', '孕期安全', 'L1', '哺乳期安全', TRUE, '新生儿可用', '用于成人及儿童急、慢性腹泻。用于食道、胃、十二指肠疾病引起的相关疼痛症状的辅助治疗。', '对本品过敏者禁用。', '成人：一次1袋（3g），一日3次。儿童：1岁以下一日1袋，1-2岁一日1-2袋，2岁以上一日2-3袋。', '可见便秘，通常减量后可消失。', '空腹服用效果更佳；严重便秘者慎用；不影响其他药物吸收。', NULL, '密封保存。', NULL, NULL, NULL, NULL, TRUE, 6, TRUE, 4230, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(7, '莫匹罗星软膏', 'mobiluoxing', 'mplx', NULL, '百多邦', 'B', '孕期较安全', 'L1', '哺乳期安全', TRUE, '儿童可用', '本品为局部外用抗生素，适用于革兰阳性球菌引起的皮肤感染，如脓疱病、疖肿、毛囊炎等原发性皮肤感染及湿疹合并感染、溃疡合并感染、创伤合并感染等继发性感染。', '对本品过敏者禁用。', '外用。取适量本品涂于患处，一日3次，疗程5天。可根据病情适当延长，但不宜超过10天。', '偶见局部烧灼感、刺痛、瘙痒、干燥、红斑等。', '避免接触眼睛和其他黏膜；不宜大面积使用；不宜长期使用。', NULL, '密封保存。', NULL, NULL, NULL, NULL, FALSE, 7, TRUE, 3850, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(8, '炉甘石洗剂', 'luganshixiji', 'lgsxj', NULL, NULL, 'A', '孕期安全', 'L1', '哺乳期安全', TRUE, '儿童可用', '用于急性瘙痒性皮肤病，如湿疹、痱子等。', '对本品过敏者禁用；有渗出液的皮肤部位禁用。', '外用。用时摇匀，取适量涂于患处，一日2-3次。', '偶见过敏反应。', '仅供外用，不得口服；避免接触眼睛和黏膜；用前摇匀。', NULL, '密封保存。', NULL, NULL, NULL, NULL, FALSE, 8, TRUE, 3520, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(9, '阿司匹林', 'asipiling', 'aspl', NULL, '拜阿司匹灵、阿司匹林肠溶片', 'D', '孕期慎用', 'L3', '哺乳期慎用', FALSE, '儿童慎用，可能引起瑞氏综合征', '用于预防心脑血管疾病；用于解热镇痛；用于抗风湿。', '对阿司匹林过敏者禁用；活动性溃疡病或其他原因引起的消化道出血禁用；血友病或血小板减少症禁用。', '预防心脑血管疾病：一次75-100mg，一日1次。解热镇痛：一次0.3-0.6g，一日3次。', '可见胃肠道反应、出血倾向、过敏反应等。', '餐后服用；不宜与抗凝药同用；定期检查凝血功能。', NULL, '遮光，密封保存。', NULL, NULL, NULL, NULL, TRUE, 9, TRUE, 5670, '2026-01-09 06:28:16', '2026-01-09 06:28:16'),
(10, '硝苯地平', 'xiaobendeping', 'xbdp', NULL, '拜新同、伲福达', 'C', '孕期权衡利弊使用', 'L2', '哺乳期较安全', FALSE, '儿童用药安全性未确立', '用于治疗高血压、冠心病、心绞痛。', '对本品过敏者禁用；心源性休克禁用；急性心肌梗死禁用。', '控释片：一次30mg，一日1次。缓释片：一次10-20mg，一日2-3次。', '可见头痛、面部潮红、心悸、踝部水肿等。', '不宜突然停药；低血压患者慎用；肝功能不全者慎用。', NULL, '遮光，密封保存。', NULL, NULL, NULL, NULL, FALSE, 10, TRUE, 4890, '2026-01-09 06:28:16', '2026-01-09 06:28:16');

-- Table: knowledge_bases
DROP TABLE IF EXISTS knowledge_bases CASCADE;
CREATE TABLE knowledge_bases (
    id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    doctor_id INTEGER,
    department_id INTEGER,
    kb_type TEXT,
    vector_store_config TEXT,
    embedding_model TEXT,
    total_documents INTEGER,
    total_chunks INTEGER,
    last_indexed_at TEXT,
    is_active BOOLEAN,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Table knowledge_bases: 无数据

-- Table: knowledge_documents
DROP TABLE IF EXISTS knowledge_documents CASCADE;
CREATE TABLE knowledge_documents (
    id INTEGER NOT NULL,
    knowledge_base_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    doc_type TEXT,
    source TEXT,
    tags TEXT,
    doc_metadata TEXT,
    status TEXT,
    reviewed_by INTEGER,
    reviewed_at TEXT,
    review_notes TEXT,
    is_indexed BOOLEAN,
    chunk_count INTEGER,
    embedding_data TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Table knowledge_documents: 无数据

-- Table: messages
DROP TABLE IF EXISTS messages CASCADE;
CREATE TABLE messages (
    id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    content TEXT NOT NULL,
    attachment_url TEXT,
    message_type TEXT,
    attachments TEXT,
    structured_data TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Data for table: messages
INSERT INTO messages (id, session_id, sender, content, attachment_url, message_type, attachments, structured_data, created_at) VALUES
(1, 'dd224f1e-f756-442e-8490-73317bee6721', 'user', '你好我手上皮肤不舒服', NULL, 'text', 'null', NULL, '2026-01-09 06:32:42'),
(2, 'dd224f1e-f756-442e-8490-73317bee6721', 'ai', '你好~我是你的皮肤科AI助手，将通过文字方式了解你的皮肤困扰，并给出温和、专业的建议。
请直接描述你目前的症状或担心的问题，我会一步步和你沟通。', NULL, 'text', NULL, 'null', '2026-01-09 06:32:42'),
(3, 'dd224f1e-f756-442e-8490-73317bee6721', 'user', '你好，我皮肤不舒服', NULL, 'text', 'null', NULL, '2026-01-09 06:33:16'),
(4, 'dd224f1e-f756-442e-8490-73317bee6721', 'ai', '你好~我是你的皮肤科AI助手，将通过文字方式了解你的皮肤困扰，并给出温和、专业的建议。
请直接描述你目前的症状或担心的问题，我会一步步和你沟通。', NULL, 'text', NULL, 'null', '2026-01-09 06:33:16'),
(5, 'dd224f1e-f756-442e-8490-73317bee6721', 'user', '你好，我皮肤有问题', NULL, 'text', 'null', NULL, '2026-01-09 06:36:54'),
(6, 'dd224f1e-f756-442e-8490-73317bee6721', 'ai', '你好~我是你的皮肤科AI助手，将通过文字方式了解你的皮肤困扰，并给出温和、专业的建议。
请直接描述你目前的症状或担心的问题，我会一步步和你沟通。', NULL, 'text', NULL, 'null', '2026-01-09 06:36:54'),
(7, 'b5448685-67b8-4484-bf6d-0b781e1f978f', 'user', '你好，我皮肤疼', NULL, 'text', 'null', NULL, '2026-01-09 06:40:13'),
(8, 'b5448685-67b8-4484-bf6d-0b781e1f978f', 'ai', '你提到皮肤疼，为了更准确地了解情况，我需要知道疼痛的具体部位。因为不同区域的皮肤问题可能原因不同，例如暴露部位多与外界刺激有关，而皱褶部位可能涉及摩擦或感染。', NULL, 'text', NULL, 'null', '2026-01-09 06:40:22'),
(9, 'b5448685-67b8-4484-bf6d-0b781e1f978f', 'user', '我是手臂上', NULL, 'text', 'null', NULL, '2026-01-09 06:41:01'),
(10, 'b5448685-67b8-4484-bf6d-0b781e1f978f', 'ai', '你提到手臂上有皮肤问题，为了更好地了解情况，请先确认主要有哪些不适？例如是否有红肿、瘙痒或疼痛等症状？明确症状有助于判断可能的原因。', NULL, 'text', NULL, 'null', '2026-01-09 06:41:09'),
(11, 'b5448685-67b8-4484-bf6d-0b781e1f978f', 'user', '有红肿，但是之前是和老婆打架的时候，她拿指甲刮的，现在还不见好，就是不结疤', NULL, 'text', 'null', NULL, '2026-01-09 06:42:55'),
(12, 'b5448685-67b8-4484-bf6d-0b781e1f978f', 'ai', '你提到皮肤红肿且之前有被指甲刮伤的情况，目前伤口仍未结痂。外伤后的红肿持续不愈可能与局部感染、持续刺激或愈合障碍有关。为了判断是否存在感染或其他并发症，需要确认当前是否有渗液（比如流黄水、脓液）或明显疼痛。', NULL, 'text', NULL, 'null', '2026-01-09 06:43:02'),
(13, 'b5448685-67b8-4484-bf6d-0b781e1f978f', 'user', '流黄水，和脓液', NULL, 'text', 'null', NULL, '2026-01-09 06:43:39'),
(14, 'b5448685-67b8-4484-bf6d-0b781e1f978f', 'ai', '你提到有流黄水和脓液的情况，这通常是感染或炎症的表现。为了更好地判断原因，我需要知道这些分泌物是从哪个部位出现的？比如是皮肤破损处、毛囊区域、生殖器周围还是其他地方？', NULL, 'text', NULL, 'null', '2026-01-09 06:43:48'),
(15, 'b5448685-67b8-4484-bf6d-0b781e1f978f', 'user', '皮肤破损处', NULL, 'text', 'null', NULL, '2026-01-09 06:44:13'),
(16, 'b5448685-67b8-4484-bf6d-0b781e1f978f', 'ai', '你提到皮肤有破损处，为了更好地了解情况，我需要知道这个破损是否伴有疼痛、瘙痒或渗液？这些信息有助于判断是否存在感染或其他刺激因素。', NULL, 'text', NULL, 'null', '2026-01-09 06:44:19'),
(17, 'b5448685-67b8-4484-bf6d-0b781e1f978f', 'user', '有疼痛，和无瘙痒', NULL, 'text', 'null', NULL, '2026-01-09 06:44:58'),
(18, 'b5448685-67b8-4484-bf6d-0b781e1f978f', 'ai', '你提到有疼痛但无瘙痒，这有助于缩小可能原因的范围。疼痛性皮肤问题常与刺激、创伤、感染（如疱疹）或炎症相关。为了进一步判断，需要了解疼痛的具体性质：是灼烧感、刺痛感，还是触碰时才疼？', NULL, 'text', NULL, 'null', '2026-01-09 06:45:06');

-- Table: session_feedbacks
DROP TABLE IF EXISTS session_feedbacks CASCADE;
CREATE TABLE session_feedbacks (
    id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    message_id INTEGER,
    user_id INTEGER NOT NULL,
    rating INTEGER,
    feedback_type TEXT,
    feedback_text TEXT,
    status TEXT,
    handled_by INTEGER,
    handled_at TEXT,
    resolution_notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Table session_feedbacks: 无数据

-- Table: sessions
DROP TABLE IF EXISTS sessions CASCADE;
CREATE TABLE sessions (
    id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    doctor_id INTEGER,
    agent_type TEXT NOT NULL,
    agent_state TEXT,
    last_message TEXT,
    status TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Data for table: sessions
INSERT INTO sessions (id, user_id, doctor_id, agent_type, agent_state, last_message, status, created_at, updated_at) VALUES
('0cd6abed-42d1-4551-9cd4-ab08274ef41a', 1, 1, 'dermatology', '{"session_id": "0cd6abed-42d1-4551-9cd4-ab08274ef41a", "user_id": 1, "messages": [], "chief_complaint": "", "symptoms": [], "symptom_details": {}, "skin_location": "", "duration": "", "skin_analyses": [], "latest_analysis": null, "report_interpretations": [], "latest_interpretation": null, "stage": "greeting", "progress": 0, "questions_asked": 0, "current_response": "", "quick_options": [], "possible_conditions": [], "risk_level": "low", "care_advice": "", "need_offline_visit": false, "current_task": "conversation", "awaiting_image": false}', NULL, 'active', '2026-01-09 06:29:51', '2026-01-09 06:29:51'),
('dae9fe57-2584-4197-8e20-468c3d7dfcab', 1, 1, 'dermatology', '{"session_id": "dae9fe57-2584-4197-8e20-468c3d7dfcab", "user_id": 1, "messages": [], "chief_complaint": "", "symptoms": [], "symptom_details": {}, "skin_location": "", "duration": "", "skin_analyses": [], "latest_analysis": null, "report_interpretations": [], "latest_interpretation": null, "stage": "greeting", "progress": 0, "questions_asked": 0, "current_response": "", "quick_options": [], "possible_conditions": [], "risk_level": "low", "care_advice": "", "need_offline_visit": false, "current_task": "conversation", "awaiting_image": false}', NULL, 'active', '2026-01-09 06:29:53', '2026-01-09 06:29:53'),
('dd224f1e-f756-442e-8490-73317bee6721', 1, 1, 'dermatology', '{"session_id": "dd224f1e-f756-442e-8490-73317bee6721", "user_id": 1, "messages": [], "chief_complaint": "", "symptoms": [], "symptom_details": {}, "skin_location": "", "duration": "", "skin_analyses": [], "latest_analysis": null, "report_interpretations": [], "latest_interpretation": null, "stage": "greeting", "progress": 0, "questions_asked": 0, "current_response": "", "quick_options": [], "possible_conditions": [], "risk_level": "low", "care_advice": "", "need_offline_visit": false, "current_task": "conversation", "awaiting_image": false}', '你好~我是你的皮肤科AI助手，将通过文字方式了解你的皮肤困扰，并给出温和、专业的建议。
请直接描述你目前的症状或担心的问题，我会一步步和你沟通。', 'active', '2026-01-09 06:32:19', '2026-01-09 06:32:42'),
('b5448685-67b8-4484-bf6d-0b781e1f978f', 1, 1, 'dermatology', '{"session_id": "b5448685-67b8-4484-bf6d-0b781e1f978f", "user_id": 1, "messages": [], "chief_complaint": "", "symptoms": [], "symptom_details": {}, "skin_location": "", "duration": "", "skin_analyses": [], "latest_analysis": null, "report_interpretations": [], "latest_interpretation": null, "stage": "greeting", "progress": 0, "questions_asked": 0, "current_response": "", "quick_options": [], "possible_conditions": [], "risk_level": "low", "care_advice": "", "need_offline_visit": false, "current_task": "conversation", "awaiting_image": false}', '你提到有疼痛但无瘙痒，这有助于缩小可能原因的范围。疼痛性皮肤问题常与刺激、创伤、感染（如疱疹）或炎症相关。为了进一步判断，需要了解疼痛的具体性质：是灼烧感、刺痛感，还是触碰时才疼？', 'active', '2026-01-09 06:40:02', '2026-01-09 06:45:06');

-- Table: users
DROP TABLE IF EXISTS users CASCADE;
CREATE TABLE users (
    id INTEGER NOT NULL,
    phone TEXT NOT NULL,
    nickname TEXT,
    avatar_url TEXT,
    gender TEXT,
    birthday TEXT,
    emergency_contact_name TEXT,
    emergency_contact_phone TEXT,
    emergency_contact_relation TEXT,
    is_profile_completed BOOLEAN,
    is_active BOOLEAN,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Data for table: users
INSERT INTO users (id, phone, nickname, avatar_url, gender, birthday, emergency_contact_name, emergency_contact_phone, emergency_contact_relation, is_profile_completed, is_active, created_at, updated_at) VALUES
(1, '18107300167', '用户0167', NULL, NULL, NULL, NULL, NULL, NULL, FALSE, TRUE, '2026-01-09 06:29:46', '2026-01-09 06:29:46');

-- 序列设置（用于自增 ID）
-- 注意: PostgreSQL 需要手动创建序列或使用 SERIAL/BIGSERIAL

-- users.id 是自增主键
-- 在 PostgreSQL 中已使用 SERIAL 或 GENERATED ALWAYS AS IDENTITY

-- departments.id 是自增主键
-- 在 PostgreSQL 中已使用 SERIAL 或 GENERATED ALWAYS AS IDENTITY

-- admin_users.id 是自增主键
-- 在 PostgreSQL 中已使用 SERIAL 或 GENERATED ALWAYS AS IDENTITY

-- audit_logs.id 是自增主键
-- 在 PostgreSQL 中已使用 SERIAL 或 GENERATED ALWAYS AS IDENTITY

-- drug_categories.id 是自增主键
-- 在 PostgreSQL 中已使用 SERIAL 或 GENERATED ALWAYS AS IDENTITY

-- drugs.id 是自增主键
-- 在 PostgreSQL 中已使用 SERIAL 或 GENERATED ALWAYS AS IDENTITY

-- doctors.id 是自增主键
-- 在 PostgreSQL 中已使用 SERIAL 或 GENERATED ALWAYS AS IDENTITY

-- drug_category_association.drug_id 是自增主键
-- 在 PostgreSQL 中已使用 SERIAL 或 GENERATED ALWAYS AS IDENTITY

-- drug_category_association.category_id 是自增主键
-- 在 PostgreSQL 中已使用 SERIAL 或 GENERATED ALWAYS AS IDENTITY

-- messages.id 是自增主键
-- 在 PostgreSQL 中已使用 SERIAL 或 GENERATED ALWAYS AS IDENTITY

-- knowledge_documents.id 是自增主键
-- 在 PostgreSQL 中已使用 SERIAL 或 GENERATED ALWAYS AS IDENTITY

-- session_feedbacks.id 是自增主键
-- 在 PostgreSQL 中已使用 SERIAL 或 GENERATED ALWAYS AS IDENTITY

-- diseases.id 是自增主键
-- 在 PostgreSQL 中已使用 SERIAL 或 GENERATED ALWAYS AS IDENTITY

COMMIT;
-- 数据迁移完成

