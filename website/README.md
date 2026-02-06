# 灵犀健康官方网站

灵犀健康（Lingxi Health）的官方网站，展示产品功能、使用场景，并提供用户下载入口。

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式**: TailwindCSS
- **路由**: React Router v6
- **动画**: Framer Motion
- **图标**: Lucide React

## 开发

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:5174

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 项目结构

```
website/
├── public/          # 静态资源
├── src/
│   ├── components/  # 可复用组件
│   │   ├── Navbar.tsx
│   │   ├── Footer.tsx
│   │   ├── Hero.tsx
│   │   ├── FeatureCard.tsx
│   │   └── ...
│   ├── pages/       # 页面组件
│   │   ├── Home.tsx
│   │   ├── Features.tsx
│   │   ├── Scenarios.tsx
│   │   ├── About.tsx
│   │   └── Download.tsx
│   ├── styles/      # 样式文件
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

## 设计系统

### 配色方案

| 颜色 | 用途 | Hex |
|------|------|-----|
| 主蓝色 | 品牌主色 | #1890FF |
| 青色 | 强调色 | #13C2C2 |
| 橙色 | CTA / 警告 | #FA8C16 |
| 绿色 | 成功状态 | #52C41A |
| 紫色 | 特殊功能 | #722ED1 |
| 背景色 | 页面背景 | #F5F8FA |
| 卡片背景 | 卡片背景 | #FFFFFF |
| 主文字 | 主要文字 | #262626 |
| 次要文字 | 次要文字 | #8C8C8C |

### 圆角

- 小: 8px
- 中: 12px
- 大: 16px
- 超大: 24px

### 阴影

- 卡片: 0 4px 12px rgba(0, 0, 0, 0.06)
- 卡片悬浮: 0 8px 24px rgba(24, 144, 255, 0.12)

## 页面

- `/` - 首页
- `/features` - 产品功能
- `/scenarios` - 使用场景
- `/about` - 关于我们
- `/download` - 下载应用

## 部署

### Vercel

```bash
vercel deploy
```

### Netlify

```bash
netlify deploy --prod
```

## License

© 2026 灵犀健康. All rights reserved.
