import pytest
from selenium import webdriver

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def pytest_addoption(parser):
    parser.addoption(
        "--base-url",
        action="store",
        default="https://stellarburgers.education-services.ru/",
        help="Base URL for UI tests",
    )
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run browsers in headless mode",
    )


@pytest.fixture(params=["chrome", "firefox"])
def driver(request):
    base_url = request.config.getoption("--base-url")
    headless = request.config.getoption("--headless")
    browser = request.param

    print(f"\nBASE_URL = {base_url}\nBROWSER  = {browser}\nHEADLESS = {headless}\n")

    if browser == "chrome":
        options = ChromeOptions()
        # eager — чтобы не висеть на полной загрузке (у stellarburgers бывает долгий "load")
        options.page_load_strategy = "eager"
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        drv = webdriver.Chrome(options=options)

    elif browser == "firefox":
        options = FirefoxOptions()
        options.page_load_strategy = "eager"
        if headless:
            options.add_argument("-headless")
        drv = webdriver.Firefox(options=options)
        drv.set_window_size(1920, 1080)

    else:
        raise ValueError(f"Unsupported browser: {browser}")

    drv.set_page_load_timeout(60)
    drv.implicitly_wait(0)

    # ВАЖНО: если get() таймаутится — НЕ падаем, часто страница уже открыта достаточно для тестов
    try:
        drv.get(base_url)
    except TimeoutException:
        pass

    wait = WebDriverWait(drv, 120)

    # 1) Дождаться, что браузер вообще отдал DOM
    wait.until(lambda d: d.execute_script("return document.readyState") in ("interactive", "complete"))

    # 2) Дождаться, что React/страница реально показала хоть что-то ключевое
    anchors = EC.any_of(
        EC.presence_of_element_located((By.XPATH, "//p[contains(., 'Конструктор')]")),
        EC.presence_of_element_located((By.XPATH, "//p[contains(., 'Лента заказов')]")),
        EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Соберите бургер')]")),
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.BurgerIngredient_ingredient__1TVf6")),
    )
    wait.until(anchors)

    yield drv
    drv.quit()
