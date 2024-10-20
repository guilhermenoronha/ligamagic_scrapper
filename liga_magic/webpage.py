import re
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver.remote.webelement import WebElement


def get_card_quality(card_quality: str = None, card_quality_id: int = None):
    """Retorna a qualidade da carta, seja em código da Liga Magic ou em sigla.
    Útil para comparar o estado da carta encontrada com a que o usuário deseja.
    Modo de uso:
        - Utilize a variável card_quality se quiser retornar o código da Liga Magic
        - Utilize a variável card_quality_id se quiser retornar a sigla da qualidade

    Representação da Sigla X Liga Magic:
        - 2: NM (Near Mint)
        - 3: SP (Slightly Played)
        - 4: MP (Moderate Player)
        - 5: HP (Heavy Player)
        - 6: D (Danified)

    Args:
        card_quality (str): Sigla da qualidade da carta;
        card_quality_id (int) Código da LigaMagic da qualidade da carta

    Returns:
        Código da Liga Magic ou a Sigla referente à qualidade da carta.
    """
    card_conditions = {"D": 6, "HP": 5, "MP": 4, "SP": 3, "NM": 2}
    if card_quality is not None:
        card_code = card_conditions.get(card_quality)
        if card_code is None:
            raise ValueError(
                "Condição do card desconhecida %s. Condições aceitas: D, HP, MP, SP, e NM",
                card_quality,
            )
        else:
            return card_code
    elif card_quality_id is not None:
        card_code = next(
            (key for key, value in card_conditions.items() if value == card_quality_id),
            None,
        )
        if card_code is None:
            raise ValueError(
                "Condição do card desconhecida %s. Condições aceitas: 2, 3, 4, 5 e 6",
                card_quality,
            )
        else:
            return card_code
    else:
        raise ValueError(
            "Ambos card_quality e card_quality_id estão nulos. Uma destas variáveis deve estar preenchidas."
        )


def get_store_card_quality(text: str) -> str:
    """Recupera a qualidade do card achado na loja.

    Args:
        text (str): Texto contendo o valor da carta.
        Padrão conhecido: MP\n-\n0 unid. R$ 3,00\nAvise quando chegar.

    Returns:
        str: Retorna os valores D, HP, MP, SP ou NM quando encontrado. Vazio se não encontrar nada.
    """
    try:
        card_quality = re.search(r"^[A-Z]+", text).group()
        return card_quality.upper() if card_quality in ("D", "HP", "MP", "SP", "NM") else None
    except:
        return None
    
def get_store_card_stock(text: str) -> str:
    """Recupera a qualidade do card achado na loja.

    Args:
        text (str): Texto contendo o valor da carta.
        Padrão conhecido: MP\n-\n0 unid. R$ 3,00\nAvise quando chegar.

    Returns:
        str: Retorna os valores D, HP, MP, SP ou NM quando encontrado. Vazio se não encontrar nada.
    """
    try:
        return int(re.search(r"\d+", text).group())
    except:
        return None


def strip_price(price_in_text: str) -> float:
    """Extrai o preço do HTML no formato texto "R$ 50,25" e converte para float.

    Args:
        price_in_text (str): formato do preço em texto.

    Returns:
        float: preço convertido em float.
    """
    try:
        return float(
            price_in_text.replace("R$ ", "").replace(".", "").replace(",", ".")
        )
    except:
        return None


def get_min_card_value(driver: Chrome) -> float:
    """Retorna o texto onde fica localizado o menor valor da carta no site da Liga Magic

    Args:
        driver (Chrome): drive conectado na url da carta

    Returns:
        float: menor valor encontrado na página.
    """
    return strip_price(
        driver.find_element(
            By.XPATH, '//*[@id="card-info"]/div[5]/div[2]/div/div[2]'
        ).text
    )


def get_avg_card_value(driver: Chrome) -> float:
    """Retorna o texto onde fica localizado o valor médio da carta no site da Liga Magic

    Args:
        driver (Chrome): drive conectado na url da carta

    Returns:
        float: valor médio encontrado na página.
    """
    
    return strip_price(
        driver.find_element(
            By.XPATH, '//*[@id="card-info"]/div[5]/div[2]/div/div[4]'
        ).text
    )


def get_lm_set(driver: Chrome, set_num: int) -> WebElement:
    return driver.find_element(By.CSS_SELECTOR, f"#edcard_{set_num}> img:nth-child(1)")


def get_lm_card_value(driver: Chrome, value_type: str) -> float:
    """Retorna o menor valor do card na Liga Magic entre todas as edições possíveis.
    Cards com valor 0 são ignorados.

    Args:
        driver (Chrome): _description_
        value_type (str): a função busca entre

    Raises:
        ValueError: _description_
        NoSuchElementException: _description_

    Returns:
        float: _description_
    """
    if value_type not in ("MIN", "AVG"):
        raise ValueError("Value_type encontrado: %s. value_types aceitos: MIN, AVG.")

    action = ActionChains(driver)
    global_min = float("inf")
    card_edition = 0
    while True:
        try:
            card_edition_element = get_lm_set(driver, card_edition)
            action.move_to_element(card_edition_element).click().perform()

            if value_type == "MIN":
                min_value = get_min_card_value(driver)
            else:
                min_value = get_avg_card_value(driver)

            global_min = (
                min_value if min_value < global_min and min_value > 0 else global_min
            )
            card_edition += 1
        except NoSuchElementException:
            if global_min == float("inf"):
                raise NoSuchElementException(
                    "Elemento não encontrado para a seguinte url: %s",
                    driver.current_url,
                )
            else:
                return global_min

def get_store_card_price(text: str) -> int:
    """Retorna o preço encontrado na loja.

    Args:
        text (str): Texto contendo o preço da carta.
        Padrão conhecido: MP\n-\n0 unid. R$ 3,00\nAvise quando chegar.

    Returns:
        str: Retorna o preço da carta quando encontrado ou 0 se não encontrar nada.
    """
    try:
        price = re.search(r"R\$ \d+,\d+", text).group()
        return strip_price(price)
    except:
        return None