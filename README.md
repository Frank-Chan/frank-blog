# Frank's Tech Blog

技术分享 · 点云渲染 · AI 编程 · 工程实践

基于 [Hugo](https://gohugo.io/) + [PaperMod](https://github.com/adityatelange/hugo-PaperMod) 主题，通过 GitHub Pages 自动部署。

## 架构

飞书写作 → Hermes 拉取 + 脱敏 → Git 管理 → GitHub Actions 自动部署 → GitHub Pages

详见 📋 个人知识库共享方案文档。

## 本地开发

```bash
# 安装 Hugo Extended
choco install hugo-extended
# 或 winget install Hugo.Hugo.Extended

# 启动本地服务器
hugo server -D

# 构建
hugo
```

## 目录结构

```
frank-blog/
├── content/          # 文章（Markdown）
├── archive/          # 历史文章归档
├── scripts/          # 自动化脚本
├── themes/PaperMod/  # Hugo 主题
├── .github/workflows/ # GitHub Actions
└── hugo.yaml         # Hugo 配置
```
