import uuid
import requests
import allure

from pages.main_page import MainPage

BASE_URL = "https://stellarburgers.education-services.ru"


def _register_user_and_get_tokens():
    uniq = uuid.uuid4().hex[:10]
    payload = {
        "email": f"vova_{uniq}@test.ru",
        "password": "Passw0rd!",
        "name": f"Vova_{uniq}"
    }
    r = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
    r.raise_for_status()
    data = r.json()
    return data["accessToken"], data["refreshToken"]


@allure.feature("Основная функциональность")
class TestCountersAfterOrder:

    @allure.story("После оформления заказа счётчики ингредиентов сбрасываются")
    def test_counters_reset_after_order_created(self, driver):
        access, refresh = _register_user_and_get_tokens()

        main = MainPage(driver).wait_page_loaded()
        main.auth_by_tokens(access, refresh)

        # собрать бургер: булка + начинка (для активной кнопки заказа)
        main.add_first_bun(timeout=40)
        main.add_first_filling(timeout=40)

        before = main.get_first_filling_counter()
        assert before > 0, "Перед оформлением заказа счётчик на карточке должен быть > 0"

        main.click_order().wait_order_modal(timeout=40).close_order_modal(timeout=40)

        # после заказа счетчики ингредиентов должны стать 0
        after = main.get_first_filling_counter()
        assert after == 0, f"После оформления заказа счётчик должен быть 0, а стал {after}"
