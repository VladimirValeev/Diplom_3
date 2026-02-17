import allure
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class IngredientPopup(BasePage):
    HEADER = (By.XPATH, "//*[contains(., 'Детали ингредиента')]")
    MODAL = (By.XPATH, "//section[contains(@class,'Modal_modal')]")
    CLOSE_BTN = (By.XPATH, "//button[contains(@class,'Modal_modal__close')]")

    @allure.step("Дождаться открытия попапа ингредиента")
    def wait_opened(self, timeout=20):
        self.wait_present(self.MODAL, timeout=timeout)
        self.wait_visible(self.HEADER, timeout=timeout)
        return self

    @allure.step("Закрыть попап по крестику")
    def close(self, timeout=20):
        self.click(self.CLOSE_BTN, timeout=timeout)
        return self

    @allure.step("Дождаться закрытия попапа ингредиента")
    def wait_closed(self, timeout=20):
        self.wait_until_gone(self.MODAL, timeout=timeout)
        return self
