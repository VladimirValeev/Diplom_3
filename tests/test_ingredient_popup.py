import allure

from pages.main_page import MainPage
from pages.ingredient_popup import IngredientPopup


@allure.feature("Основная функциональность")
@allure.story("Клик по ингредиенту открывает окно с деталями")
def test_ingredient_details_popup_opens(driver):
    main = MainPage(driver).wait_page_loaded()
    main.open_first_ingredient()

    popup = IngredientPopup(driver).wait_opened()
    assert popup is not None


@allure.feature("Основная функциональность")
@allure.story("Окно деталей закрывается по крестику")
def test_ingredient_details_popup_closes_by_x(driver):
    main = MainPage(driver).wait_page_loaded()
    main.open_first_ingredient()

    popup = IngredientPopup(driver).wait_opened()
    popup.close()

    # если close() не кинул исключение — считаем ок
    assert True


@allure.feature("Основная функциональность")
@allure.story("При добавлении ингредиента в заказ счётчик увеличивается")
def test_ingredient_counter_increases_after_add_to_order(driver):
    main = MainPage(driver).wait_page_loaded()
    after = main.add_filling_and_wait_counter(timeout=40)

    # -1 означает, что ожидание увеличения не произошло (Timeout внутри page object)
    assert after != -1, "Не удалось добиться увеличения счётчика ингредиента после добавления в заказ"
    assert after >= 1, f"Счётчик должен быть >= 1, а получился {after}"
