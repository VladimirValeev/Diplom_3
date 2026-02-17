import allure

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

    # ---------- wait helpers ----------

    def _wait(self, timeout=None):
        return WebDriverWait(self.driver, timeout or self.timeout)

    def wait_visible(self, locator, timeout=None):
        with allure.step(f"Ожидать видимость: {locator}"):
            return self._wait(timeout).until(EC.visibility_of_element_located(locator))

    def wait_present(self, locator, timeout=None):
        with allure.step(f"Ожидать присутствие: {locator}"):
            return self._wait(timeout).until(EC.presence_of_element_located(locator))

    def wait_clickable(self, locator, timeout=None):
        with allure.step(f"Ожидать кликабельность: {locator}"):
            return self._wait(timeout).until(EC.element_to_be_clickable(locator))

    def wait_all_present(self, locator, timeout=None):
        with allure.step(f"Ожидать список элементов: {locator}"):
            return self._wait(timeout).until(EC.presence_of_all_elements_located(locator))

    def wait_until_gone(self, locator, timeout=None):
        with allure.step(f"Ожидать исчезновение: {locator}"):
            return self._wait(timeout).until(EC.invisibility_of_element_located(locator))

    # ---------- text helpers ----------

    def text_of(self, locator, timeout=None) -> str:
        """
        Нужен для FeedPage (и вообще удобен в проекте).
        Возвращает .text видимого элемента, с trim.
        """
        with allure.step(f"Получить текст элемента: {locator}"):
            el = self.wait_visible(locator, timeout=timeout)
            return (el.text or "").strip()

    # ---------- checks ----------

    def is_visible(self, locator, timeout=3):
        try:
            self.wait_visible(locator, timeout=timeout)
            return True
        except Exception:
            return False

    def is_invisible(self, locator, timeout=3):
        try:
            self.wait_until_gone(locator, timeout=timeout)
            return True
        except Exception:
            return False

    # ---------- dom helpers ----------

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
        presence -> scroll -> обычный click
        если не вышло -> clickable -> click
        если не вышло -> JS click
        """
        with allure.step(f"Клик: {locator}"):
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

            try:
                el = self.wait_clickable(locator, timeout=t)
                self.scroll_into_view(el)
                el.click()
                return
            except Exception:
                el = self.wait_present(locator, timeout=t)
                self.scroll_into_view(el)
                self.js_click(el)

    # ---------- localStorage / refresh ----------

    def set_local_storage_item(self, key: str, value: str):
        with allure.step(f"localStorage set: {key}"):
            self.driver.execute_script(
                "window.localStorage.setItem(arguments[0], arguments[1]);",
                key, value
            )

    def refresh(self):
        with allure.step("Обновить страницу"):
            self.driver.refresh()

    # ---------- DnD robust ----------

    def _dnd_actionchains(self, src, dst):
        ActionChains(self.driver).drag_and_drop(src, dst).perform()

    def _dnd_clickhold_offset(self, src, dst):
        ActionChains(self.driver)\
            .move_to_element(src)\
            .pause(0.1)\
            .click_and_hold(src)\
            .pause(0.2)\
            .move_to_element_with_offset(dst, 0, 40)\
            .pause(0.2)\
            .release()\
            .perform()

    def _dnd_html5_js(self, src, dst):
        script = r"""
            const source = arguments[0];
            const target = arguments[1];

            function makeDataTransfer(){
              try { return new DataTransfer(); }
              catch(e) {
                return {
                  data: {},
                  setData: function(k,v){ this.data[k]=v; },
                  getData: function(k){ return this.data[k]; },
                  clearData: function(){ this.data = {}; },
                  dropEffect: 'move',
                  effectAllowed: 'all',
                  files: [],
                  items: [],
                  types: []
                };
              }
            }

            function fire(type, elem, dt){
              let evt;
              try {
                evt = new DragEvent(type, { bubbles:true, cancelable:true, dataTransfer: dt });
              } catch(e) {
                evt = document.createEvent('CustomEvent');
                evt.initCustomEvent(type, true, true, null);
                evt.dataTransfer = dt;
              }
              elem.dispatchEvent(evt);
            }

            const dt = makeDataTransfer();

            try { source.scrollIntoView({block:'center'}); } catch(e){}
            try { target.scrollIntoView({block:'center'}); } catch(e){}

            fire('pointerdown', source, dt);
            fire('mousedown', source, dt);

            fire('dragstart', source, dt);
            fire('dragenter', target, dt);
            fire('dragover', target, dt);
            fire('drop', target, dt);
            fire('dragend', source, dt);

            fire('mouseup', target, dt);
        """
        self.driver.execute_script(script, src, dst)

    def drag_and_drop_robust(self, source, target):
        with allure.step("Drag&Drop (robust)"):
            self.scroll_into_view(source)
            self.scroll_into_view(target)

            tries = [
                ("actionchains", self._dnd_actionchains),
                ("clickhold_offset", self._dnd_clickhold_offset),
                ("html5_js", self._dnd_html5_js),
            ]
            last = None
            for _, fn in tries:
                try:
                    fn(source, target)
                    return
                except Exception as e:
                    last = e
            raise last if last else TimeoutException("DnD failed")

    # !!! ВАЖНО: совместимость со старым кодом !!!
    def drag_and_drop(self, source, target):
        return self.drag_and_drop_robust(source, target)
