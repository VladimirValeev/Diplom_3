import allure

from pages.main_page import MainPage


@allure.feature("Навигация")
@allure.story("Переход по клику на «Конструктор»")
def test_go_to_constructor(driver):
    main = MainPage(driver).wait_page_loaded()
    main.click_feed()
    main.click_constructor()
    # достаточно проверить, что "Соберите бургер" присутствует
    assert "Соберите бургер" in driver.page_source


@allure.feature("Навигация")
@allure.story("Переход по клику на «Лента заказов»")
def test_go_to_feed(driver):
    main = MainPage(driver).wait_page_loaded()
    main.click_feed()
    # у ленты есть заголовок "Лента заказов" (или "Лента заказов" внутри страницы)
    assert "Лента заказов" in driver.page_source or "Лента заказов".lower() in driver.page_source.lower()
