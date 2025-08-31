# 快速开始 - Midscene Python

Midscene Python 是一个基于 AI 的自动化框架，支持 Web 和 Android 平台的 UI 自动化操作。

## 安装

```bash
pip install midscene-python
```

## 基本配置

### 1. 配置 AI 模型

设置环境变量：

```bash
export MIDSCENE_AI_PROVIDER=openai
export MIDSCENE_AI_MODEL=gpt-4-vision-preview
export MIDSCENE_AI_API_KEY=your-api-key-here
```

或创建配置文件 `midscene.yml`：

```yaml
ai:
  provider: "openai"
  model: "gpt-4-vision-preview"
  api_key: "your-api-key-here"
```

### 2. 支持的 AI 提供商

- **OpenAI**: GPT-4V, GPT-4o
- **Anthropic**: Claude 3.5 Sonnet
- **阿里云**: Qwen2.5-VL
- **Google**: Gemini Pro Vision

## Web 自动化

### Selenium 示例

```python
import asyncio
from midscene import Agent
from midscene.web import SeleniumWebPage

async def web_automation():
    # 创建浏览器实例
    with SeleniumWebPage.create(headless=False) as page:
        agent = Agent(page)
        
        # 导航到网站
        await page.navigate_to("https://example.com")
        
        # 使用自然语言进行操作
        await agent.ai_action("点击登录按钮")
        await agent.ai_action("在用户名框输入 'demo@example.com'")
        await agent.ai_action("在密码框输入 'password123'")
        await agent.ai_action("点击提交按钮")
        
        # 数据提取
        user_info = await agent.ai_extract({
            "username": "用户名",
            "email": "邮箱地址"
        })
        print(f"用户信息: {user_info}")
        
        # 断言验证
        await agent.ai_assert("页面显示欢迎信息")

# 运行示例
asyncio.run(web_automation())
```

### Playwright 示例

```python
import asyncio
from midscene import Agent
from midscene.web import PlaywrightWebPage

async def playwright_automation():
    # 创建 Playwright 页面
    async with await PlaywrightWebPage.create() as page:
        agent = Agent(page)
        
        await page.navigate_to("https://playwright.dev")
        await agent.ai_action("点击文档链接")
        
        # 提取页面信息
        page_info = await agent.ai_extract({
            "title": "页面标题",
            "sections": ["主要章节列表"]
        })
        print(f"页面信息: {page_info}")

asyncio.run(playwright_automation())
```

## Android 自动化

```python
import asyncio
from midscene.android import AndroidAgent

async def android_automation():
    # 创建 Android Agent（自动检测设备）
    agent = await AndroidAgent.create()
    
    # 启动应用
    await agent.launch_app("com.android.settings")
    
    # 使用自然语言导航
    await agent.ai_action("点击WLAN设置")
    await agent.ai_action("滑动到底部")
    
    # 提取信息
    wifi_list = await agent.ai_extract({
        "networks": [
            {"name": "网络名称", "security": "安全类型"}
        ]
    })
    print(f"WiFi网络: {wifi_list}")
    
    # 返回
    await agent.back()

asyncio.run(android_automation())
```

## 命令行工具

### 运行 YAML 脚本

```bash
# 运行单个脚本
midscene run script.yaml

# 运行目录中的所有脚本
midscene run scripts/

# 使用配置文件
midscene run script.yaml --config midscene.yml

# 并发执行
midscene run scripts/ --concurrent 3

# Android 设备指定
midscene run android_script.yaml --device device_id
```

### 列出 Android 设备

```bash
midscene devices
```

### 初始化项目

```bash
midscene init my-project
cd my-project
```

## YAML 脚本格式

创建 `example.yaml`：

```yaml
# Web 自动化脚本
web:
  url: "https://example.com"
  browser: "chrome"
  headless: false

tasks:
  - name: "登录操作"
    steps:
      - action: "ai_action"
        prompt: "点击登录按钮"
      
      - action: "ai_action" 
        prompt: "输入用户名 'demo@example.com'"
      
      - action: "ai_action"
        prompt: "输入密码 'password123'"
      
      - action: "ai_action"
        prompt: "点击提交按钮"
  
  - name: "数据提取"
    steps:
      - action: "ai_extract"
        prompt:
          username: "用户名"
          email: "邮箱地址"
        save_to: "user_info"
  
  - name: "状态验证"
    steps:
      - action: "ai_assert"
        prompt: "页面显示欢迎信息"
```

## 核心概念

### Agent 系统

Agent 是自动化操作的核心控制器，协调 AI 模型与设备交互：

```python
from midscene import Agent
from midscene.web import SeleniumWebPage

page = SeleniumWebPage.create()
agent = Agent(page)
```

### AI 操作类型

1. **ai_action**: 执行自然语言描述的操作
2. **ai_locate**: 定位 UI 元素
3. **ai_extract**: 提取结构化数据
4. **ai_assert**: 验证页面状态

### 缓存机制

启用缓存可以提升重复执行的效率：

```python
from midscene.core import AgentOptions

options = AgentOptions(
    cache_id="my_automation",
    generate_report=True
)
agent = Agent(page, options)
```

## 最佳实践

### 1. 错误处理

```python
try:
    await agent.ai_action("点击不存在的按钮")
except Exception as e:
    print(f"操作失败: {e}")
```

### 2. 等待条件

```python
# 等待元素出现
await agent.ai_wait_for("登录成功页面出现", timeout_ms=10000)
```

### 3. 数据验证

```python
# 使用断言验证数据
user_data = await agent.ai_extract({"username": "用户名"})
assert user_data["username"], "用户名不能为空"
```

### 4. 截图和报告

```python
# 生成执行报告
options = AgentOptions(
    generate_report=True,
    report_file_name="automation_report"
)
```

## 故障排除

### 常见问题

1. **AI API 密钥未设置**
   ```
   ValueError: AI API key not configured
   ```
   解决：设置 `MIDSCENE_AI_API_KEY` 环境变量

2. **Chrome 浏览器未找到**
   ```
   WebDriverException: chrome not found
   ```
   解决：安装 Chrome 浏览器或指定 Chrome 路径

3. **Android 设备连接失败**
   ```
   RuntimeError: No Android devices found
   ```
   解决：确保设备已连接并启用 USB 调试

### 调试技巧

1. **启用详细日志**
   ```python
   from midscene.shared import setup_logger
   setup_logger(level="DEBUG")
   ```

2. **查看生成的报告**
   执行完成后检查 `./reports/` 目录中的 HTML 报告

3. **使用非无头模式**
   设置 `headless=False` 观察浏览器操作过程

## 下一步

- 查看 [API 文档](api.md) 了解详细接口
- 浏览 [示例集合](examples/) 学习更多用法
- 阅读 [配置指南](configuration.md) 了解高级配置