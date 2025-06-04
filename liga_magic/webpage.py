import re
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def get_card_quality(card_quality: str = None, card_quality_id: int = None):
    """Retorna a qualidade da carta, seja em código da Liga Magic ou em sigla.
    Útil para comparar o estado da carta encontrada com a que o usuário deseja.
    Modo de uso:
        - Utilize a variável card_quality se quiser retornar o código da Liga Magic
        - Utilize a variável card_quality_id se quiser retornar a sigla da qualidade

    Representação da Sigla X Liga Magic:
        - 1: M (Mint)
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
    card_conditions = {"D": 6, "HP": 5, "MP": 4, "SP": 3, "NM": 2, "M": 1}
    if card_quality is not None:
        card_code = card_conditions.get(card_quality)
        if card_code is None:
            raise ValueError(
                "Condição do card desconhecida %s. Condições aceitas: D, HP, MP, SP, NM, M"
                % card_quality,
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
                "Condição do card desconhecida %s. Condições aceitas: 1, 2, 3, 4, 5 e 6",
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
        return card_quality.upper() if card_quality in ("D", "HP", "MP", "SP", "NM", "M") else None
    except:
        return None
    
def get_store_card_stock(text: str) -> str:
    """Recupera a qualidade do card achado na loja.

    Args:
        text (str): Texto contendo o valor da carta.
            Padrão conhecido: MP\n-\n0 unid. R$ 3,00\nAvise quando chegar.

    Returns:
        str: Retorna os valores D, HP, MP, SP, NM, M quando encontrado. Vazio se não encontrar nada.
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


def get_card_value(driver: Chrome, div_name: str) -> float:
    """Retorna o texto onde fica localizado o menor valor da carta no site da Liga Magic

    Args:
        driver (Chrome): drive conectado na url da carta

    Returns:
        float: menor valor encontrado na página.
    """
    if div_name not in ("min", "medium"):
        raise ValueError("div_name encontrado desconhecido. Valores aceitos: min, medium. Valor encontrado: %s", div_name)
    all_prices = driver.find_elements(By.CSS_SELECTOR, f"div.{div_name} > div.price")
    min_value = float("inf")
    for price in all_prices:
        card_price = strip_price(price.text)
        if card_price < min_value:
            min_value = card_price
    return min_value

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
    def _return_price_element(driver: Chrome, value_type: str):
        if value_type == "MIN":
            return get_card_value(driver, "min")
        else:
            return get_card_value(driver, "medium")
        

    if value_type not in ("MIN", "AVG"):
        raise ValueError("Value_type encontrado: %s. value_types aceitos: MIN, AVG." % value_type)

    action = ActionChains(driver)
    global_min = float("inf")

    card_edition_elements = driver.find_elements(By.CLASS_NAME, "edition-icon")
    if len(card_edition_elements) == 0: # card com apenas uma edição
        return _return_price_element(driver, value_type)
    else:
        for card_edition_element in card_edition_elements:
            try:
                action.move_to_element(card_edition_element).click().perform()                
                min_value = _return_price_element(driver, value_type)
                global_min = (
                    min_value if min_value < global_min and min_value > 0 else global_min
                )
            except NoSuchElementException:
                if global_min == float("inf"):
                    raise NoSuchElementException(
                        "Elemento não encontrado para a seguinte url: %s",
                        driver.current_url,
                    )
                else:
                    return global_min
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

def get_driver_instance() -> Chrome:
    """Função que retorna uma instância do Chrome para ser usada como web scrapper.

    Returns:
        Chrome: Instância do Chrome.
    """
    # algumas configurações para o webdriver
    chrome_options = ChromeOptions()
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
    chrome_options.add_argument("--disable-images")

    # instanciando a versão do webdriver que será instalada na máquina local
    service = Service(ChromeDriverManager().install())

    # instanciando o webdriver
    driver = Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(2)
    driver.set_page_load_timeout(600)
    return driver