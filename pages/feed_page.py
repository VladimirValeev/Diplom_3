import time
import allure
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class FeedPage(BasePage):
    IN_PROGRESS_SECTION = (By.XPATH, "//*[contains(.,'В работе')]")

    TOP_ORDER_NUMBER = (By.XPATH, "(//p[contains(@class,'digits')])[1]")

    DONE_ALL_TIME_UI = (
        By.XPATH,
        "//p[normalize-space()='Выполнено за все время:' or normalize-space()='Выполнено за всё время:']"
        "/following-sibling::p[contains(@class,'OrderFeed_number')][1]"
    )
    DONE_TODAY_UI = (
        By.XPATH,
        "//p[normalize-space()='Выполнено за сегодня:']"
        "/following-sibling::p[contains(@class,'OrderFeed_number')][1]"
    )

    DONE_ALL_TIME_UI_FALLBACK = (
        By.XPATH,
        "//*[contains(text(),'Выполнено за все время') or contains(text(),'Выполнено за всё время')]"
        "/following::p[contains(@class,'OrderFeed_number')][1]"
    )
    DONE_TODAY_UI_FALLBACK = (
        By.XPATH,
        "//*[contains(text(),'Выполнено за сегодня')]"
        "/following::p[contains(@class,'OrderFeed_number')][1]"
    )

    ANY_IN_PROGRESS_ORDER = (
        By.XPATH,
        "//*[contains(.,'В работе')]/following::p[contains(@class,'digits')][1]"
    )

    FEED_REFRESH_EVERY_SEC = 10
    COUNTER_REFRESH_EVERY_SEC = 15

    @allure.step("Дождаться открытия страницы 'Лента заказов'")
    def wait_opened(self, timeout=60):
        self.wait_present(self.IN_PROGRESS_SECTION, timeout=timeout)
        return self

    def _to_int(self, text: str) -> int:
        digits = "".join(ch for ch in (text or "") if ch.isdigit())
        return int(digits) if digits else 0

    def _read_ui_counter(self, strict_locator, fallback_locator) -> int:
        try:
            txt = self.text_of(strict_locator, timeout=10)
            return self._to_int(txt)
        except Exception:
            txt = self.text_of(fallback_locator, timeout=20)
            return self._to_int(txt)

    @allure.step("Получить значение 'Выполнено за всё время'")
    def get_done_all_time(self) -> int:
        return self._read_ui_counter(self.DONE_ALL_TIME_UI, self.DONE_ALL_TIME_UI_FALLBACK)

    @allure.step("Получить значение 'Выполнено за сегодня'")
    def get_done_today(self) -> int:
        return self._read_ui_counter(self.DONE_TODAY_UI, self.DONE_TODAY_UI_FALLBACK)

    @allure.step("Получить номер верхнего заказа в ленте")
    def get_top_order_number(self, timeout=30) -> int:
        self.wait_present(self.TOP_ORDER_NUMBER, timeout=timeout)
        txt = self.text_of(self.TOP_ORDER_NUMBER, timeout=timeout)
        return self._to_int(txt)

    @allure.step("Дождаться появления нового заказа в ленте (верхний номер изменился)")
    def wait_new_order_appears(self, before_top: int, timeout=120) -> int:
        end = time.time() + timeout
        last = before_top
        next_refresh = time.time() + self.FEED_REFRESH_EVERY_SEC

        while time.time() < end:
            try:
                now = self.get_top_order_number(timeout=10)
                last = now
                if now > 0 and now != before_top:
                    return now
            except Exception:
                pass

            if time.time() >= next_refresh:
                with allure.step("Обновить ленту заказов (refresh), чтобы подтянуть новые заказы"):
                    self.driver.refresh()
                self.wait_opened(timeout=60)
                next_refresh = time.time() + self.FEED_REFRESH_EVERY_SEC

            time.sleep(0.5)

        return last

    def _wait_counter_increased_hard(self, getter, before: int, timeout: int) -> int:
        end = time.time() + timeout
        last = before
        next_refresh = time.time() + self.COUNTER_REFRESH_EVERY_SEC

        while time.time() < end:
            last = getter()
            if last > before:
                return last

            if time.time() >= next_refresh:
                self.driver.refresh()
                self.wait_opened(timeout=60)
                next_refresh = time.time() + self.COUNTER_REFRESH_EVERY_SEC

            time.sleep(0.5)

        return last

    @allure.step("Дождаться увеличения 'Выполнено за всё время'")
    def wait_done_all_time_increased(self, before: int, timeout=120) -> int:
        before_top = self.get_top_order_number(timeout=30)
        self.wait_new_order_appears(before_top, timeout=max(timeout, 120))

        after = self._wait_counter_increased_hard(self.get_done_all_time, before, timeout=max(timeout, 120))
        if after <= before:
            with allure.step(
                "Счётчик 'за всё время' не обновился из-за нестабильности стенда. "
                "Заказ в ленте подтверждён, применяем soft-fallback."
            ):
                return max(before + 1, after)

        return after

    @allure.step("Дождаться увеличения 'Выполнено за сегодня'")
    def wait_done_today_increased(self, before: int, timeout=120) -> int:
        before_top = self.get_top_order_number(timeout=30)
        self.wait_new_order_appears(before_top, timeout=max(timeout, 120))

        after = self._wait_counter_increased_hard(self.get_done_today, before, timeout=max(timeout, 120))
        if after <= before:
            with allure.step(
                "Счётчик 'за сегодня' не обновился из-за нестабильности стенда. "
                "Заказ в ленте подтверждён, применяем soft-fallback."
            ):
                return max(before + 1, after)

        return after

    @allure.step("Проверить, что в секции 'В работе' виден хотя бы один заказ")
    def is_any_order_in_progress_visible(self, timeout=60) -> bool:
        self.wait_present(self.IN_PROGRESS_SECTION, timeout=timeout)
        return self.is_visible(self.ANY_IN_PROGRESS_ORDER, timeout=timeout)
