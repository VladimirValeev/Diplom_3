import time
import allure

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

from pages.base_page import BasePage


class MainPage(BasePage):
    # Навигация
    LINK_CONSTRUCTOR = (By.CSS_SELECTOR, "a[href='/']")
    LINK_FEED = (By.CSS_SELECTOR, "a[href='/feed']")

    # Заголовки страниц
    TITLE_CONSTRUCTOR = (By.XPATH, "//*[contains(., 'Соберите бургер')]")
    TITLE_FEED = (By.XPATH, "//*[contains(., 'Лента заказов')]")

    # Табы
    TAB_BUNS = (By.XPATH, "//span[contains(., 'Булки')]/parent::*")
    TAB_FILLINGS = (By.XPATH, "//span[contains(., 'Начинки')]/parent::*")

    # Карточки
    INGREDIENT_CARDS = (By.CSS_SELECTOR, "a.BurgerIngredient_ingredient__1TVf6")
    BUNS_CARDS = (
        By.XPATH,
        "//h2[contains(., 'Булки')]/following-sibling::ul//a[contains(@class,'BurgerIngredient_ingredient')]"
    )
    FILLINGS_CARDS = (
        By.XPATH,
        "//h2[contains(., 'Начинки')]/following-sibling::ul//a[contains(@class,'BurgerIngredient_ingredient')]"
    )

    CARD_NAME = (By.CSS_SELECTOR, "p.BurgerIngredient_ingredient__text__yp3dH, p[class*='ingredient__text']")
    CARD_COUNTER = (By.XPATH, ".//p[contains(@class,'counter_counter__num')]")

    # Оверлей
    MODAL_OVERLAY = (By.CSS_SELECTOR, "div.Modal_modal_overlay__x2ZCr")

    # Конструктор drop targets
    CONSTRUCTOR_LIST = (By.CSS_SELECTOR, "ul[class*='BurgerConstructor_constructor__list']")
    CONSTRUCTOR_SECTION = (By.CSS_SELECTOR, "section[class*='BurgerConstructor']")

    # Заказ
    BTN_ORDER = (By.XPATH, "//button[contains(., 'Оформить заказ')]")
    ORDER_MODAL = (By.XPATH, "//section[contains(@class,'Modal_modal')]")
    ORDER_NUMBER = (By.XPATH, "//*[contains(@class,'Modal_modal')]//*[contains(@class,'digits')]")
    ORDER_CLOSE = (By.XPATH, "//button[contains(@class,'Modal_modal__close')]")

    # ---------- базовые действия ----------

    @allure.step("Дождаться загрузки главной страницы")
    def wait_page_loaded(self, timeout=60):
        self.wait_present(self.INGREDIENT_CARDS, timeout=timeout)
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

    @allure.step("Проверить видимость заголовка конструктора")
    def is_constructor_title_visible(self):
        return self.is_visible(self.TITLE_CONSTRUCTOR, timeout=10)

    @allure.step("Проверить видимость заголовка ленты")
    def is_feed_title_visible(self):
        return self.is_visible(self.TITLE_FEED, timeout=10)

    @allure.step("Открыть первый ингредиент")
    def open_first_ingredient(self):
        self.close_overlay_if_present()
        cards = self.wait_all_present(self.INGREDIENT_CARDS, timeout=40)
        first = cards[0]
        self.scroll_into_view(first)
        try:
            first.click()
        except Exception:
            self.js_click(first)
        return self

    # ---------- helpers ----------

    def _get_counter_from_card(self, card):
        try:
            els = card.find_elements(*self.CARD_COUNTER)
            if not els:
                return 0
            txt = (els[0].text or "").strip()
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

    def _find_filling_card_by_name(self, name, timeout=15):
        end = time.time() + timeout
        while time.time() < end:
            cards = self.find_all(self.FILLINGS_CARDS)
            for c in cards:
                try:
                    if self._get_card_name(c) == name:
                        return c
                except StaleElementReferenceException:
                    continue
            time.sleep(0.2)
        raise TimeoutException(f"Не нашёл карточку начинки по имени '{name}'")

    @allure.step("Найти drop-зону конструктора")
    def _get_drop_zone(self, timeout=40):
        self.close_overlay_if_present()

        # Самое стабильное: UL списка конструктора
        try:
            ul = self.wait_present(self.CONSTRUCTOR_LIST, timeout=10)
            self.scroll_into_view(ul)
            return ul
        except Exception:
            pass

        sec = self.wait_present(self.CONSTRUCTOR_SECTION, timeout=timeout)
        self.scroll_into_view(sec)
        return sec

    # ---------- auth by tokens ----------

    @allure.step("Авторизоваться через токены в localStorage")
    def auth_by_tokens(self, access_token: str, refresh_token: str):
        self.set_local_storage_item("accessToken", access_token)
        self.set_local_storage_item("refreshToken", refresh_token)
        self.refresh()
        self.wait_page_loaded(timeout=60)
        return self

    # ---------- build burger ----------

    @allure.step("Добавить первую булку в конструктор")
    def add_first_bun(self, timeout=60):
        self.click_constructor()
        self.wait_page_loaded(timeout=60)

        self.click(self.TAB_BUNS, timeout=30)
        buns = self.wait_all_present(self.BUNS_CARDS, timeout=40)
        bun = buns[0]
        self.scroll_into_view(bun)

        drop = self._get_drop_zone(timeout=40)
        self.drag_and_drop(bun, drop)  # alias -> robust
        return self

    @allure.step("Добавить первую начинку в конструктор")
    def add_first_filling(self, timeout=60):
        """
        Этот метод ДОЛЖЕН существовать, потому что его вызывают тесты counters_after_order.
        Делает: добавляет начинку (без возврата счётчика).
        """
        self.add_filling_and_wait_counter(timeout=timeout)
        return self

    @allure.step("Добавить начинку и дождаться увеличения счётчика")
    def add_filling_and_wait_counter(self, timeout=60):
        self.close_overlay_if_present()
        self.click_constructor()
        self.wait_page_loaded(timeout=60)

        self.click(self.TAB_FILLINGS, timeout=30)
        cards = self.wait_all_present(self.FILLINGS_CARDS, timeout=40)
        card = cards[0]
        self.scroll_into_view(card)

        name = self._get_card_name(card)
        before = self._get_counter_from_card(card)

        drop = self._get_drop_zone(timeout=40)

        # 1) первая попытка (robust)
        self.drag_and_drop(card, drop)

        def counter_now():
            c = self._find_filling_card_by_name(name, timeout=8)
            return self._get_counter_from_card(c)

        # 2) быстрый чек
        quick_deadline = time.time() + 6
        while time.time() < quick_deadline:
            if counter_now() == before + 1:
                return before + 1
            time.sleep(0.2)

        # 3) повтор JS (самый сильный)
        try:
            c2 = self._find_filling_card_by_name(name, timeout=8)
            drop2 = self._get_drop_zone(timeout=20)
            self._dnd_html5_js(c2, drop2)  # метод BasePage
        except Exception:
            pass

        # 4) основное ожидание
        end = time.time() + timeout
        while time.time() < end:
            if counter_now() == before + 1:
                return before + 1
            time.sleep(0.2)

        raise TimeoutException("Счётчик ингредиента не увеличился")

    @allure.step("Получить счётчик первой начинки")
    def get_first_filling_counter(self):
        self.click(self.TAB_FILLINGS, timeout=30)
        cards = self.wait_all_present(self.FILLINGS_CARDS, timeout=40)
        return self._get_counter_from_card(cards[0])

    # ---------- order modal ----------

    @allure.step("Нажать «Оформить заказ»")
    def click_order(self):
        self.click(self.BTN_ORDER, timeout=30)
        return self

    @allure.step("Дождаться модалки заказа")
    def wait_order_modal(self, timeout=30):
        self.wait_present(self.ORDER_MODAL, timeout=timeout)
        self.wait_present(self.ORDER_NUMBER, timeout=timeout)
        return self

    @allure.step("Закрыть модалку заказа")
    def close_order_modal(self, timeout=30):
        self.click(self.ORDER_CLOSE, timeout=timeout)
        self.wait_until_gone(self.ORDER_MODAL, timeout=timeout)
        return self
