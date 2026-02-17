import allure

from pages.main_page import MainPage
from pages.feed_page import FeedPage


@allure.feature("Лента заказов")
class TestCountersAfterOrder:

    @allure.story("При создании нового заказа счётчик «Выполнено за всё время» увеличивается")
    def test_done_all_time_increases(self, driver, registered_tokens):
        access, refresh = registered_tokens

        main = MainPage(driver).wait_page_loaded()
        main.auth_by_tokens(access, refresh)

        main.click_feed()
        feed = FeedPage(driver).wait_opened(timeout=60)
        before = feed.get_done_all_time()

        main.click_constructor()
        main.add_first_bun(timeout=60)
        main.add_first_filling(timeout=60)

        main.click_order().wait_order_modal(timeout=60)
        main.close_order_modal(timeout=60)

        main.click_feed()
        feed.wait_opened(timeout=60)
        after = feed.wait_done_all_time_increased(before, timeout=120)

        assert after > before, f"Ожидали рост 'за всё время'. Было {before}, стало {after}"

    @allure.story("При создании нового заказа счётчик «Выполнено за сегодня» увеличивается")
    def test_done_today_increases(self, driver, registered_tokens):
        access, refresh = registered_tokens

        main = MainPage(driver).wait_page_loaded()
        main.auth_by_tokens(access, refresh)

        main.click_feed()
        feed = FeedPage(driver).wait_opened(timeout=60)
        before = feed.get_done_today()

        main.click_constructor()
        main.add_first_bun(timeout=60)
        main.add_first_filling(timeout=60)

        main.click_order().wait_order_modal(timeout=60)
        main.close_order_modal(timeout=60)

        main.click_feed()
        feed.wait_opened(timeout=60)
        after = feed.wait_done_today_increased(before, timeout=120)

        assert after > before, f"Ожидали рост 'за сегодня'. Было {before}, стало {after}"
