<div align="center">
# Midscene Python
[English](README.md) | [中文](README.zh.md)

Midscene Python is an AI-based automation framework that supports UI automation operations on Web and Android platforms.
</div>
## Overview

Midscene Python provides comprehensive UI automation capabilities with the following core features:

- **Natural Language Driven**: Describe automation tasks using natural language
- **Multi-platform Support**: Supports Web (Selenium/Playwright) and Android (ADB)
- **AI Model Integration**: Supports multiple vision-language models such as GPT-4V, Qwen2.5-VL, and Gemini
- **Visual Debugging**: Provides detailed execution reports and debugging information
- **Caching Mechanism**: Intelligent caching to improve execution efficiency

## Project Architecture

```
midscene-python/
├── midscene/                    # Core framework
│   ├── core/                    # Core framework
│   │   ├── agent/              # Agent system
│   │   ├── insight/            # AI inference engine
│   │   ├── ai_model/           # AI model integration
│   │   ├── yaml/               # YAML script executor
│   │   └── types.py            # Core type definitions
│   ├── web/                     # Web integration
│   │   ├── selenium/           # Selenium integration
│   │   ├── playwright/         # Playwright integration
│   │   └── bridge/             # Bridge mode
│   ├── android/                 # Android integration
│   │   ├── device.py           # Device management
│   │   └── agent.py            # Android Agent
│   ├── cli/                     # Command line tools
│   ├── mcp/                     # MCP protocol support
│   ├── shared/                 # Shared utilities
│   └── visualizer/             # Visual reports
├── examples/                   # Example code
├── tests/                      # Test cases
└── docs/                       # Documentation
```

## Tech Stack

- **Python 3.9+**: Core runtime environment
- **Pydantic**: Data validation and serialization
- **Selenium/Playwright**: Web automation
- **OpenCV/Pillow**: Image processing
- **HTTPX/AIOHTTP**: HTTP client
- **Typer**: CLI framework
- **Loguru**: Logging

## Quick Start

### Installation

```bash
pip install midscene-python
```

### Basic Usage

```python
from midscene import Agent
from midscene.web import SeleniumWebPage

# Create a Web Agent
with SeleniumWebPage.create() as page:
    agent = Agent(page)
    
    # Perform automation operations using natural language
    await agent.ai_action("Click the login button")
    await agent.ai_action("Enter username 'test@example.com'")
    await agent.ai_action("Enter password 'password123'")
    await agent.ai_action("Click the submit button")
    
    # Data extraction
    user_info = await agent.ai_extract("Extract user personal information")
    
    # Assertion verification
    await agent.ai_assert("Page displays welcome message")
```

## Key Features

### 🤖 AI-Driven Automation

Describe operations using natural language, and AI automatically understands and executes:

```python
await agent.ai_action("Enter 'Python tutorial' in the search box and search")
```

### 🔍 Intelligent Element Location

Supports multiple location strategies and automatically selects the optimal solution:

```python
element = await agent.ai_locate("Login button")
```

### 📊 Data Extraction

Extract structured data from the page:

```python
products = await agent.ai_extract({
    "products": [
        {"name": "Product Name", "price": "Price", "rating": "Rating"}
    ]
})
```

### ✅ Intelligent Assertions

AI understands page state and performs intelligent assertions:

```python
await agent.ai_assert("User has successfully logged in")
```

### 📝 Credits

Thanks to Midscene Project: https://github.com/web-infra-dev/midscene for inspiration and technical references 

## License

MIT License
