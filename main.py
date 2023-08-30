import undetected_chromedriver as uc
import time
import json
import re
import argparse
import selenium.webdriver.support.expected_conditions as EC
from dateutil.parser import isoparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from PIL import Image

# refactor this code later
from enum import Enum
class StoreType(Enum):
    SAVEON = 'saveon'
    WALMART = 'walmart'
    SUPERSTORE = 'superstore'


def make_driver():
    """
    Create and configure a Chrome WebDriver instance with a headless option and a subprocess option disabled.

    Return the configured WebDriver instance.
    """
    driver = uc.Chrome(headless=False,use_subprocess=False)
    return driver

def swap_to_iframe(driver, iframe_class="flippiframe.mainframe"):
    driver.switch_to.default_content()
    # Switch to the iframe
    iframe = driver.find_element(By.CLASS_NAME, iframe_class)
    # then find frame and swap
    driver.switch_to.frame(iframe)


def parse_flipp_aside(driver, cfg)-> dict:
    """
    Parse the flipp aside iframe and extract relevant data.
    
    Args:
        driver (WebDriver): The WebDriver instance to use for parsing the iframe.
        cfg (dict): A dictionary containing configuration parameters.
        
    Returns:
        dict: A dictionary containing the extracted data from the flipp aside iframe.
            The dictionary has the following keys:
            - "start_date" (str): The start date of the flipp aside.
            - "end_date" (str): The end date of the flipp aside.
            - "description" (str): The description of the flipp aside.
            - "size" (str): The size of the flipp aside.
            - "quantity" (str): The quantity of the flipp aside.
            - "product_type" (str): The product type of the flipp aside.
            - "frozen" (bool): True if the flipp aside is frozen, False otherwise.
            - "see_more_link" (str): The link to see more information about the flipp aside.
    """
    swap_to_iframe(driver, "flippiframe.productframe")

    flipp_aside_data = {}
    # find translation
    validity_dates = driver.find_element(By.TAG_NAME, "flipp-validity-dates")
    start_date = validity_dates.get_attribute("start-date")
    end_date = validity_dates.get_attribute("end-date")

    flipp_aside_data["start_date"] = start_date
    flipp_aside_data["end_date"] = end_date
    # Parse the date strings into datetime objects if needed
    # start_date = isoparse(start_date)
    # end_date = isoparse(end_date)
    # screenshot
    # get element by tag name p.flipp-description
    try:
        flipp_description = driver.find_element(By.CLASS_NAME, "flipp-description")
        # get text
        description = flipp_description.text
    except NoSuchElementException as e:
        description = ""

    flipp_aside_data["description"] = description
    # scrap size and type, parse from description
    # look for mL and g following an number
    size_regex = r"(\d+(?:\.\d+)?)\s*(mL|g)"
    match = re.search(size_regex, description)
    if match:
        size = f"{match.group(0)}" # mL or g
    else:
        size = 1

    flipp_aside_data["size"] = size

    quantity_regex = r"(\d+)\s*X\s*(\d+)\s*(mL|g)"
    match = re.search(quantity_regex, description)
    if match:
        quantity = f"{match.group(1)}" # mL or g
    else: 
        quantity = 1

    flipp_aside_data["quantity"] = quantity
    # look for Pack. and Each. in description
    if "pack" in description.lower():
        product_type = "pack"
    elif "each" in description.lower():
        product_type = "each"
    else:
        product_type = ""

    flipp_aside_data["product_type"] = product_type

    if "frozen" in description.lower():
        frozen = True
    else:
        frozen = False

    flipp_aside_data["frozen"] = frozen

    time.sleep(1)
    # get link by class see-more-link and extract href property
    try:
        see_more_ele = driver.find_element(By.CLASS_NAME, "see-more-link")
        see_more_link = see_more_ele.get_attribute("href")
    except Exception as e:
        see_more_link = ""
    
    flipp_aside_data["see_more_link"] = see_more_link
    # driver.save_screenshot(f"data/{data_product_id}.png")
    swap_to_iframe(driver)

    # return dict with all data variables
    return flipp_aside_data


def selenium_setup_saveon():
    # setup selenium manually by entering postal code
    driver = make_driver()
    driver.get("https://www.saveonfoods.com/sm/pickup/rsid/907/circular")
    # driver.get("https://www.walmart.ca/en/stores-near-me")
    return driver

def selenium_setup_walmart():
    # setup selenium manually by entering postal code
    driver = make_driver()
    driver.get("https://www.walmart.ca/flyer?flyer_type=walmartcanada&store_code=1213&locale=en")
    # driver.get("https://www.walmart.ca/en/stores-near-me")
    return driver


def setup_superstore():
    driver = make_driver()
    driver.get("https://www.realcanadiansuperstore.ca/print-flyer")
    cookie = {
        'name': 'last_selected_store',
        'value': '1518',
    }
    driver.refresh()
    return driver

def setup_walmart():
    """
    Sets up the Walmart web scraping environment by:
    1. Creating a driver using the make_driver() function.
    2. Navigating to the Walmart flyer page.
    3. Injecting a cookie with the nearest postal code.
    4. Refreshing the page to apply the cookie changes.
    
    Returns:
        driver (WebDriver): The WebDriver instance for interacting with the Walmart website.
    """
    driver = make_driver()

    driver.get("https://www.walmart.ca/flyer?flyer_type=walmartcanada&store_code=1213&locale=en")
    cookie = {
        'name': 'walmart.nearestPostalCode',
        'value': 'V5H4M1',
    }
    # Inject the cookie
    driver.add_cookie(cookie)

    shipping_address = {
        "name": "walmart.shippingPostalCode",
        "value": "V5H4M1"
    }
    driver.add_cookie(shipping_address)

    preferred_store = {
        'name': "walmart.preferredstore",
        'value': "1213"
    }

    geolocation_cookie = {
        'name': "walmart.nearestLatLng",
        'value': '"49.2311,-122.956"'
    }

    driver.add_cookie(preferred_store)
    
    # Refresh the page to apply the cookie changes
    driver.refresh()
    print("try again")
    return driver


def scrap_flyer(driver, cfg: dict):
    """
    Scrapes a flipp flyer using a Selenium WebDriver and saves the data to a JSON file.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        cfg (dict): A dictionary containing configuration parameters.

    Returns:
        None
    """
    print("Scrapping flyer")
    try:
        main_element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.TAG_NAME, "main")))
    except Exception as e:
        # save page source
        error_file = cfg.get("error_file", "error_walmart.html")
        with open(error_file, "w", errors="ignore", encoding="utf-8") as f:
            f.write(driver.page_source)
        time.sleep(3)
    time.sleep(5)
    # Switch to the iframe
    swap_to_iframe(driver)
    # save content as data/walmart.html
    cookies = driver.get_cookies()
    # save cookies are cookies.json
    cookies_file = cfg.get("cookies_file", "data/cookies.json")
    with open(cookies_file, "w") as f:
        json.dump(cookies, f)
    
    # get source html for driver
    html = driver.page_source

    html_file = cfg.get("html_file", "data/walmart.html")
    # save to data/html
    with open(html_file, "w", errors="ignore", encoding="utf-8") as f:
        f.write(html)

    main_flyer = driver.find_element(By.XPATH, "/html/body/flipp-router")
    if main_flyer:
        print("Found main flyer")
    else:
        main_flyer = iframe.find_element(By.TAG_NAME, "sfml-linear-layout")
        raise Exception("Could not find main flyer")
    # click on first item in iframe

    time.sleep(7)
    # get all tags named sfml-flyer-image from main_flyer and loop through them
    flyer_images = main_flyer.find_elements(By.TAG_NAME, "sfml-flyer-image")
    if flyer_images:
        print("Found flyer")
        # filter images for "save on" to ensure
        if cfg.get("type") == StoreType.SAVEON:
            pass
            # filter flyer_images out that are missing attribute impressionable
            # flyer_images = [image for image in flyer_images if image.get_attribute("impressionable") is None]
    else:
        raise Exception("Could not find flyer images")
    data = []
    # close modal if present
    # make a new dataframe

    item_text = cfg.get("item_text")
    rollbar_regex = cfg.get("rollbar_regex")
    save_regex = cfg.get("save_regex")
    data_file = cfg.get("data_file")
    max_items = cfg.get("max_items")

    # look for acsCloseButton acsAbandonButton and click it
    try:
        # activeModal = driver.find_element(By.CLASS_NAME, "acsCloseButton")
        # activeModal.click()
        # acsDeclineButton
        activeModal = driver.find_element(By.CLASS_NAME, "acsAbandonButton")
        activeModal.click()
    except Exception as e:
        print("No active modal found")

    parsed_labels = []
    for findex, flyer_image in enumerate(flyer_images):

        # get each button from flyer
        driver.execute_script("arguments[0].scrollIntoView();", flyer_image)
        buttons = flyer_image.find_elements(By.TAG_NAME, "button")
        # extract path from flyer_image
        flyer_path = flyer_image.get_attribute("path")
        # iterate through each button
        for index, button in enumerate(buttons):
            # click on button
            # print aria-label for button
            label = button.get_attribute("aria-label")
            if label in parsed_labels:
                print("Parsed label: " + label)
                continue
            else:
                print(f"Parsing for button: {label}")
            parsed_labels.append(label)
            data_product_id = button.get_attribute("data-product-id")
            product_name = label.split(",")[0].strip()

            # information scrappable on the main flyer without clicking for more details
            item_main_info = {}
            item_main_info["label"] = label
            item_main_info["flyer_path"] = flyer_path
            item_main_info["product_name"] = product_name
            item_main_info["data_product_id"] = data_product_id
            # remove Select for details from label
            # scroll so button is centered
            # driver.execute_script("arguments[0].scrollIntoView();", button)
            savings_regex = re.search(save_regex, label)
            savings = ""
            current_price = ""
            if savings_regex:
                savings = float(savings_regex.group(1))
                current_price = float(savings_regex.group(2))
            else: 
                # if price is not set, scan for numbers, if only one match, then current_price,
                # if two matches then savings is available as well, second number
                # disable double number checking for save on
                # as grams can happen next, this should be a fallback
                number_regex = re.findall(r'\$?(\d+(?:\.\d+)?)', label)
                if number_regex != None:
                    if len(number_regex) == 1:
                        current_price = number_regex[0]
                    elif len(number_regex) == 2:
                        if "\u00a2" in label:
                            savings = float(number_regex[0]) * 0.01
                        else:
                            savings = number_regex[0]
                            current_price = number_regex[1]
                    else:
                        current_price = ""

            if current_price == "" or current_price == None:
                # check for Rollback
                rollback_regex = re.search(rollbar_regex, label)
                if rollback_regex:
                    current_price = float(rollback_regex.group(1))

                # logic for superstore
            if current_price == "":
                number_regex = re.findall(r'\$(\d+(?:\.\d+)?)', label)
                if number_regex != None:
                    current_price = number_regex[0]
            # pull label from cfg
            item_main_info['savings'] = savings,
            item_main_info['current_price'] = current_price,
            label = label.replace(item_text, "")
            try:
                # check if button is in view, if not scroll to button
                # buttonHeight = button.size["height"] + 150
                # print(buttonHeight)
                # if button.location_once_scrolled_into_view == False:
                #     driver.execute_script(f"window.scrollBy(0, -{buttonHeight});")
                #     time.sleep(2)
                #     print("scrolling into view")
                driver.execute_script("arguments[0].click();", button)
            except Exception as e:
                print(e)
                error_file = cfg.get("error_file", "error_walmart.html")
                with open(error_file, "w", errors="ignore", encoding="utf-8") as f:
                    f.write(driver.page_source)
                exit(1)
            time.sleep(5)
            # handle product details subsection
            if cfg.get("type") != StoreType.SUPERSTORE:
                flipp_aside_info = parse_flipp_aside(driver, cfg)
            # handle superstore
            else:
                flipp_aside_info = {}
                pass
            
            item_main_info.update(flipp_aside_info)
            # merge data
            # attempt to match for words, pack. or each.
            # frozen, true or false
            
            data.append(item_main_info)

            with open(data_file, 'w') as f:
                json.dump(data, f)

            # if index >= 2:
            #     print("Only scan up to the first 75 items")
            #     break
        if len(data) >= max_items:
            print("Only scan up to the first 75 items")
            break
    with open(data_file, 'w') as f:
        json.dump(data, f)

    print("script done")
    driver.switch_to.default_content()
def get_walmart():
    """
    Get the information about Walmart.
    Returns:
        None
    """

    driver = selenium_setup_walmart()
    cfg = {
        'url': "https://www.walmart.ca/flyer?locale=en&icid=home+page_HP_Header_Groceries_WM",
        'postal_code': "V5H 4M1",
        'error_file': "data/error_walmart.html",
        'cookies_file': "data/cookies.json",
        'html_file': "data/walmart.html",
        'data_file': "data/walmart.json",
        'item_text': 'Select for details',
        'rollbar_regex': r'Rollback, (\d+)',
        'save_regex': r'Save \$([\d*?]+), \$([\d.]+)',
        'max_items': 50,
    }
    scrap_flyer(driver, cfg)
    
def get_walmart():
    """
    Get the information about Walmart.
    Returns:
        None
    """

    driver = selenium_setup_walmart()
    cfg = {
        'url': "https://www.saveonfoods.com/sm/pickup/rsid/907/circular",
        'postal_code': "V5H 4M1",
        'error_file': "data/error_save_on.html",
        'cookies_file': "data/save_on_cookies.json",
        'html_file': "data/walmart.html",
        'data_file': "data/walmart.json",
        'item_text': 'Select for details',
        'rollbar_regex': r'Rollback, (\d+)',
        'save_regex': r'Save \$([\d*?]+), \$([\d.]+)',
        'max_items': 50,
        'type': StoreType("walmart"),
    }
    scrap_flyer(driver, cfg)

def get_saveon():
    """
    Get the information about Walmart.
    Returns:
        None
    """
    driver = selenium_setup_saveon()
    cfg = {
        'url': "https://www.saveonfoods.com/sm/pickup/rsid/907/circular",
        'postal_code': "V5H 4M1",
        'error_file': "data/error_save_on.html",
        'cookies_file': "data/save_on_cookies.json",
        'html_file': "data/walmart.html",
        'data_file': "data/walmart.json",
        'item_text': 'Select for details',
        'rollbar_regex': r'Rollback, (\d+)',
        'save_regex': r'Save \$([\d*?]+), \$([\d.]+)',
        'max_items': 50,
        'type': StoreType("saveon"),
    }
    scrap_flyer(driver, cfg)


def get_superstore():
    """
    Get the information about Superstore.
    Returns:
        None
    """
    driver = setup_superstore()
    cfg = {
        'url': "https://www.realcanadiansuperstore.ca/print-flyer",
        'postal_code': "V5H 4M1",
        'error_file': "data/error_superstore.html",
        'cookies_file': "data/superstore_cookies.json",
        'html_file': "data/superstore.html",
        'data_file': "data/superstore.json",
        'item_text': 'Select for details',
        'rollbar_regex': r'Rollback, (\d+)',
        'save_regex': r'Save \$([\d*?]+), \$([\d.]+)',
        'max_items': 50,
        'type': StoreType("superstore"),
    }
    scrap_flyer(driver, cfg)

def main(args):
    type_value = args.type
    # convert type_value to enum

    store_value = StoreType(type_value)
    if store_value == StoreType.SAVEON:
        # Do something for saveon option
        get_saveon()
    elif store_value == StoreType.WALMART:
        # Do something for walmart option
        get_walmart()
    elif store_value == StoreType.SUPERSTORE:
        # Do something for superstore option
        get_superstore()
    else:
        raise Exception("Not implemented yet")

if __name__ == '__main__':
    # argparser with the following arguments type
    parser = argparse.ArgumentParser()
    # argument type with 3 options: saveon, walmart, and superstore
    # argparse with enum
    parser.add_argument("-t", '--type', type=str, choices=['saveon', 'walmart', 'superstore'], default="walmart")
    # convert type to enum
    # Parse the command-line arguments
    args = parser.parse_args()

    # Access the value of the "type" argument
    main(args)
    # get_walmart()