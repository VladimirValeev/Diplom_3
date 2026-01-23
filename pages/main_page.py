import time
import allure

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

from pages.base_page import BasePage


class MainPage(BasePage):
    # Навигация
    LINK_CONSTRUCTOR = (By.CSS_SELECTOR, "a[href='/']")
    LINK_FEED = (By.CSS_SELECTOR, "a[href='/feed']")

    # Табы
    TAB_FILLINGS = (By.XPATH, "//span[contains(., 'Начинки')]/parent::*")

    # Карточки ингредиентов (общий)
    INGREDIENT_CARDS = (By.CSS_SELECTOR, "a.BurgerIngredient_ingredient__1TVf6")

    # Карточки ИМЕННО в блоке "Начинки"
    FILLINGS_CARDS = (
        By.XPATH,
        "//h2[contains(., 'Начинки')]/following-sibling::ul//a[contains(@class,'BurgerIngredient_ingredient')]"
    )

    # Имя ингредиента в карточке
    CARD_NAME = (By.CSS_SELECTOR, "p.BurgerIngredient_ingredient__text__yp3dH, p[class*='ingredient__text']")

    # Счётчик на карточке
    CARD_COUNTER = (By.XPATH, ".//p[contains(@class,'counter_counter__num')]")

    # Оверлей модалки (иногда мешает кликам)
    MODAL_OVERLAY = (By.CSS_SELECTOR, "div.Modal_modal_overlay__x2ZCr")

    # Конструктор (drop зоны)
    CONSTRUCTOR_SECTION = (By.CSS_SELECTOR, "section[class*='BurgerConstructor']")
    # Самая стабильная drop-зона для Firefox/React: список конструктора (ul)
    CONSTRUCTOR_LIST = (By.CSS_SELECTOR, "ul[class*='BurgerConstructor_constructor__list']")
    # Плейсхолдер “Перетащите начинку сюда” (иногда полезен как фолбек)
    DROP_FILLING_PLACEHOLDER = (By.XPATH, "//*[contains(., 'Перетащите начинку сюда')][1]")

    @allure.step("Дождаться загрузки главной страницы")
    def wait_page_loaded(self, timeout=60):
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.find_elements(*self.LINK_CONSTRUCTOR) or d.find_elements(*self.LINK_FEED)
        )
        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(self.INGREDIENT_CARDS)
        )
        return self

    def close_overlay_if_present(self):
        try:
            if self.find_all(self.MODAL_OVERLAY):
                self.driver.switch_to.active_element.send_keys("\uE00C")  # ESC
        except Exception:
            pass

    @allure.step("Перейти в 'Конструктор'")
    def click_constructor(self):
        self.close_overlay_if_present()
        self.click(self.LINK_CONSTRUCTOR, timeout=30)
        return self

    @allure.step("Перейти в 'Лента заказов'")
    def click_feed(self):
        self.close_overlay_if_present()
        self.click(self.LINK_FEED, timeout=30)
        return self

    @allure.step("Открыть первый ингредиент")
    def open_first_ingredient(self):
        self.close_overlay_if_present()
        cards = WebDriverWait(self.driver, 40).until(
            EC.presence_of_all_elements_located(self.INGREDIENT_CARDS)
        )
        first = cards[0]
        self.scroll_into_view(first)
        try:
            first.click()
        except Exception:
            self.js_click(first)
        return self

    def _get_counter_from_card(self, card):
        try:
            el = card.find_elements(*self.CARD_COUNTER)
            if not el:
                return 0
            txt = (el[0].text or "").strip()
            return int(txt) if txt.isdigit() else 0
        except Exception:
            return 0

    def _get_card_name(self, card):
        try:
            name_el = card.find_elements(*self.CARD_NAME)
            if name_el:
                return (name_el[0].text or "").strip()
        except Exception:
            pass
        return (card.text or "").split("\n")[0].strip()

    def _find_filling_card_by_name(self, name, timeout=30):
        end = time.time() + timeout
        last_err = None
        while time.time() < end:
            try:
                cards = self.driver.find_elements(*self.FILLINGS_CARDS)
                for c in cards:
                    try:
                        if self._get_card_name(c) == name:
                            return c
                    except StaleElementReferenceException:
                        continue
            except Exception as e:
                last_err = e
            time.sleep(0.2)
        raise TimeoutException(f"Не нашёл карточку начинки по имени '{name}'. Последняя ошибка: {last_err}")

    def _get_drop_for_filling(self, timeout=40):
        """
        В Firefox/React надёжнее всего drop'ать в UL списка конструктора.
        Плейсхолдер оставляем как fallback.
        """
        self.close_overlay_if_present()
        wait = WebDriverWait(self.driver, timeout)

        # 1) UL списка конструктора — лучший drop target
        try:
            ul = wait.until(EC.presence_of_element_located(self.CONSTRUCTOR_LIST))
            self.scroll_into_view(ul)
            return ul
        except Exception:
            pass

        # 2) fallback: плейсхолдер текста
        try:
            ph = wait.until(EC.presence_of_element_located(self.DROP_FILLING_PLACEHOLDER))
            self.scroll_into_view(ph)
            return ph
        except Exception:
            pass

        # 3) fallback: секция конструктора
        try:
            sec = wait.until(EC.presence_of_element_located(self.CONSTRUCTOR_SECTION))
            self.scroll_into_view(sec)
            return sec
        except Exception:
            pass

        raise TimeoutException("Не удалось найти drop-зону для начинки (ul/placeholder/section).")

    # ---------- DRAG & DROP стратегии ----------

    def _dnd_actionchains(self, src, dst):
        ActionChains(self.driver).move_to_element(src).pause(0.1).click_and_hold(src).pause(0.2).move_to_element(dst).pause(0.2).release().perform()

    def _dnd_clickhold_offset(self, src, dst):
        ActionChains(self.driver).click_and_hold(src).pause(0.2).move_to_element_with_offset(dst, 0, 40).pause(0.2).release().perform()

    def _dnd_html5_js(self, src, dst):
        """
        Максимально совместимый HTML5 DnD.
        В Firefox new DragEvent / new DataTransfer могут быть капризны → есть fallback.
        """
        script = r"""
            const source = arguments[0];
            const target = arguments[1];

            function makeDataTransfer(){
              try {
                return new DataTransfer();
              } catch(e) {
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
                evt = new DragEvent(type, { bubbles: true, cancelable: true, dataTransfer: dt });
              } catch(e) {
                evt = document.createEvent('CustomEvent');
                evt.initCustomEvent(type, true, true, null);
                evt.dataTransfer = dt;
              }
              elem.dispatchEvent(evt);
            }

            const dt = makeDataTransfer();

            // Небольшая "разминка" для React обработчиков
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

    def _drag_and_drop_robust(self, src, dst):
        # Важный порядок: сначала простые, потом JS (он самый сильный, но пусть будет последним)
        tries = [
            ("actionchains", self._dnd_actionchains),
            ("clickhold_offset", self._dnd_clickhold_offset),
            ("html5_js", self._dnd_html5_js),
        ]
        last = None
        for name, fn in tries:
            try:
                fn(src, dst)
                return name
            except Exception as e:
                last = e
                continue
        raise last

    # ---------- основной сценарий теста ----------

    @allure.step("Добавить начинку и дождаться увеличения счётчика")
    def add_filling_and_wait_counter(self, timeout=60):
        self.close_overlay_if_present()

        # гарантированно на конструкторе
        self.click_constructor()
        self.wait_page_loaded(timeout=60)

        # открыть таб "Начинки"
        self.click(self.TAB_FILLINGS, timeout=30)

        # получить первую карточку именно из секции "Начинки"
        cards = WebDriverWait(self.driver, 40).until(
            EC.presence_of_all_elements_located(self.FILLINGS_CARDS)
        )
        card = cards[0]
        self.scroll_into_view(card)

        name = self._get_card_name(card)
        before = self._get_counter_from_card(card)

        drop = self._get_drop_for_filling(timeout=40)

        # Пытаемся сделать DnD. В Firefox иногда нужен повтор.
        self._drag_and_drop_robust(card, drop)

        w = WebDriverWait(self.driver, timeout)

        def counter_value():
            c = self._find_filling_card_by_name(name, timeout=10)
            return self._get_counter_from_card(c)

        # Быстрая проверка: если за 6 сек не вырос — повторим DnD (особенно для Firefox)
        try:
            WebDriverWait(self.driver, 6).until(lambda d: counter_value() == before + 1)
        except Exception:
            # повтор №1 — принудительно через JS (самый надёжный)
            try:
                card2 = self._find_filling_card_by_name(name, timeout=10)
                drop2 = self._get_drop_for_filling(timeout=20)
                self._dnd_html5_js(card2, drop2)
            except Exception:
                pass

        # Основное ожидание до конца timeout
        w.until(lambda d: counter_value() == before + 1)

        return before + 1
