from selenium.webdriver.common.by import By
from .base_page import BasePage


class FeedPage(BasePage):
    # Счётчики (на стенде могут быть разные теги — ищем по тексту рядом)
    DONE_ALL_TIME = (By.XPATH, "//*[contains(.,'Выполнено за все время') or contains(.,'Выполнено за всё время')]/following::*[1]")
    DONE_TODAY = (By.XPATH, "//*[contains(.,'Выполнено за сегодня')]/following::*[1]")

    IN_PROGRESS_SECTION = (By.XPATH, "//*[contains(.,'В работе')]")

    def wait_opened(self):
        self.wait_present(self.IN_PROGRESS_SECTION)
        return self

    def get_done_all_time(self) -> int:
        return int(self.text_of(self.DONE_ALL_TIME))

    def get_done_today(self) -> int:
        return int(self.text_of(self.DONE_TODAY))
