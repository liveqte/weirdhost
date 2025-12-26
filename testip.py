import os
from playwright.sync_api import sync_playwright

def main():
    # 从环境变量读取代理（你可以改成写死）
    chrome_proxy = os.getenv("CHROME_PROXY")

    if not chrome_proxy:
        print("❌ 未设置 CHROME_PROXY 环境变量")
        return

    with sync_playwright() as p:
        print(f"使用代理: {chrome_proxy}")

        browser = p.chromium.launch(
            headless=True,
            proxy={"server": chrome_proxy}
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
            )
        )

        page = context.new_page()

        print("打开 https://cip.cc ...")
        page.goto("https://cip.cc", timeout=60000)

        # 截图保存到脚本所在目录
        screenshot_path = os.path.join(os.getcwd(), "testip.png")
        page.screenshot(path=screenshot_path, full_page=True)

        print(f"截图已保存: {screenshot_path}")

        browser.close()

if __name__ == "__main__":
    main()
