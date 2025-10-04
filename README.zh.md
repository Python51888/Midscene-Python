# Midscene Python     [![zread](https://img.shields.io/badge/Ask_Zread-_.svg?style=flat&color=00b0aa&labelColor=000000&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuOTYxNTYgMS42MDAxSDIuMjQxNTZDMS44ODgxIDEuNjAwMSAxLjYwMTU2IDEuODg2NjQgMS42MDE1NiAyLjI0MDFWNC45NjAxQzEuNjAxNTYgNS4zMTM1NiAxLjg4ODEgNS42MDAxIDIuMjQxNTYgNS42MDAxSDQuOTYxNTZDNS4zMTUwMiA1LjYwMDEgNS42MDE1NiA1LjMxMzU2IDUuNjAxNTYgNC45NjAxVjIuMjQwMUM1LjYwMTU2IDEuODg2NjQgNS4zMTUwMiAxLjYwMDEgNC45NjE1NiAxLjYwMDFaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00Ljk2MTU2IDEwLjM5OTlIMi4yNDE1NkMxLjg4ODEgMTAuMzk5OSAxLjYwMTU2IDEwLjY4NjQgMS42MDE1NiAxMS4wMzk5VjEzLjc1OTlDMS42MDE1NiAxNC4xMTM0IDEuODg4MSAxNC4zOTk5IDIuMjQxNTYgMTQuMzk5OUg0Ljk2MTU2QzUuMzE1MDIgMTQuMzk5OSA1LjYwMTU2IDE0LjExMzQgNS42MDE1NiAxMy43NTk5VjExLjAzOTlDNS42MDE1NiAxMC42ODY0IDUuMzE1MDIgMTAuMzk5OSA0Ljk2MTU2IDEwLjM5OTlaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik0xMy43NTg0IDEuNjAwMUgxMS4wMzg0QzEwLjY4NSAxLjYwMDEgMTAuMzk4NCAxLjg4NjY0IDEwLjM5ODQgMi4yNDAxVjQuOTYwMUMxMC4zOTg0IDUuMzEzNTYgMTAuNjg1IDUuNjAwMSAxMS4wMzg0IDUuNjAwMUgxMy43NTg0QzE0LjExMTkgNS42MDAxIDE0LjM5ODQgNS4zMTM1NiAxNC4zOTg0IDQuOTYwMVYyLjI0MDFDMTQuMzk4NCAxLjg4NjY0IDE0LjExMTkgMS42MDAxIDEzLjc1ODQgMS42MDAxWiIgZmlsbD0iI2ZmZiIvPgo8cGF0aCBkPSJNNCAxMkwxMiA0TDQgMTJaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00IDEyTDEyIDQiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K&logoColor=ffffff)](https://zread.ai/Python51888/Midscene-Python)

[English](README.md) | [中文](README.zh.md)  

Midscene Python 是一个基于 AI 的自动化框架，支持 Web 和 Android 平台的 UI 自动化操作。

## 概述

Midscene Python 提供全面的 UI 自动化能力，具有以下核心特性：

- **自然语言驱动**：使用自然语言描述自动化任务
- **多平台支持**：支持 Web（Selenium/Playwright）和 Android（ADB）
- **AI 模型集成**：支持 GPT-4V、Qwen2.5-VL、Gemini 等多种视觉语言模型
- **可视化调试**：提供详细的执行报告和调试信息
- **缓存机制**：智能缓存提升执行效率

## 项目架构

```
midscene-python/
├── midscene/                    # 核心框架
│   ├── core/                    # 核心框架
│   │   ├── agent/              # Agent系统
│   │   ├── insight/            # AI推理引擎
│   │   ├── ai_model/           # AI模型集成
│   │   ├── yaml/               # YAML脚本执行器
│   │   └── types.py            # 核心类型定义
│   ├── web/                     # Web集成
│   │   ├── selenium/           # Selenium集成
│   │   ├── playwright/         # Playwright集成
│   │   └── bridge/             # Bridge模式
│   ├── android/                 # Android集成
│   │   ├── device.py           # 设备管理
│   │   └── agent.py            # Android Agent
│   ├── cli/                     # 命令行工具
│   ├── mcp/                     # MCP协议支持
│   ├── shared/                 # 共享工具
│   └── visualizer/             # 可视化报告
├── examples/                   # 示例代码
├── tests/                      # 测试用例
└── docs/                       # 文档
```

## 技术栈

- **Python 3.9+**：核心运行环境
- **Pydantic**：数据验证和序列化
- **Selenium/Playwright**：Web 自动化
- **OpenCV/Pillow**：图像处理
- **HTTPX/AIOHTTP**：HTTP 客户端
- **Typer**：CLI 框架
- **Loguru**：日志记录

## 快速开始

### 安装

```bash
pip install midscene-python
```

### 基础用法

```python
from midscene import Agent
from midscene.web import SeleniumWebPage

# 创建 Web Agent
with SeleniumWebPage.create() as page:
    agent = Agent(page)
    
    # 使用自然语言进行自动化操作
    await agent.ai_action("点击登录按钮")
    await agent.ai_action("输入用户名 'test@example.com'")
    await agent.ai_action("输入密码 'password123'")
    await agent.ai_action("点击提交按钮")
    
    # 数据提取
    user_info = await agent.ai_extract("提取用户个人信息")
    
    # 断言验证
    await agent.ai_assert("页面显示欢迎信息")
```

## 主要特性

### 🤖 AI 驱动的自动化

使用自然语言描述操作，AI 自动理解并执行：

```python
await agent.ai_action("在搜索框中输入'Python教程'并搜索")
```

### 🔍 智能元素定位

支持多种定位策略，自动选择最优方案：

```python
element = await agent.ai_locate("登录按钮")
```

### 📊 数据提取

从页面提取结构化数据：

```python
products = await agent.ai_extract({
    "products": [
        {"name": "产品名称", "price": "价格", "rating": "评分"}
    ]
})
```

### ✅ 智能断言

AI 理解页面状态，进行智能断言：

```python
await agent.ai_assert("用户已成功登录")
```

### 📝 致谢

感谢Midscene项目：https://github.com/web-infra-dev/midscene 提供的灵感和技术参考

## 许可证

MIT License
