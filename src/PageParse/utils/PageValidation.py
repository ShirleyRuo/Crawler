import time
from ...Config.Config import config
from ...utils.Logger import Logger

logger = Logger(config.log_dir).get_logger(__name__)

def validation(url : str) -> str:
    '''
    使用selenium获取网页源代码并将Cookie同步到config.headers
    '''
    try:
        from selenium import webdriver
        from selenium.webdriver import ChromeOptions
        options = ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(f'user-agent={config.headers["User-Agent"]}')
        options.add_argument('--incognito')
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.get(url=url)
        time.sleep(20)
        html_text = driver.page_source
        config.cookie = driver.get_cookies()
        driver.quit()
        return html_text
    except Exception as e:
        logger.error(f'请安装Chrome浏览器并配置环境变量,{e}')
        return ""