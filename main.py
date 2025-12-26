import os
import time
from playwright.sync_api import sync_playwright, Cookie, TimeoutError as PlaywrightTimeoutError
from typing import Optional
import re
import random

def solve_turnstile_sync(page, logger=None):
    """
    同步版本 - 使用 Playwright 解决 Cloudflare Turnstile 验证
    
    Args:
        page: Playwright 同步版本的 page 对象
        logger: 日志记录器，如果为 None 则使用 print
    """
    
    def log(msg, level="debug"):
        if logger:
            if level == "debug":
                logger.debug(msg)
            elif level == "info":
                logger.info(msg)
        else:
            print(f"[{level.upper()}] {msg}")
    
    def check_element(name, element):
        if not element:
            log(f"❌ 元素未找到: {name}", "info")
            raise Exception(f"Element not found: {name}")
        log(f"✅ 找到元素: {name}", "debug")
        return True
    
    def wait_for(min_seconds, max_seconds=None):
        if max_seconds:
            wait_time = random.uniform(min_seconds, max_seconds)
        else:
            wait_time = min_seconds
        log(f"等待 {wait_time:.1f} 秒", "debug")
        time.sleep(wait_time)
    
    def capture_screenshot(filename="screenshot.png"):
        try:
            page.screenshot(path=filename, full_page=True)
            log(f"截图保存为: {filename}", "debug")
        except Exception as e:
            log(f"截图失败: {str(e)}", "debug")
    
    log("等待 Turnstile 验证", "info")
    
    # 等待随机时间
    wait_for(15, 30)
    capture_screenshot("cf_begin.png")
    # 查找 iframe - Cloudflare Turnstile iframe 通常有特定的属性
    try:
        # 方法1: 查找包含 Cloudflare Turnstile 的 iframe
        iframe_selector = "iframe[src*='cloudflare'], iframe[title*='Cloudflare'], iframe[title*='challenge']"
        
        # 等待 iframe 出现
        log("查找 Cloudflare Turnstile iframe", "debug")
        
        # 等待页面加载完成 - 同步版本使用 wait_for_load_state()
        page.wait_for_load_state("networkidle")
        
        # 查找所有可能的 iframe - 同步版本使用 query_selector_all()
        iframes = page.query_selector_all("iframe")
        log(f"找到 {len(iframes)} 个 iframe", "debug")
        
        target_iframe = None
        for iframe in iframes:
            src = iframe.get_attribute("src") or ""
            title = iframe.get_attribute("title") or ""
            if "cloudflare" in src.lower() or "cloudflare" in title.lower() or "challenge" in title.lower():
                target_iframe = iframe
                log(f"找到目标 iframe: src={src}, title={title}", "debug")
                break
        
        if not target_iframe:
            # 尝试其他选择器
            target_iframe = page.query_selector(iframe_selector)
        
        check_element("Cloudflare Turnstile iframe", target_iframe)
        
        # 切换到 iframe 上下文 - 同步版本
        frame = target_iframe.content_frame()
        check_element("iframe content frame", frame)
        
        # 在 iframe 内查找 checkbox
        checkbox_selectors = [
            'input[type="checkbox"]',
            '.challenge-container input',
            '#challenge-stage input',
            'label input',
            'div[role="checkbox"]',
            '[data-testid="cf-challenge-widget"] input'
        ]
        
        checkbox = None
        for selector in checkbox_selectors:
            checkbox = frame.query_selector(selector)
            if checkbox:
                log(f"使用选择器找到 checkbox: {selector}", "debug")
                break
        
        # 如果没找到，尝试通过 XPath 查找
        if not checkbox:
            checkbox = frame.query_selector('xpath=//label/input')
            if checkbox:
                log("使用 XPath 找到 checkbox", "debug")
        
        check_element("Turnstile checkbox", checkbox)
        
        # 获取复选框位置和大小 - 同步版本
        box = checkbox.bounding_box()
        if box:
            # 计算点击位置（稍微偏移中心）
            x = box['x'] + box['width'] / 2 + random.randint(5, 8)
            y = box['y'] + box['height'] / 2 + random.randint(5, 8)
            
            log(f"点击位置: x={x}, y={y}", "debug")
            
            # 点击复选框 - 同步版本
            page.mouse.click(x, y)
            log("✅ 已点击 Turnstile 验证框", "info")
        else:
            # 如果无法获取边界框，直接点击元素
            checkbox.click()
            log("✅ 已直接点击 Turnstile 验证框", "info")
        
        # 等待验证完成
        wait_for(10, 12)
        
        # 检查是否验证成功
        wait_for(3, 5)
        
        # 尝试截图
        capture_screenshot("cf_result.png")
        
        log("Turnstile 验证处理完成", "info")
        return True
        
    except Exception as e:
        log(f"处理 Turnstile 验证时出错: {str(e)}", "info")
        
        # 出错时截图
        try:
            capture_screenshot("cf_error.png")
        except:
            pass
        return False
        
def is_valid_proxy(proxy: str) -> bool:
    """
    校验代理格式是否合法，例如:
    socks5://domain.com:1080
    http://1.2.3.4:8080
    """
    pattern = re.compile(
        r'^(http|https|socks4|socks5)://'   # 协议
        r'([a-zA-Z0-9.-]+|\d{1,3}(\.\d{1,3}){3})'  # 域名或 IP
        r':(\d+)$'  # 端口
    )
    return bool(pattern.match(proxy))

def add_server_time():
    """
    尝试登录 hub.weirdhost.xyz 并点击 "시간 추가" 按钮。
    优先使用 REMEMBER_WEB_COOKIE 进行会话登录，如果不存在则回退到邮箱密码登录。
    此函数设计为每次GitHub Actions运行时执行一次。
    """
    # 从环境变量获取登录凭据
    remember_web_cookie = os.environ.get('REMEMBER_WEB_COOKIE')
    pterodactyl_email = os.environ.get('PTERODACTYL_EMAIL')
    pterodactyl_password = os.environ.get('PTERODACTYL_PASSWORD')
    server_url=os.environ.get('WEIRDHOST_SERVER_URLS')
    chrome_proxy = os.environ.get("CHROME_PROXY")
    
    # 检查是否提供了任何登录凭据
    if not (remember_web_cookie or (pterodactyl_email and pterodactyl_password)):
        print("错误: 缺少登录凭据。请设置 REMEMBER_WEB_COOKIE 或 PTERODACTYL_EMAIL 和 PTERODACTYL_PASSWORD 环境变量。")
        return False

    with sync_playwright() as p:

        if not is_valid_proxy(chrome_proxy):
            raise ValueError(f"代理格式不合法: {chrome_proxy}")
        
        browser = p.chromium.launch(
            headless=False,
            proxy={"server": chrome_proxy}
        )
        
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.0 Safari/605.1.15"
            ),
            viewport={"width": 1366, "height": 768},
            timezone_id="America/Los_Angeles"
        )
        
        page = context.new_page()
        # 增加默认超时时间到90秒，以应对网络波动和慢加载
        page.set_default_timeout(90000)

        try:
            # --- 方案一：优先尝试使用 Cookie 会话登录 ---
            if remember_web_cookie:
                print("检测到 REMEMBER_WEB_COOKIE，尝试使用 Cookie 登录...")
                session_cookie = {
                    'name': 'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d',
                    'value': remember_web_cookie,
                    'domain': 'hub.weirdhost.xyz',  # 已更新为新的域名
                    'path': '/',
                    'expires': int(time.time()) + 3600 * 24 * 365, # 设置一个较长的过期时间
                    'httpOnly': True,
                    'secure': True,
                    'sameSite': 'Lax'
                }
                page.context.add_cookies([session_cookie])
                print(f"已设置 Cookie。正在访问目标服务器页面: {server_url}")
                
                try:
                    # 使用 'domcontentloaded' 以加快页面加载判断，然后依赖选择器等待确保元素加载
                    page.goto(server_url, wait_until="domcontentloaded", timeout=90000)
                except PlaywrightTimeoutError:
                    print(f"页面加载超时（90秒）。")
                    page.screenshot(path="goto_timeout_error.png")
                
                # 检查是否因 Cookie 无效被重定向到登录页
                if "login" in page.url or "auth" in page.url:
                    print("Cookie 登录失败或会话已过期，将回退到邮箱密码登录。")
                    page.context.clear_cookies()
                    remember_web_cookie = None # 标记 Cookie 登录失败，以便执行下一步
                else:
                    print("Cookie 登录成功，已进入服务器页面。")

            # --- 方案二：如果 Cookie 方案失败或未提供，则使用邮箱密码登录 ---
            if not remember_web_cookie:
                if not (pterodactyl_email and pterodactyl_password):
                    print("错误: Cookie 无效，且未提供 PTERODACTYL_EMAIL 或 PTERODACTYL_PASSWORD。无法登录。")
                    browser.close()
                    return False

                login_url = "https://hub.weirdhost.xyz/auth/login" # 已更新为新的登录URL
                print(f"正在访问登录页面: {login_url}")
                page.goto(login_url, wait_until="domcontentloaded", timeout=90000)

                # 定义选择器 (Pterodactyl 面板通用，无需修改)
                email_selector = 'input[name="username"]' 
                password_selector = 'input[name="password"]'
                login_button_selector = 'button[type="submit"]'

                print("等待登录表单元素加载...")
                page.wait_for_selector(email_selector)
                page.wait_for_selector(password_selector)
                page.wait_for_selector(login_button_selector)

                print("正在填写邮箱和密码...")
                page.fill(email_selector, pterodactyl_email)
                page.fill(password_selector, pterodactyl_password)

                print("正在点击登录按钮...")
                with page.expect_navigation(wait_until="domcontentloaded", timeout=60000):
                    page.click(login_button_selector)

                # 检查登录后是否成功
                if "login" in page.url or "auth" in page.url:
                    error_text = page.locator('.alert.alert-danger').inner_text().strip() if page.locator('.alert.alert-danger').count() > 0 else "未知错误，URL仍在登录页。"
                    print(f"邮箱密码登录失败: {error_text}")
                    page.screenshot(path="login_fail_error.png")
                    browser.close()
                    return False
                else:
                    print("邮箱密码登录成功。")

            # --- 确保当前位于正确的服务器页面 ---
            if page.url != server_url:
                print(f"当前不在目标服务器页面，正在导航至: {server_url}")
                page.goto(server_url, wait_until="domcontentloaded", timeout=90000)
                if "login" in page.url:
                    print("导航失败，会话可能已失效，需要重新登录。")
                    page.screenshot(path="server_page_nav_fail.png")
                    browser.close()
                    return False
            success = solve_turnstile_sync(page)
            if success:
                print("验证成功!")
            else:
                print("验证失败!")
                exit(1)
            # --- 核心操作：查找并点击 "시간 추가" 按钮 ---
            add_button_selector = 'button:has-text("시간 추가")' # 已更新为新的按钮文本
            print(f"正在查找并等待 '{add_button_selector}' 按钮...")

            try:
                # 等待按钮变为可见且可点击
                add_button = page.locator(add_button_selector)
                add_button.wait_for(state='visible', timeout=30000)
                add_button.click()
                print("成功点击 '시간 추가' 按钮。")
                time.sleep(5) # 等待5秒，确保操作在服务器端生效
                print("任务完成。")
                browser.close()
                return True
            except PlaywrightTimeoutError:
                print(f"错误: 在30秒内未找到或 '시간 추가' 按钮不可见/不可点击。")
                page.screenshot(path="add_6h_button_not_found.png")
                browser.close()
                return False

        except Exception as e:
            print(f"执行过程中发生未知错误: {e}")
            # 发生任何异常时都截图，以便调试
            page.screenshot(path="general_error.png")
            browser.close()
            return False

if __name__ == "__main__":
    print("开始执行添加服务器时间任务...")
    success = add_server_time()
    if success:
        print("任务执行成功。")
        exit(0)
    else:
        print("任务执行失败。")
        exit(1)
