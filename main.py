import re
import os
from time import sleep
from dotenv import load_dotenv
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import liga_magic.webpage as wp

load_dotenv()
INPUTS = "assets/inputs/"
OUTPUTS = "assets/outputs/"

with open(INPUTS + "cardlist.txt", "r", encoding="UTF-8") as f:
    cards = f.readlines()

cards = [
    re.sub(r"\d+", "", re.sub(r"//.*", "", re.sub(r"\(.*", "", card))).strip()
    for card in cards
]

# algumas configurações para o webdriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--proxy-server='direct://'")
chrome_options.add_argument("--proxy-bypass-list=*")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--ignore-certificate-errors")
# Testando
chrome_options.add_argument("--disable-images")

# instanciando a versão do webdriver que será instalada na máquina local
service = Service(ChromeDriverManager().install())

# instanciando o webdriver
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.implicitly_wait(2)
driver.set_page_load_timeout(600)

user_card_quality = os.getenv("MINIMAL_CARD_QUALITY").upper()
user_accepted_languages = os.getenv("ACCEPTED_LANGUAGES").upper().split(",")


# efetuando busca no site
cartas_web_dic = []

user_stores = pd.read_csv(INPUTS + "stores.csv", sep=",")
user_stores["name"] = user_stores["name"].str.upper()

for card_name in cards:
    card_url = card_name.replace(" ", "+")
    driver.get(f"https://www.ligamagic.com.br/?view=cards/card&card={card_url}")

    min_card_value = wp.get_lm_card_value(driver, "MIN")
    avg_card_value = wp.get_lm_card_value(driver, "AVG")

    # Bloco para pegar a melhor oferta dentre os parâmetros passados pelo usuário
    user_card_quality_code = wp.get_card_quality(card_quality=user_card_quality)
    stores = driver.find_elements(By.XPATH, '//div[starts-with(@id, "line_e")]')
    for count, store in enumerate(stores):
        found_store_name = ""
        card_quality_code = int(
            re.search(
                r"\d+",
                store.find_element(By.CSS_SELECTOR, "div.e-col4 font").get_attribute(
                    "onclick"
                ),
            ).group()
        )
        card_language = (
            store.find_element(By.CSS_SELECTOR, "div.e-col4 img")
            .get_attribute("title")
            .upper()
        )
        store_name = (
            store.find_element(By.CSS_SELECTOR, "div.container-logo-selo img")
            .get_attribute("title")
            .upper()
        )
        if (
            user_stores["name"].isin([store_name]).any()
            and card_language in user_accepted_languages
            and card_quality_code <= user_card_quality_code
        ):
            cheaper_cards_amount = count
            found_card_quality = wp.get_card_quality(card_quality_id=card_quality_code)
            found_store_name = store_name
            break

    # Bloco para pegar o preço da carta na loja achada
    if found_store_name != "":  # não achou a carta
        card_url = driver.find_element(By.CLASS_NAME, "cinzaescuro").get_property(
            "href"
        )
        card_id = re.search(r"\d+", card_url).group()
        store_url = user_stores[user_stores["name"] == found_store_name]["url"].values[
            0
        ]
        store_url = f"{store_url}?view=ecom/item&tcg=1&card={card_id}"
        discount = user_stores[user_stores["name"] == found_store_name][
            "discount"
        ].values[0]
        store_discount = 0 if np.isnan(discount) else discount / 100
        driver.get(store_url)

        # TODO: arrumar isso
        for i in range(10):
            store_cards = driver.find_elements(By.CLASS_NAME, "table-cards-row")
            if len(store_cards) == 0:
                sleep(5)
            else:
                break

        if len(store_cards) == 0:
            raise ValueError("Found no regs from %s", store_url)

        final_card_price = float("inf")

        card_languages = driver.find_elements(
            "xpath",
            '//div[@class="table-cards-body-cell tooltip-item text-center"]//img',
        )

        for i in range(len(card_languages)):
            store_text = store_cards[i].text
            card_language = card_languages[i].accessible_name.upper()
            card_quality = wp.get_store_card_quality(store_text)
            card_price = wp.get_store_card_price(store_text)
            card_stock = wp.get_store_card_stock(store_text)

            if (
                card_price is not None
                and card_language is not None
                and card_quality is not None
            ):
                if (
                    card_language in user_accepted_languages
                    and card_quality_code
                    <= wp.get_card_quality(card_quality=card_quality)
                    and card_price <= final_card_price
                    and card_stock > 0
                ):
                    if card_price < final_card_price:
                        total_cards = 0
                    total_cards += card_stock
                    final_card_price = card_price

        cartas_web_dic = [
            {
                "card_name": card_name.replace(",", " ").replace("\n", ""),
                "store_name": found_store_name,
                "card_quality": found_card_quality,
                "stock": total_cards,
                "cheaper_cards_amount": cheaper_cards_amount,
                "min_value": min_card_value,
                "avg_value": avg_card_value,
                "store_value": final_card_price,
                "premium_discount_on_min_value": (final_card_price / min_card_value)
                - 1,
                "premium_discount_on_avg_value": (final_card_price / avg_card_value)
                - 1,
            }
        ]
    else:
        cartas_web_dic = [
            {
                "card_name": card_name.replace(",", " ").replace("\n", ""),
                "store_name": None,
                "card_quality": None,
                "stock": 0,
                "cheaper_cards_amount": 0,
                "min_value": min_card_value,
                "avg_value": avg_card_value,
                "store_value": 0,
                "premium_discount_on_min_value": 0,
                "premium_discount_on_avg_value": 0,
            }
        ]
        print("Não achou a carta", card_name)

    output_file = OUTPUTS + "cards.csv"
    cartas_web_df = pd.DataFrame().from_dict(cartas_web_dic)
    cartas_web_df.to_csv(
        output_file, sep=";", mode="a", header=not os.path.exists(output_file), index=False
    )
driver.close()
