"""
Basic usage examples for Midscene Python
"""

import asyncio
from midscene import Agent
from midscene.web import SeleniumWebPage
from midscene.android import AndroidAgent


async def web_automation_example():
    """Basic web automation example"""
    print("🌐 Web Automation Example")
    
    # Create web page instance
    with SeleniumWebPage.create(headless=False) as page:
        # Create agent
        agent = Agent(page)
        
        # Navigate to website
        await page.navigate_to("https://example.com")
        
        # Use AI to interact with the page
        await agent.ai_action("点击登录按钮")
        await agent.ai_action("在用户名输入框输入 'demo@example.com'")
        await agent.ai_action("在密码输入框输入 'password123'")
        await agent.ai_action("点击提交按钮")
        
        # Extract data using AI
        user_info = await agent.ai_extract({
            "username": "用户名",
            "email": "邮箱地址",
            "last_login": "最后登录时间"
        })
        print(f"提取的用户信息: {user_info}")
        
        # Assert page state
        await agent.ai_assert("页面显示欢迎信息")
        
        print("✅ Web automation completed successfully!")


async def android_automation_example():
    """Basic Android automation example"""
    print("📱 Android Automation Example")
    
    try:
        # Create Android agent
        agent = await AndroidAgent.create()
        
        # Launch app
        await agent.launch_app("com.android.settings")
        
        # Use AI to navigate
        await agent.ai_action("点击WLAN设置")
        await agent.ai_action("滑动到底部")
        
        # Extract information
        wifi_list = await agent.ai_extract({
            "available_networks": [
                {"name": "网络名称", "security": "安全类型", "signal": "信号强度"}
            ]
        })
        print(f"可用WiFi网络: {wifi_list}")
        
        # Go back
        await agent.back()
        
        print("✅ Android automation completed successfully!")
        
    except Exception as e:
        print(f"❌ Android automation failed: {e}")


async def playwright_example():
    """Playwright integration example"""
    print("🎭 Playwright Example")
    
    from midscene.web import PlaywrightWebPage
    
    # Create Playwright page
    async with await PlaywrightWebPage.create(headless=False) as page:
        agent = Agent(page)
        
        # Navigate and interact
        await page.navigate_to("https://playwright.dev")
        
        # Use AI for navigation
        await agent.ai_action("点击文档链接")
        await agent.ai_action("搜索 'getting started'")
        
        # Extract page information
        page_info = await agent.ai_extract({
            "title": "页面标题",
            "description": "页面描述",
            "sections": ["主要章节列表"]
        })
        print(f"页面信息: {page_info}")
        
        print("✅ Playwright example completed!")


async def main():
    """Run all examples"""
    print("🚀 Midscene Python Examples\n")
    
    # Web automation with Selenium
    await web_automation_example()
    print()
    
    # Playwright example
    await playwright_example()
    print()
    
    # Android automation (if device available)
    await android_automation_example()


if __name__ == "__main__":
    asyncio.run(main())