import undetected_chromedriver as uc
import time
import json
import re
import argparse
import selenium.webdriver.support.expected_conditions as EC
from dateutil.parser import isoparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from PIL import Image

# refactor this code later
from enum import Enum
class StoreType(Enum):
    SAVEON = 'saveon'
    WALMART = 'walmart'
    SUPERSTORE = 'superstore'

def calc_location_styles_from_button(element):
    style = element.get_attribute('style')
    left_match = re.search(r'left:\s*([\d.]+)px', style)
    top_match = re.search(r'top:\s*([\d.]+)px', style)
    width_match = re.search(r'width:\s*([\d.]+)px', style)
    height_match = re.search(r'height:\s*([\d.]+)px', style)
    # return top, left, right=left+width, bottom=top+height
    if left_match and top_match and width_match and height_match:
        left = float(left_match.group(1))
        top = float(top_match.group(1))
        width = float(width_match.group(1))
        height = float(height_match.group(1))
        # return matches if they all exist
        return {
            'left': left,
            'top': top,
            'right': left + width,
            'bottom': top+height,
            'height': height,
            'width': width
        }
    else: 
        raise Exception("RAISING ERROR AS this is still not working")
        return None

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



def selenium_setup_walmart():
    # setup selenium manually by entering postal code
    driver = make_driver()
    driver.get("https://www.walmart.ca/flyer?flyer_type=walmartcanada&store_code=1213&locale=en")
    # driver.get("https://www.walmart.ca/en/stores-near-me")

    # # input postal code into sfa-search__input
    # # clear sfa-search__input
    # driver.find_element(By.CLASS_NAME, "sfa-search__input").clear()
    # time.sleep(1)
    # driver.find_element(By.CLASS_NAME, "sfa-search__input").send_keys("V5H4M1")
    # time.sleep(1)
    # # click on sfa-wm-btn sfa-search__btn search-btn
    # driver.find_element(By.CLASS_NAME, "sfa-search__btn").click()
    # time.sleep(3)
    # # click on first element
    # driver.find_element(By.CLASS_NAME, "sfa-store-list-item__name").click()
    # time.sleep(2)
    # # find link header-flyers
    # driver.find_element(By.LINK_TEXT, "Flyers").click()
    # time.sleep(2)
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

    time.sleep(1)
    # get all tags named sfml-flyer-image from main_flyer and loop through them
    flyer_images = main_flyer.find_elements(By.TAG_NAME, "sfml-flyer-image")
    if flyer_images:
        print("Found flyer")
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
        activeModal = driver.find_element(By.CLASS_NAME, "acsCloseButton")
        activeModal.click()
    except Exception as e:
        print("No active modal found")
    for findex, flyer_image in enumerate(flyer_images):
        # time sleep 5
        # get each button from flyer
        driver.execute_script("arguments[0].scrollIntoView();", flyer_image)
        buttons = flyer_image.find_elements(By.TAG_NAME, "button")
        # extract path from flyer_image
        flyer_path = flyer_image.get_attribute("path")
        # iterate through each button
        for index, button in enumerate(buttons):
            # click on button
            # print aria-label for button
            print(f"Parsing for button: {button.get_attribute('aria-label')}")
            label = button.get_attribute("aria-label")
            data_product_id = button.get_attribute("data-product-id")
            product_name = label.split(",")[0].strip()
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
            # pull label from cfg
            label = label.replace(item_text, "")
            try:
                button.click()
            except Exception as e:
                print(e)
                error_file = cfg.get("error_file", "error_walmart.html")
                with open(error_file, "w", errors="ignore", encoding="utf-8") as f:
                    f.write(driver.page_source)
                # activeModal = driver.find_element(By.CLASS_NAME, "acsCloseButton.acsAbandonButton")
                # activeModal.click()
                exit(1)
            time.sleep(5)
            swap_to_iframe(driver, "flippiframe.productframe")
            # find translation
            validity_dates = driver.find_element(By.TAG_NAME, "flipp-validity-dates")
            start_date = validity_dates.get_attribute("start-date")
            end_date = validity_dates.get_attribute("end-date")

            # Parse the date strings into datetime objects if needed
            # start_date = isoparse(start_date)
            # end_date = isoparse(end_date)
            # screenshot
            # get element by tag name p.flipp-description
            flipp_description = driver.find_element(By.CLASS_NAME, "flipp-description")
            # get text
            description = flipp_description.text

            # scrap size and type, parse from description
            # look for mL and g following an number
            size_regex = r"(\d+(?:\.\d+)?)\s*(mL|g)"
            match = re.search(size_regex, description)
            if match:
                size = f"{match.group(0)}" # mL or g
            else:
                size = 1
            quantity_regex = r"(\d+)\s*X\s*(\d+)\s*(mL|g)"
            match = re.search(quantity_regex, description)
            if match:
                quantity = f"{match.group(1)}" # mL or g
            else: 
                quantity = 1

            # look for Pack. and Each. in description
            if "pack" in description.lower():
                product_type = "pack"
            elif "each" in description.lower():
                product_type = "each"

            if "frozen" in description.lower():
                frozen = True
            else:
                frozen = False
            time.sleep(1)
            # get link by class see-more-link and extract href property
            try:
                see_more_ele = driver.find_element(By.CLASS_NAME, "see-more-link")
                see_more_link = see_more_ele.get_attribute("href")
            except Exception as e:
                see_more_link = ""
                print(e)
            driver.save_screenshot(f"data/{data_product_id}.png")
            swap_to_iframe(driver)
            # attempt to match for words, pack. or each.
            # frozen, true or false
            
            data.append({
                'label': label,
                'data_product_id': data_product_id,
                'product_name': product_name,
                'savings': savings,
                'current_price': current_price,
                'start_date': start_date,
                'end_date': end_date,
                'description': description,
                'quantity': quantity,
                'size': size,
                'type': product_type,
                'frozen': frozen,
                'flyer_url': flyer_path,
                'url': see_more_link
            })

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
    

def main(args):
    if type_value == StoreType.SAVEON:
        # Do something for saveon option
        pass
    elif type_value == StoreType.WALMART:
        # Do something for walmart option
        get_walmart()
    elif type_value == StoreType.SUPERSTORE:
        # Do something for superstore option
        raise Exception("Not implemented yet")

if __name__ == '__main__':
    # argparser with the following arguments type
    parser = argparse.ArgumentParser()
    # argument type with 3 options: saveon, walmart, and superstore
    parser.add_argument("type", type=str, choices=['saveon', 'walmart', 'superstore'], default="walmart")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Access the value of the "type" argument
    main(args)