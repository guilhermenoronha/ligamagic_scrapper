from unittest.mock import MagicMock, patch
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ChromeOptions, Chrome
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pytest
import liga_magic.webpage as wp


@pytest.fixture
def init_driver():
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
    service = Service(ChromeDriverManager().install())
    return Chrome(service=service, options=chrome_options)


def test_get_card_quality():
    assert wp.get_card_quality(card_quality="D") == 6
    assert wp.get_card_quality(card_quality="HP") == 5
    assert wp.get_card_quality(card_quality="MP") == 4
    assert wp.get_card_quality(card_quality="SP") == 3
    assert wp.get_card_quality(card_quality="NM") == 2
    assert wp.get_card_quality(card_quality="M") == 1
    assert wp.get_card_quality(card_quality_id=6) == "D"
    assert wp.get_card_quality(card_quality_id=5) == "HP"
    assert wp.get_card_quality(card_quality_id=4) == "MP"
    assert wp.get_card_quality(card_quality_id=3) == "SP"
    assert wp.get_card_quality(card_quality_id=2) == "NM"
    assert wp.get_card_quality(card_quality_id=1) == "M"


def test_get_card_quality_fails():
    # all none
    with pytest.raises(Exception):
        wp.get_card_quality()
    # invalid card_quality
    with pytest.raises(Exception):
        wp.get_card_quality(card_quality="FF")
    # invalic card_quality_id
    with pytest.raises(Exception):
        wp.get_card_quality(card_quality_id=7)


def test_strip_price():
    assert wp.strip_price("5,50") == 5.50
    assert wp.strip_price("R$ 100,00") == 100
    assert wp.strip_price("R$ 0,01") == 0.01


def test_strip_price_fails():
    assert wp.strip_price("") == None
    assert wp.strip_price("USD 5.50") == None


@patch("selenium.webdriver.common.action_chains.ActionChains")
def test_get_lm_card_value_normal(mock_action):
    # Create a mock driver instance
    mock_driver = MagicMock()

    # Create mock WebElement instances
    mock_card_edition_element = MagicMock(spec=WebElement)
    mock_min_element_1 = MagicMock(spec=WebElement, text="R$ 10,00")
    mock_min_element_2 = MagicMock(spec=WebElement, text="R$ 5,00")

    # Mock find_element to return different elements in sequence
    mock_driver.find_element.side_effect = [
        mock_card_edition_element,  # First edition element
        mock_min_element_1,  # First min value element
        mock_card_edition_element,  # Second edition element
        mock_min_element_2,  # Second min value element
        NoSuchElementException,  # End the loop
    ]

    # Mock action chain behavior
    mock_action_instance = mock_action.return_value
    mock_action_instance.move_to_element.return_value = mock_action_instance
    mock_action_instance.click.return_value = mock_action_instance
    mock_action_instance.perform.return_value = None

    # Call the function and assert the result
    assert wp.get_lm_card_value(mock_driver, "AVG") == 5.00


def test_get_lm_card_value_with_no_values():
    # Create a mock driver instance
    mock_driver = MagicMock()

    # Simulate NoSuchElementException immediately to end the loop
    mock_driver.find_element.side_effect = NoSuchElementException

    # Call the function and assert the result
    with pytest.raises(Exception):
        wp.get_lm_card_value(mock_driver, "MIN")


@patch("selenium.webdriver.common.action_chains.ActionChains")
def test_get_lm_card_value_ignores_zero(mock_action):
    # Create a mock driver instance
    mock_driver = MagicMock()

    # Create mock WebElement instances
    mock_card_edition_element = MagicMock(spec=WebElement)
    mock_min_element_0 = MagicMock(spec=WebElement, text="R$ 0,00")
    mock_min_element_10 = MagicMock(spec=WebElement, text="R$ 10,00")

    # Mock find_element to return different elements in sequence
    mock_driver.find_element.side_effect = [
        mock_card_edition_element,  # First edition element
        mock_min_element_0,  # Min value = 0, should be ignored
        mock_card_edition_element,  # Second edition element
        mock_min_element_10,  # Min value = 10.00, should be selected
        NoSuchElementException,  # End the loop
    ]

    # Mock action chain behavior
    mock_action_instance = mock_action.return_value
    mock_action_instance.move_to_element.return_value = mock_action_instance
    mock_action_instance.click.return_value = mock_action_instance
    mock_action_instance.perform.return_value = None

    # Call the function and assert the result
    assert wp.get_lm_card_value(mock_driver, "MIN")


@patch("selenium.webdriver.common.action_chains.ActionChains")
def test_get_lm_card_value_wrong_type_value(mock_action):
    # Create a mock driver instance
    mock_driver = MagicMock()

    # Create a mock driver instance
    mock_driver = MagicMock()

    # Create mock WebElement instances
    mock_card_edition_element = MagicMock(spec=WebElement)
    mock_min_element_0 = MagicMock(spec=WebElement, text="R$ 0,00")

    # Mock find_element to return different elements in sequence
    mock_driver.find_element.side_effect = [
        mock_card_edition_element,  # First edition element
        mock_min_element_0,  # Min value = 0, should be ignored
        mock_card_edition_element,  # Second edition element
        NoSuchElementException,  # End the loop
    ]

    # Mock action chain behavior
    mock_action_instance = mock_action.return_value
    mock_action_instance.move_to_element.return_value = mock_action_instance
    mock_action_instance.click.return_value = mock_action_instance
    mock_action_instance.perform.return_value = None

    # Call the function and assert the result
    with pytest.raises(Exception):
        wp.get_lm_card_value(mock_driver, "MAX")


def test_get_min_card_value(init_driver):
    driver = init_driver
    driver.get(
        "https://www.ligamagic.com.br/?view=cards/card&card=Emberheart+Challenger"
    )
    assert wp.get_min_card_value(driver) > 0


def test_get_avg_card_value(init_driver):
    driver = init_driver
    driver.get(
        "https://www.ligamagic.com.br/?view=cards/card&card=Emberheart+Challenger"
    )
    assert wp.get_avg_card_value(driver) > 0

def test_get_lm_set(init_driver):
    #TODO:
    pass

def test_get_store_card_quality():
    assert wp.get_store_card_quality("MP\n-\n0 unid. R$ 3,00\nAvise quando chegar.") == "MP"
    assert wp.get_store_card_quality("'NM\nFoil\n2 unid.\nProduto indisponível.'") is None


def test_get_store_card_price():
    assert wp.get_store_card_price("MP\n-\n0 unid. R$ 3,00\nAvise quando chegar.") == 3
    assert wp.get_store_card_price("'NM\nFoil\n2 unid.\nProduto indisponível.'") is None

def test_get_store_card_stock():
    assert wp.get_store_card_stock("MP\n-\n0 unid. R$ 3,00\nAvise quando chegar.") == 0
    assert wp.get_store_card_stock("'NM\nFoil\n2 unid.\nProduto indisponível.'") is None