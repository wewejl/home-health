# MedLive 药品爬虫使用说明

## 📋 概述

此爬虫用于从医脉通药品参考数据库 (drugs.medlive.cn) 获取药品数据并导入到本地数据库。

## 🔑 获取 Cookie

由于 MedLive 需要登录才能查看药品详情，请按以下步骤获取 Cookie：

### 方法一：浏览器开发者工具

1. 打开浏览器，访问 https://drugs.medlive.cn
2. 登录您的账号
3. 按 `F12` 打开开发者工具
4. 切换到 `Network` 标签
5. 刷新页面或访问任意药品详情页
6. 点击请求，查看 `Request Headers` 中的 `Cookie`
7. 复制完整的 Cookie 值

### 方法二：浏览器插件

使用 `EditThisCookie` 或 `Cookie-Editor` 插件导出 Cookie。

## 🚀 使用方法

### 方式 1：命令行参数

```bash
cd backend/scripts/medlive_crawler
python drug_crawler.py --detail-ids 4adae13be2c445f389f058211eacca9e --cookie "your_cookie_here"
```

### 方式 2：环境变量

```bash
export MEDLIVE_DRUG_COOKIE="your_cookie_here"
python drug_crawler.py --detail-ids 4adae13be2c445f389f058211eacca9e
```

### 方式 3：批量导入

创建 `drug_ids.txt` 文件，每行一个 detailId：

```
4adae13be2c445f389f058211eacca9e
another_detail_id
...
```

然后运行：

```bash
python drug_crawler.py --file drug_ids.txt
```

## 📦 收集药品 detailId

由于 MedLive 搜索需要登录，目前 detailId 需要手动收集：

1. 登录后访问药品搜索页
2. 搜索目标药品（如"布洛芬"）
3. 点击进入详情页
4. 从 URL 中复制 `detailId` 参数值

## ⚠️ 常见问题

### Cookie 失效

如果看到 `Cookie 已失效` 提示，请：
1. 重新登录网站
2. 获取新的 Cookie
3. 更新命令或环境变量

### 解析失败

药品页面结构可能发生变化，如果解析失败请：
1. 检查页面是否正常加载
2. 确认登录状态
3. 联系开发者更新解析逻辑

## 📊 数据映射

爬虫会自动将 MedLive 的分类映射到我们的分类系统：

| MedLive 分类 | 映射到 |
|-------------|--------|
| 解热镇痛抗炎抗风湿 | 感冒发烧 |
| 抗生素 | 感冒发烧 |
| 呼吸系统 | 感冒发烧 |
| 消化系统 | 消化系统 |
| 皮肤科 | 皮肤用药 |
| 心血管 | 心脑血管 |
| 其他 | 其他 |
