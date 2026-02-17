import logging
import uuid

import pytest
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from pages.main_page import MainPage


logger = logging.getLogger(__name__)


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


def pytest_configure(config):
    # Настраиваем логирование один раз на сессию pytest
    # (и убираем print'ы по требованию ревью)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


@pytest.fixture
def base_url(request) -> str:
    return request.config.getoption("--base-url")


@pytest.fixture(params=["chrome", "firefox"])
def driver(request, base_url):
    headless = request.config.getoption("--headless")
    browser = request.param

    logger.info("UI tests config: BASE_URL=%s BROWSER=%s HEADLESS=%s", base_url, browser, headless)

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

    # По ревью: никаких локаторов в conftest.
    # Ожидание готовности приложения делаем методом Page Object.
    MainPage(drv).wait_app_ready(timeout=120)

    yield drv
    drv.quit()


@pytest.fixture
def registered_tokens():
    """
    По ревью: из tests/ выносим регистрацию/токены.
    Возвращает (accessToken, refreshToken).
    """
    api_base = "https://stellarburgers.education-services.ru"
    uniq = uuid.uuid4().hex[:10]
    payload = {
        "email": f"vova_{uniq}@test.ru",
        "password": "Passw0rd!",
        "name": f"Vova_{uniq}",
    }

    r = requests.post(f"{api_base}/api/auth/register", json=payload, timeout=20)
    r.raise_for_status()
    data = r.json()

    return data["accessToken"], data["refreshToken"]
