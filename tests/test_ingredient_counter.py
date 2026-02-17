import allure
from pages.main_page import MainPage


@allure.feature("Основная функциональность")
class TestIngredientCounter:

    @allure.story("При добавлении ингредиента в заказ счётчик увеличивается")
    def test_ingredient_counter_increases_after_add_to_order(self, driver):
        main = MainPage(driver).wait_page_loaded()
        after = main.add_filling_and_wait_counter(timeout=40)
        assert after >= 1, f"Счётчик должен быть >= 1, а получился {after}"
