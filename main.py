import re
import os
import logging
from time import sleep
from dotenv import load_dotenv
import numpy as np
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
from pandas import DataFrame
import liga_magic.webpage as wp


def get_cards(card_list_file: str) -> list[str]:
    """Lê o arquivo com a lista de cartas e faz um tratamento para ser carregado no site da liga magic.

    Args:
        card_list_file (str): lista de cartas. Padrão esperado:
            1 Pinnacle Monk
            1 Scavenger's Talent

    Returns:
        list[str]: lista com o nome das cartas.
    """
    with open(card_list_file, "r", encoding="UTF-8") as f:
        cards = f.readlines()
    return [
        re.sub(r"\d+", "", re.sub(r"//.*", "", re.sub(r"\(.*", "", card))).strip()
        for card in cards
    ]


def get_card_dataframe(
    legible_card_name: str,
    min_card_value: float,
    avg_card_value: float,
    store_name: str = None,
    card_quality: str = None,
    stock: int = 0,
    cheaper_cards_amount: int = 0,
    store_value: float = 0,
    premium_discount_on_min_value: float = 0,
    premium_discount_on_avg_value: float = 0,
) -> DataFrame:
    cartas_web_dic = [
        {
            "card_name": legible_card_name,
            "store_name": store_name,
            "card_quality": card_quality,
            "stock": stock,
            "cheaper_cards_amount": cheaper_cards_amount,
            "min_value": min_card_value,
            "avg_value": avg_card_value,
            "store_value": store_value,
            "premium_discount_on_min_value": premium_discount_on_min_value,
            "premium_discount_on_avg_value": premium_discount_on_avg_value,
        }
    ]
    return pd.DataFrame().from_dict(cartas_web_dic)


logging.basicConfig(level=logging.INFO)
load_dotenv()
INPUTS = "assets/inputs/"
OUTPUT_FILE = "assets/outputs/cards.csv"
USER_ACCEPTED_LANGUAGES = os.getenv("ACCEPTED_LANGUAGES").upper().split(",")

# Se a variável MAXIMUM_CARD_PRICE não for configurada, coloca um valor alto para comparações.
if os.getenv("MAXIMUM_CARD_PRICE") is not None:
    MAXIMUM_CARD_PRICE = float(os.getenv("MAXIMUM_CARD_PRICE"))
else:
    MAXIMUM_CARD_PRICE = float("inf")


user_stores = pd.read_csv(INPUTS + "stores.csv", sep=";")
user_stores["name"] = user_stores["name"].str.upper()

# Bloco para pegar a melhor oferta dentre os parâmetros passados pelo usuário
USER_CARD_QUALITY_CODE = wp.get_card_quality(
    card_quality=os.getenv("MINIMAL_CARD_QUALITY").upper()
)

driver = wp.get_driver_instance()
is_the_cookie_removed = False

# Loop para pegar informação de cada card.
for card_name in get_cards(INPUTS + "cardlist.txt"):
    legible_card_name = card_name.replace(",", " ").replace("\n", "")
    card_url = card_name.replace(" ", "+")
    driver.get(f"https://www.ligamagic.com.br/?view=cards/card&card={card_url}")

    min_card_value, avg_card_value = wp.get_lm_min_avg_card_value(driver)
    #min_card_value = wp.get_lm_card_value(driver, "MIN")
    #avg_card_value = wp.get_lm_card_value(driver, "AVG")

    # Carta está mais cara do que estou disposto a pagar, então não procuro valores.
    if min_card_value > MAXIMUM_CARD_PRICE:
        cartas_web_df = get_card_dataframe(
            legible_card_name, min_card_value, avg_card_value
        )
        logging.info(f"Carta {card_name} está muito cara! Está custando {min_card_value}")
        cartas_web_df.to_csv(
            OUTPUT_FILE,
            sep=";",
            mode="a",
            header=not os.path.exists(OUTPUT_FILE),
            index=False,
        )
        continue

    wait = WebDriverWait(driver, 10)

    if not is_the_cookie_removed:
        # Clica no botão de banner pela primeira vez para aceitar os cookies..
        try:
            cookie_banner = wait.until(
                EC.presence_of_element_located((By.ID, "lgpd-cookie"))
            )
            close_cookie_button = cookie_banner.find_element(
                By.TAG_NAME, "button"
            )
            close_cookie_button.click()
            is_the_cookie_removed = True
        except Exception as e:
            pass

    #TODO: PAREI AQUI. VER UMA FORMA MELHOR DE ESCREVER ESSE CODIGO
    # Clica no botão VER MAIS nas cartas que possuem muitas ofertas.
    try:
        load_more_button = wait.until(
            EC.element_to_be_clickable((By.ID, "marketplace-stores-loadmore"))
        )
        load_more_button.click()
        sleep(5)
    except Exception as e:
        # Caso o botão não exista, não faz nada.
        pass

    marketplace_stores = driver.find_element(By.ID, "marketplace-stores")
    stores = marketplace_stores.find_elements(By.CLASS_NAME, "store")

    original_window = driver.current_window_handle
    for count, store in enumerate(stores):
        # driver.get(f"https://www.ligamagic.com.br/?view=cards/card&card={card_url}")

        found_store_name = ""

        card_quality = store.find_element(
            By.XPATH,
            f"/html/body/main/div[1]/div[7]/div[2]/div[4]/div[{count + 1}]/div[3]/div[1]/div[2]/div[2]",
        ).text
        card_quality = card_quality if card_quality != "" else "D"

        card_quality_code = wp.get_card_quality(card_quality=card_quality)

        card_language = store.find_element(
            By.XPATH,
            f"/html/body/main/div[1]/div[7]/div[2]/div[4]/div[{count + 1}]/div[3]/div[1]/div[2]/div[1]/img",
        ).accessible_name.upper()
        store_image = store.find_element(
            By.XPATH,
            f"/html/body/main/div[1]/div[7]/div[2]/div[4]/div[{count + 1}]/div[2]/div[1]/a/div/img",
        )
        store_code = int(re.search(r"(\d+)", store_image.get_attribute("data-src")).group(0))
        
        # Quando não há o código da loja. Método mais lento, pois visita pagina por pagina para achar o nome.
        if user_stores["ligamagic_store_code"].count() == 0:
            driver.execute_script(
                f"window.open('https://www.ligamagic.com.br/?view=mp/showcase/home&id={store_code}', '_blank');"
            )
            driver.switch_to.window(driver.window_handles[-1])
            sleep(1)
            store_name = driver.find_element(
                By.CSS_SELECTOR, ".container-store-name .name div:first-child"
            ).text.upper()
            driver.close()
            driver.switch_to.window(original_window)
        else:
            if not user_stores["ligamagic_store_code"].isin([store_code]).any():
                store_name = '' 
            else:
                store_name = user_stores.loc[user_stores['ligamagic_store_code'] == store_code, 'name'].iloc[0]

        if (
            user_stores["name"].isin([store_name]).any()
            #store_code in store_codes
            and card_language in USER_ACCEPTED_LANGUAGES
            and card_quality_code <= USER_CARD_QUALITY_CODE
        ):
            cheaper_cards_amount = count
            found_card_quality = card_quality
            found_store_name = store_name
            break

    # Bloco para pegar o preço da carta na loja achada
    if found_store_name != "":  # não achou a carta

        card_url = driver.find_element(
            By.XPATH,
            "/html/body/main/div[1]/div[3]/div[2]/div/div/div[2]/div[2]/div[1]/img",
        ).get_attribute("class")

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
                logging.warning("ELEMENTO NÃO ENCONTRADO EM table-cards-row!")
                sleep(5)
            else:
                break

        if len(store_cards) == 0:
            raise ValueError("Found no regs from %s" % store_url)

        final_card_price = float(
            "inf"
        )  # driver.find_elements(By.CSS_SELECTOR, "div.min > div.price")

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
                    card_language in USER_ACCEPTED_LANGUAGES
                    and card_quality_code
                    <= wp.get_card_quality(card_quality=card_quality)
                    and card_price <= final_card_price
                    and card_stock > 0
                ):
                    if card_price < final_card_price:
                        total_cards = 0
                    total_cards += card_stock
                    final_card_price = card_price

        cartas_web_df = get_card_dataframe(
            legible_card_name,
            min_card_value,
            avg_card_value,
            found_store_name,
            found_card_quality,
            total_cards,
            cheaper_cards_amount,
            final_card_price,
            (final_card_price / min_card_value) - 1,
            (final_card_price / avg_card_value) - 1,
        )
        print("Salvando a carta", legible_card_name)
    else:
        cartas_web_df = get_card_dataframe(
            legible_card_name, min_card_value, avg_card_value
        )
        print("Não achou a carta", card_name)
    cartas_web_df.to_csv(
        OUTPUT_FILE,
        sep=";",
        mode="a",
        header=not os.path.exists(OUTPUT_FILE),
        index=False,
    )
driver.close()
