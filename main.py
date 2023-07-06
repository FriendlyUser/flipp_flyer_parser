import undetected_chromedriver as uc
import time
import json
import re
import selenium.webdriver.support.expected_conditions as EC
from dateutil.parser import isoparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from PIL import Image

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
    Inject a cookie with the name 'walmart.nearestPostalCode' and the value 'V5H 4M1'.
    Refresh the page to apply the cookie changes.
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

    driver.get("https://www.walmart.ca/flyer?locale=en&icid=home+page_HP_Header_Groceries_WM")
    cookie = {
        'name': 'walmart.nearestPostalCode',
        'value': 'V5H 4M1',
    }
    # Inject the cookie
    driver.add_cookie(cookie)
    
    # Refresh the page to apply the cookie changes
    driver.refresh()
    return driver


def scrap_flyer(driver, cfg: dict):
    try:
        main_element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.TAG_NAME, "main")))
    except Exception as e:
        # save page source
        error_file = cfg.get("error_file", "data/error_walmart.html")
        with open(error_file, "w", errors="ignore", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(e)
        exit(1)
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

    # /html/body/flipp-router/flipp-publication-page/div/div[2]/flipp-sfml-component/sfml-storefront/div/sfml-linear-layout
    main_flyer = driver.find_element(By.XPATH, "/html/body/flipp-router")
    if main_flyer:
        print("Found main flyer")
    else:
        main_flyer = iframe.find_element(By.TAG_NAME, "sfml-linear-layout")
        raise Exception("Could not find main flyer")
    # click on first item in iframe

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
    for findex, flyer_image in enumerate(flyer_images):
        # time sleep 5
        # get each button from flyer
        driver.execute_script("arguments[0].scrollIntoView();", flyer_image)
        buttons = flyer_image.find_elements(By.TAG_NAME, "button")
        # extract path from flyer_image
        # <sfml-flyer-image impressionable="" width="27064" height="2560" path="flyers/d24a169f-17dd-4c05-b326-87391b598be6/" resolutions="8 5.33 3.7 2.33 1.55 1" src-rect="0 0 975 2560" aspect-ratio="2.6256410256410256" sfml-anchor-id="0" style="width: 100%; height: 1423.1px;"><a wayfinder-anchor="" name="sfml_anchor_0"></a>
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
            if savings_regex:
                savings = float(savings_regex.group(1))
                current_price = float(savings_regex.group(2))
            else: 
                savings = ""
                current_price = ""

            if current_price == "":
                # check for Rollback
                rollback_regex = re.search(rollbar_regex, label)
                if rollback_regex:
                    current_price = float(rollback_regex.group(1))
            # pull label from cfg
            label = label.replace(item_text, "")
            button.click()
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
                'size': 0,
                'type': 0,
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
    driver.switch_to.default_content()
def get_walmart():
    """
    Get the information about Walmart.
    Returns:
        None
    """

    driver = setup_walmart()
    cfg = {
        'url': "https://www.walmart.ca/flyer?locale=en&icid=home+page_HP_Header_Groceries_WM",
        'postal_code': "V5H 4M1",
        'error_file': "data/error_walmart.html",
        'cookies_file': "data/cookies.json",
        'html_file': "data/walmart.html",
        'data_file': "data/walmart.json",
        'item_text': 'Select for details',
        'rollbar_regex': r'Rollback, (\d+)',
        'save_regex': r'Save \$([\d.]+), \$([\d.]+)',
        'max_items': 50,
    }
    scrap_flyer(driver, cfg)
    

if __name__ == '__main__':    
    get_walmart()