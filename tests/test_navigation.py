import allure
from pages.main_page import MainPage


@allure.feature("Навигация")
class TestNavigation:

    @allure.story("Переход по клику на «Конструктор»")
    def test_go_to_constructor(self, driver):
        main = MainPage(driver).wait_page_loaded()
        main.click_feed()
        main.click_constructor()
        assert main.is_constructor_title_visible(), "Не отображается заголовок конструктора 'Соберите бургер'"

    @allure.story("Переход по клику на «Лента заказов»")
    def test_go_to_feed(self, driver):
        main = MainPage(driver).wait_page_loaded()
        main.click_feed()
        assert main.is_feed_title_visible(), "Не отображается заголовок ленты заказов"
