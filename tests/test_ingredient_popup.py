import allure

from pages.main_page import MainPage
from pages.ingredient_popup import IngredientPopup


@allure.feature("Основная функциональность")
class TestIngredientPopup:

    @allure.story("Клик по ингредиенту открывает окно с деталями")
    def test_ingredient_details_popup_opens(self, driver):
        main = MainPage(driver).wait_page_loaded()
        main.open_first_ingredient()
        popup = IngredientPopup(driver).wait_opened()
        assert popup is not None

    @allure.story("Окно деталей закрывается по крестику")
    def test_ingredient_details_popup_closes_by_x(self, driver):
        main = MainPage(driver).wait_page_loaded()
        main.open_first_ingredient()

        popup = IngredientPopup(driver).wait_opened()
        popup.close().wait_closed(timeout=20)

        assert popup.is_invisible(popup.MODAL, timeout=5), "Попап ингредиента не закрылся (модалка всё ещё видима)"
