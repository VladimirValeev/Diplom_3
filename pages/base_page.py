from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.action_chains import ActionChains


class BasePage:
    def __init__(self, driver, timeout=20):
        self.driver = driver
        self.timeout = timeout

    def wait_visible(self, locator, timeout=None):
        t = timeout or self.timeout
        return WebDriverWait(self.driver, t).until(EC.visibility_of_element_located(locator))

    def wait_present(self, locator, timeout=None):
        t = timeout or self.timeout
        return WebDriverWait(self.driver, t).until(EC.presence_of_element_located(locator))

    def wait_clickable(self, locator, timeout=None):
        t = timeout or self.timeout
        return WebDriverWait(self.driver, t).until(EC.element_to_be_clickable(locator))

    def find_all(self, locator):
        return self.driver.find_elements(*locator)

    def scroll_into_view(self, element):
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center', inline:'center'});",
                element
            )
        except Exception:
            pass

    def js_click(self, element):
        self.driver.execute_script("arguments[0].click();", element)

    def click(self, locator, timeout=None):
        """
        ВАЖНО: НЕ начинаем с element_to_be_clickable — он часто флапает на React.
        Сначала presence -> scroll -> обычный click, и только если не вышло — JS click.
        """
        t = timeout or self.timeout
        el = self.wait_present(locator, timeout=t)
        self.scroll_into_view(el)

        try:
            el.click()
            return
        except (ElementClickInterceptedException, StaleElementReferenceException):
            pass
        except Exception:
            pass

        # пробуем дождаться кликабельности (если всё же надо)
        try:
            el = self.wait_clickable(locator, timeout=t)
            self.scroll_into_view(el)
            el.click()
            return
        except Exception:
            # последний шанс — JS click
            el = self.wait_present(locator, timeout=t)
            self.scroll_into_view(el)
            self.js_click(el)

    def drag_and_drop(self, source, target):
        """
        1) пробуем ActionChains
        2) если не сработало — HTML5 drag&drop через JS (гораздо стабильнее на этом проекте)
        """
        self.scroll_into_view(source)
        self.scroll_into_view(target)

        try:
            ActionChains(self.driver).drag_and_drop(source, target).perform()
            return
        except Exception:
            pass

        # HTML5 drag&drop через JS
        js = """
        const source = arguments[0];
        const target = arguments[1];

        const dataTransfer = new DataTransfer();

        function fire(type, elem) {
          const event = new DragEvent(type, { bubbles: true, cancelable: true, dataTransfer });
          elem.dispatchEvent(event);
        }

        fire('dragstart', source);
        fire('dragenter', target);
        fire('dragover', target);
        fire('drop', target);
        fire('dragend', source);
        """
        self.driver.execute_script(js, source, target)

    def wait_until_gone(self, locator, timeout=None):
        t = timeout or self.timeout
        return WebDriverWait(self.driver, t).until(EC.invisibility_of_element_located(locator))

    def safe_find_text_int(self, root, xpath):
        try:
            el = root.find_element("xpath", xpath)
            txt = (el.text or "").strip()
            return int(txt) if txt.isdigit() else 0
        except Exception:
            return 0
