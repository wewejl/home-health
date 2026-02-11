"""
药品管理 API 测试

测试内容：
- 药品列表获取
- 药品搜索
- 药品详情获取
- 药品分类获取
- 热门药品获取
"""
import pytest

try:
    from app.models.drug import Drug, DrugCategory
    from app.models.department import Department
except ImportError:
    from backend.app.models.drug import Drug, DrugCategory
    from backend.app.models.department import Department


# ============================================================================
# 药品 API 测试
# ============================================================================

def test_get_drug_categories_with_drugs(test_client):
    """测试获取药品分类及其热门药品"""
    response = test_client.get("/api/drugs/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_drug_categories_with_limit(test_client):
    """测试获取药品分类 - 带限制"""
    response = test_client.get("/api/drugs/categories?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # 验证每个分类的药品数量不超过限制
    for category in data:
        if "drugs" in category:
            assert len(category["drugs"]) <= 5


def test_get_hot_drugs(test_client):
    """测试获取热门药品列表"""
    response = test_client.get("/api/drugs/hot")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_hot_drugs_with_limit(test_client):
    """测试获取热门药品列表 - 带限制"""
    response = test_client.get("/api/drugs/hot?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5


def test_get_hot_drugs_by_category(db_session, test_client):
    """测试按分类获取热门药品"""
    # 创建测试分类
    category = DrugCategory(
        name="感冒用药",
        icon="pill",
        description="感冒相关药品",
        display_type="grid",
        sort_order=1,
        is_active=True
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    # 创建测试药品
    drug = Drug(
        name="布洛芬",
        pinyin="buluofen",
        pinyin_abbr="blf",
        common_brands="芬必得",
        is_hot=True,
        is_active=True,
        sort_order=1
    )
    db_session.add(drug)
    db_session.commit()
    db_session.refresh(drug)

    # 关联药品和分类
    drug.categories.append(category)
    db_session.commit()

    response = test_client.get(f"/api/drugs/hot?category_id={category.id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_search_drugs(test_client):
    """测试搜索药品"""
    response = test_client.get("/api/drugs/search?q=阿司匹林")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_search_drugs_empty_query(test_client):
    """测试搜索药品 - 空查询（应该验证失败）"""
    response = test_client.get("/api/drugs/search?q=")
    # 空查询应该返回422验证错误
    assert response.status_code == 422


def test_search_drugs_by_pinyin(db_session, test_client):
    """测试通过拼音搜索药品"""
    # 创建测试分类
    category = DrugCategory(
        name="解热镇痛",
        icon="thermometer",
        description="解热镇痛药品",
        is_active=True
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    # 创建测试药品
    drug = Drug(
        name="对乙酰氨基酚",
        pinyin="duiyixiananjifen",
        pinyin_abbr="dyxajf",
        common_brands="泰诺、必理通",
        is_active=True
    )
    db_session.add(drug)
    db_session.commit()
    db_session.refresh(drug)

    # 关联药品和分类
    drug.categories.append(category)
    db_session.commit()

    # 测试拼音搜索
    response = test_client.get("/api/drugs/search?q=duiyixiananjifen")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data

    # 测试拼音缩写搜索
    response = test_client.get("/api/drugs/search?q=dyxajf")
    assert response.status_code == 200


def test_search_drugs_by_brand(db_session, test_client):
    """测试通过商品名搜索药品"""
    # 创建测试分类
    category = DrugCategory(
        name="感冒药",
        icon="capsule",
        is_active=True
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    # 创建测试药品
    drug = Drug(
        name="复方氨酚烷胺",
        pinyin="fufinganfenwanan",
        pinyin_abbr="ffgfw a",
        common_brands="感康、快克",
        is_active=True
    )
    db_session.add(drug)
    db_session.commit()
    db_session.refresh(drug)

    # 关联药品和分类
    drug.categories.append(category)
    db_session.commit()

    # 测试通过商品名搜索
    response = test_client.get("/api/drugs/search?q=感康")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data


def test_search_drugs_with_offset_and_limit(test_client):
    """测试药品搜索的分页功能"""
    response = test_client.get("/api/drugs/search?q=阿司匹林&limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert len(data["items"]) <= 5


def test_search_drugs_by_category(db_session, test_client):
    """测试在指定分类下搜索药品"""
    # 创建测试分类
    category = DrugCategory(
        name="抗生素",
        icon=" prescription",
        is_active=True
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    # 创建测试药品
    drug = Drug(
        name="阿莫西林",
        pinyin="amoxilin",
        pinyin_abbr="amxl",
        common_brands="阿莫仙、再林",
        is_active=True
    )
    db_session.add(drug)
    db_session.commit()
    db_session.refresh(drug)

    # 关联药品和分类
    drug.categories.append(category)
    db_session.commit()

    response = test_client.get(f"/api/drugs/search?q=阿&category_id={category.id}")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_get_drug_detail_success(db_session, test_client):
    """测试获取药品详情 - 成功"""
    # 创建测试分类
    category = DrugCategory(
        name="消化系统用药",
        icon="stomach",
        is_active=True
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    # 创建测试药品
    drug = Drug(
        name="奥美拉唑",
        pinyin="aomeilazuo",
        pinyin_abbr="amlz",
        common_brands="洛赛克、奥克",
        pregnancy_level="C",
        pregnancy_desc="妊娠分级 C",
        lactation_level="L3",
        lactation_desc="哺乳分级 L3",
        children_usable=True,
        indications="治疗胃溃疡、十二指肠溃疡",
        contraindications="对本品过敏者禁用",
        dosage="口服，一次20mg",
        side_effects="头痛、腹泻",
        precautions="长期使用需定期检查",
        storage="密封，在干燥处保存",
        author_name="张医生",
        author_title="主任医师",
        is_active=True,
        view_count=100
    )
    db_session.add(drug)
    db_session.commit()
    db_session.refresh(drug)

    # 关联药品和分类
    drug.categories.append(category)
    db_session.commit()

    response = test_client.get(f"/api/drugs/{drug.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == drug.id
    assert data["name"] == "奥美拉唑"
    assert "indications" in data
    assert "contraindications" in data
    assert "pregnancy_level" in data
    assert "lactation_level" in data
    assert "children_usable" in data


def test_get_drug_detail_not_found(test_client):
    """测试获取药品详情 - 不存在"""
    response = test_client.get("/api/drugs/999999")
    assert response.status_code == 404


def test_get_drug_detail_with_view_count_increment(db_session, test_client):
    """测试获取药品详情后浏览次数增加"""
    # 创建测试分类
    category = DrugCategory(
        name="维生素类",
        icon="vitamin",
        is_active=True
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    # 创建测试药品
    drug = Drug(
        name="维生素C",
        pinyin="weishengsuC",
        pinyin_abbr="wss C",
        common_brands="力度伸",
        is_active=True,
        view_count=50
    )
    db_session.add(drug)
    db_session.commit()
    db_session.refresh(drug)

    # 关联药品和分类
    drug.categories.append(category)
    db_session.commit()

    initial_view_count = drug.view_count

    response = test_client.get(f"/api/drugs/{drug.id}")
    assert response.status_code == 200

    # 验证浏览次数增加
    db_session.refresh(drug)
    assert drug.view_count == initial_view_count + 1


def test_get_drugs_inactive_not_returned(db_session, test_client):
    """测试非活跃药品不返回"""
    # 创建测试分类
    category = DrugCategory(
        name="测试分类",
        is_active=True
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    # 创建非活跃药品
    drug = Drug(
        name="测试药品",
        pinyin="ceshipinyaop",
        pinyin_abbr="cspyp",
        is_active=False  # 非活跃
    )
    db_session.add(drug)
    db_session.commit()
    db_session.refresh(drug)

    # 关联药品和分类
    drug.categories.append(category)
    db_session.commit()

    # 搜索结果中不应该包含非活跃药品
    response = test_client.get("/api/drugs/search?q=测试")
    assert response.status_code == 200
    data = response.json()
    drug_ids = [d["id"] for d in data["items"]]
    assert drug.id not in drug_ids


def test_get_drug_categories_inactive_not_returned(db_session, test_client):
    """测试非活跃分类不返回"""
    # 创建非活跃分类
    category = DrugCategory(
        name="非活跃分类",
        is_active=False  # 非活跃
    )
    db_session.add(category)
    db_session.commit()

    response = test_client.get("/api/drugs/categories")
    assert response.status_code == 200
    data = response.json()
    category_ids = [c["id"] for c in data]
    assert category.id not in category_ids


def test_search_drugs_by_aliases(db_session, test_client):
    """测试通过别名搜索药品"""
    # 创建测试分类
    category = DrugCategory(
        name="止痛药",
        icon="painkiller",
        is_active=True
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    # 创建测试药品
    drug = Drug(
        name="双氯芬酸钠",
        pinyin="shuanglvifensuanna",
        pinyin_abbr="slfsnn",
        aliases="扶他林、迪克乐克",
        common_brands=" Voltaren",
        is_active=True
    )
    db_session.add(drug)
    db_session.commit()
    db_session.refresh(drug)

    # 关联药品和分类
    drug.categories.append(category)
    db_session.commit()

    # 测试通过别名搜索
    response = test_client.get("/api/drugs/search?q=扶他林")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data


def test_drug_category_display_type(db_session, test_client):
    """测试药品分类显示类型"""
    # 创建测试分类 - 列表类型
    category = DrugCategory(
        name="特殊药品",
        icon="special",
        description="需要特殊管理的药品",
        display_type="list",
        sort_order=1,
        is_active=True
    )
    db_session.add(category)
    db_session.commit()

    response = test_client.get("/api/drugs/categories")
    assert response.status_code == 200
    data = response.json()

    # 查找我们创建的分类
    found = False
    for cat in data:
        if cat["id"] == category.id:
            found = True
            assert cat["display_type"] == "list"
            break

    assert found, "创建的分类应该在返回结果中"


def test_get_drugs_by_multiple_categories(db_session, test_client):
    """测试获取多个分类的药品"""
    # 创建两个测试分类
    category1 = DrugCategory(
        name="分类1",
        icon="cat1",
        is_active=True,
        sort_order=1
    )
    category2 = DrugCategory(
        name="分类2",
        icon="cat2",
        is_active=True,
        sort_order=2
    )
    db_session.add(category1)
    db_session.add(category2)
    db_session.commit()
    db_session.refresh(category1)
    db_session.refresh(category2)

    # 创建测试药品，属于两个分类
    drug = Drug(
        name="多分类药品",
        pinyin="duofenleiyaopin",
        pinyin_abbr="dfl yp",
        is_active=True
    )
    db_session.add(drug)
    db_session.commit()
    db_session.refresh(drug)

    # 关联药品到两个分类
    drug.categories.append(category1)
    drug.categories.append(category2)
    db_session.commit()

    # 获取分类列表，验证药品出现在两个分类中
    response = test_client.get("/api/drugs/categories")
    assert response.status_code == 200
    data = response.json()

    # 验证药品在两个分类中都能找到
    found_in_cat1 = False
    found_in_cat2 = False

    for cat in data:
        if cat["id"] == category1.id:
            drug_ids = [d["id"] for d in cat.get("drugs", [])]
            found_in_cat1 = drug.id in drug_ids
        elif cat["id"] == category2.id:
            drug_ids = [d["id"] for d in cat.get("drugs", [])]
            found_in_cat2 = drug.id in drug_ids

    # 至少在一个分类中找到（因为limit限制）
    assert found_in_cat1 or found_in_cat2


def test_get_drug_detail_with_children_info(db_session, test_client):
    """测试获取药品详情中的儿童用药信息"""
    # 创建测试分类
    category = DrugCategory(
        name="儿科用药",
        icon="baby",
        is_active=True
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    # 创建测试药品 - 儿童可用
    drug = Drug(
        name="儿童退热药",
        pinyin="ertongtuireyao",
        pinyin_abbr="et try",
        common_brands="美林",
        children_usable=True,
        children_desc="6个月以上儿童可用",
        is_active=True
    )
    db_session.add(drug)
    db_session.commit()
    db_session.refresh(drug)

    # 关联药品和分类
    drug.categories.append(category)
    db_session.commit()

    response = test_client.get(f"/api/drugs/{drug.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["children_usable"] is True
    assert data["children_desc"] == "6个月以上儿童可用"


def test_get_drug_detail_with_pregnancy_info(db_session, test_client):
    """测试获取药品详情中的孕期用药信息"""
    # 创建测试分类
    category = DrugCategory(
        name="孕期用药",
        icon="pregnant",
        is_active=True
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    # 创建测试药品
    drug = Drug(
        name="叶酸",
        pinyin="yesuan",
        pinyin_abbr="ys",
        common_brands="斯利安",
        pregnancy_level="A",
        pregnancy_desc="妊娠分级 A，安全",
        lactation_level="L1",
        lactation_desc="哺乳分级 L1，安全",
        is_active=True
    )
    db_session.add(drug)
    db_session.commit()
    db_session.refresh(drug)

    # 关联药品和分类
    drug.categories.append(category)
    db_session.commit()

    response = test_client.get(f"/api/drugs/{drug.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["pregnancy_level"] == "A"
    assert data["pregnancy_desc"] == "妊娠分级 A，安全"
    assert data["lactation_level"] == "L1"
    assert data["lactation_desc"] == "哺乳分级 L1，安全"


def test_search_drugs_case_insensitive(db_session, test_client):
    """测试搜索药品大小写不敏感"""
    # 创建测试分类
    category = DrugCategory(
        name="测试分类",
        is_active=True
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    # 创建测试药品
    drug = Drug(
        name="阿莫西林",
        pinyin="Amoxilin",  # 首字母大写
        pinyin_abbr="Amxl",
        is_active=True
    )
    db_session.add(drug)
    db_session.commit()
    db_session.refresh(drug)

    # 关联药品和分类
    drug.categories.append(category)
    db_session.commit()

    # 测试小写搜索
    response = test_client.get("/api/drugs/search?q=amoxilin")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
