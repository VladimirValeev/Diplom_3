import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage


class IngredientPopup(BasePage):
    # Заголовок модалки "Детали ингредиента"
    HEADER = (By.XPATH, "//*[contains(., 'Детали ингредиента')]")

    # Контейнер модалки (чтобы ждать исчезновение)
    MODAL = (By.XPATH, "//section[contains(@class,'Modal_modal')]")

    # Крестик закрытия
    CLOSE_BTN = (By.XPATH, "//button[contains(@class,'Modal_modal__close')]")

    def wait_opened(self, timeout=20):
        # ВАЖНО: возвращаем self, а не WebElement
        self.wait_present(self.MODAL, timeout=timeout)
        self.wait_present(self.HEADER, timeout=timeout)
        return self

    @allure.step("Закрыть попап по крестику")
    def close(self, timeout=20):
        self.click(self.CLOSE_BTN, timeout=timeout)
        self.wait_until_gone(self.MODAL, timeout=timeout)
        return self
