# Midscene Python
[English](README.md) | [简体中文](README.zh.md)  
[![zread](https://img.shields.io/badge/Ask_Zread-_.svg?style=flat&color=00b0aa&labelColor=000000&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuOTYxNTYgMS42MDAxSDIuMjQxNTZDMS44ODgxIDEuNjAwMSAxLjYwMTU2IDEuODg2NjQgMS42MDE1NiAyLjI0MDFWNC45NjAxQzEuNjAxNTYgNS4zMTM1NiAxLjg4ODEgNS42MDAxIDIuMjQxNTYgNS42MDAxSDQuOTYxNTZDNS4zMTUwMiA1LjYwMDEgNS42MDE1NiA1LjMxMzU2IDUuNjAxNTYgNC45NjAxVjIuMjQwMUM1LjYwMTU2IDEuODg2NjQgNS4zMTUwMiAxLjYwMDEgNC45NjE1NiAxLjYwMDFaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00Ljk2MTU2IDEwLjM5OTlIMi4yNDE1NkMxLjg4ODEgMTAuMzk5OSAxLjYwMTU2IDEwLjY4NjQgMS42MDE1NiAxMS4wMzk5VjEzLjc1OTlDMS42MDE1NiAxNC4xMTM0IDEuODg4MSAxNC4zOTk5IDIuMjQxNTYgMTQuMzk5OUg0Ljk2MTU2QzUuMzE1MDIgMTQuMzk5OSA1LjYwMTU2IDE0LjExMzQgNS42MDE1NiAxMy43NTk5VjExLjAzOTlDNS42MDE1NiAxMC42ODY0IDUuMzE1MDIgMTAuMzk5OSA0Ljk2MTU2IDEwLjM5OTlaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik0xMy43NTg0IDEuNjAwMUgxMS4wMzg0QzEwLjY4NSAxLjYwMDEgMTAuMzk4NCAxLjg4NjY0IDEwLjM5ODQgMi4yNDAxVjQuOTYwMUMxMC4zOTg0IDUuMzEzNTYgMTAuNjg1IDUuNjAwMSAxMS4wMzg0IDUuNjAwMUgxMy43NTg0QzE0LjExMTkgNS42MDAxIDE0LjM5ODQgNS4zMTM1NiAxNC4zOTg0IDQuOTYwMVYyLjI0MDFDMTQuMzk4NCAxLjg4NjY0IDE0LjExMTkgMS42MDAxIDEzLjc1ODQgMS42MDAxWiIgZmlsbD0iI2ZmZiIvPgo8cGF0aCBkPSJNNCAxMkwxMiA0TDQgMTJaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00IDEyTDEyIDQiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K&logoColor=ffffff)](https://zread.ai/Python51888/Midscene-Python)

Midscene Python is an AI-based automation framework that supports UI automation operations on Web and Android platforms.

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
