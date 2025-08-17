import nodriver as uc
import time
import json
import re
import random
import argparse
import selenium.webdriver.support.expected_conditions as EC
from bs4 import BeautifulSoup
import os
import datetime
from dotenv import load_dotenv
from dateutil.parser import isoparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from PIL import Image

# refactor this code later
from enum import Enum
import psycopg2
from psycopg2 import sql, errors

load_dotenv()

class StoreType(Enum):
    SAVEON = 'saveon'
    WALMART = 'walmart'
    SUPERSTORE = 'superstore'
    LOBLAWS = 'loblaws'


async def make_driver():
    """
    Create and configure a Chrome WebDriver instance with a headless option and a subprocess option disabled.

    Return the configured WebDriver instance.
    """
    driver = await uc.start()
    # driver = uc.Chrome(headless=False,use_subprocess=False)

    # driver.maximize_window()
    return driver

async def swap_to_iframe(tab: uc.Tab, iframe_class="flippiframe.mainframe"):
    # tab.switch_to.default_content()
    # Switch to the iframe
    # iframe = tab.select(By.CLASS_NAME, iframe_class)
    # iframe = await tab.select(By.CLASS_NAME, iframe_class)
    # # then find frame and swap
    # if not iframe:
    #     raise Exception("iframe not found, likely changes in the flipp template")
    # assuming we dont need to swap to iframe anymore
    # driver.switch_to.frame(iframe)
    pass 


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
    # before this was flippiframe.productframe flippiframe asideframe
    try:
        swap_to_iframe(driver, "flippiframe.asideframe")
    except Exception as e:
        print("failed to search with flippiframe.asideframe")
        swap_to_iframe(driver, "flippiframe.navframe")

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

    # if not see_more_link:
        
    
    flipp_aside_data["see_more_link"] = see_more_link
    # driver.save_screenshot(f"data/{data_product_id}.png")
    swap_to_iframe(driver)

    # return dict with all data variables
    return flipp_aside_data


async def selenium_setup_saveon():
    # setup selenium manually by entering postal code
    driver = await make_driver()
    tab = driver.get("https://www.saveonfoods.com/sm/planning/rsid/907/circular")
    # driver.get("https://www.walmart.ca/en/stores-near-me")
    return tab

async def setup_walmart():
    # setup selenium manually by entering postal code
    driver = await make_driver()
    tab: uc.Tab = driver.get('https://www.walmart.ca/en/stores-near-me/burnaby-sw-1213')

    try:
        # Wait for the "Set as My Store" button to be clickable
        # set_as_my_store_button = WebDriverWait(driver, 10).until(
        #     EC.element_to_be_clickable((By.XPATH, "//button[text()='Set as My Store']"))
        # )
        set_as_my_store_button = await tab.find(
            text='Set as My Store', 
            timeout=10
        )
        if set_as_my_store_button:
            print("Button found! Clicking it.")
            await set_as_my_store_button.click()
        else:
            print("Button not found within the timeout period.")

        # between 1 and 5 seconds
        lapse_rand = random.randint(1, 5)
        # Wait for a bit after setting the store
        time.sleep(lapse_rand)

        # Wait for the "View Flyers" button to be clickable and then click
        # view_flyers_button = WebDriverWait(driver, 10).until(
        #     EC.element_to_be_clickable((By.XPATH, "//a[text()='View Flyers']"))
        # )
        view_flyers_button = await tab.find(
            text='View Flyers', 
            timeout=10
        )

        lapse_rand = random.randint(1, 5)
        # Wait for a bit after setting the store
        time.sleep(lapse_rand)
        view_flyers_button.click()


        # WebDriverWait(driver, 10).until(
        #     EC.url_contains("flyer?flyer_type=walmartcanada&store_code=1213&locale=en")
        # )
        # current_url = await tab.get_url()
        # if "flyer?flyer_type=walmartcanada&store_code=1213&locale=en" in current_url:
        #     print("Successfully navigated to the flyer page.")


    except Exception as e:
        print(f"An error occurred: {e}")
        driver.get("https://www.walmart.ca/flyer?flyer_type=walmartcanada&store_code=1213&locale=en")

    return driver

def selenium_setup_loblaws():
    # setup selenium manually by entering postal code
    driver = make_driver()
    driver.get("https://www.loblaws.ca/en/store-locator/details/7491")
    try:
        # Wait for the flyer link to be clickable
        location_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "location-details-contact__flyer__link"))
        )
        location_link.click()

        # Wait for a bit after clicking the link
        WebDriverWait(driver, 5)

    except Exception as e:
        print(f"An error occurred: {e}")
        driver.quit()
        return None

    # driver.get("https://www.walmart.ca/en/stores-near-me")
    return driver


def setup_superstore():
    driver = make_driver()
    driver.get('https://www.realcanadiansuperstore.ca/en/store-locator/details/1518?icta=pickup-details-modal')
    try:
        time.sleep(7)
        cookie_more = {
            'name': 'flipp-store-code_2271',
            'value': '1518',
            'domain': 'www.realcanadiansuperstore.ca',  # Ensure this matches the domain of the current page
            'path': '/'
        }
        driver.add_cookie(cookie_more)
        driver.refresh()
        time.sleep(15)
        location_link = driver.find_element(By.CLASS_NAME, "location-details-contact__flyer__link")
        location_link.click()
        time.sleep(3)
    except Exception as e:
        print("Move to the flyer page before proceeding")
        input("Press enter to continue")
    return driver

async def setup_walmart():
    """
    Sets up the Walmart web scraping environment by:
    1. Creating a driver using the make_driver() function.
    2. Navigating to the Walmart flyer page.
    3. Injecting a cookie with the nearest postal code.
    4. Refreshing the page to apply the cookie changes.
    
    Returns:
        driver (WebDriver): The WebDriver instance for interacting with the Walmart website.
    """
    driver = await make_driver()

    tab = await driver.get("https://www.walmart.ca/flyer?flyer_type=walmartcanada&store_code=1213&locale=en")
    cookies = await tab.send(uc.cdp.storage.get_cookies())
    print(cookies)
    cookie = json.dumps({
        'name': 'walmart.nearestPostalCode',
        'value': 'V5H4M1',
    })
    # cookies.append(cookie)
    await tab.send(uc.cdp.storage.set_cookies(cookies))

    # shipping_address = {
    #     "name": "walmart.shippingPostalCode",
    #     "value": "V5H4M1"
    # }
    # driver.add_cookie(shipping_address)

    # preferred_store = {
    #     'name': "walmart.preferredstore",
    #     'value': "1213"
    # }

    # geolocation_cookie = {
    #     'name': "walmart.nearestLatLng",
    #     'value': '"49.2311,-122.956"'
    # }

    # driver.add_cookie(preferred_store)
    
    print("try again")
    return tab


async def scrap_flyer(tab: uc.Tab, cfg: dict):
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
        # main_element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.TAG_NAME, "main")))
        main_element = await tab.find("main", timeout=10)
        url = tab.url
        print("url", url)
    except Exception as e:
        # save page source
        error_file = cfg.get("error_file", "error_walmart.html")
        page_content = tab.get_content()
        with open(error_file, "w", errors="ignore", encoding="utf-8") as f:
            f.write(page_content)
        time.sleep(3)
    time.sleep(5)
    # Switch to the iframe
    await swap_to_iframe(tab)
    # save content as data/walmart.html
    cookies = await tab.send(uc.cdp.storage.get_cookies())
    # save cookies are cookies.json
    cookies_file = cfg.get("cookies_file", "data/cookies.json")
    # check if data directory exists, if not create it
    if not os.path.exists("data"):
        os.makedirs("data")
    # with open(cookies_file, "w") as f:
    #     json.dump(cookies, f)
    
    # get source html for driver
    html = await tab.get_content()

    html_file = cfg.get("html_file", "data/walmart.html")
    # save to data/html
    with open(html_file, "w", errors="ignore", encoding="utf-8") as f:
        f.write(html)

    main_flyer = await tab.find("flipp-router")
    if main_flyer:
        print("Found main flyer")
    else:
        # main_flyer = iframe.find_element(By.TAG_NAME, "sfml-linear-layout")
        raise Exception("Could not find main flyer")
    # click on first item in iframe

    time.sleep(7)
    # get all tags named sfml-flyer-image from main_flyer and loop through them
    flyer_images = await tab.find_all("sfml-flyer-image")
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
        activeModal = tab.find("acsAbandonButton")
        activeModal.click()
    except Exception as e:
        print("No active modal found")

    parsed_labels = []
    for findex, flyer_image in enumerate(flyer_images):
        
        # get each button from flyer
        flyer_image_uc: uc.Element = flyer_image
        # driver.execute_script("arguments[0].scrollIntoView();", flyer_image)
        # tab.evaluate("arguments[0].scrollIntoView();", flyer_image)
        await flyer_image_uc.scroll_into_view()
        buttons = await flyer_image_uc.query_selector("button")
        # extract path from flyer_image
        flyer_attributes = flyer_image_uc.attributes
        # assuming list print and exit
        print(flyer_attributes)
        flyer_path = flyer_attributes.get("src")
        print(flyer_path)
        exit(1)
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
                    if len(number_regex) >= 1:
                        current_price = number_regex[0]
            # pull label from cfg
            # check if savings is list, if so grab first item
            if type(savings) == list:
                savings = savings[0]
            
            if type(current_price) == list:
                current_price = current_price[0]
            item_main_info['savings'] = savings
            item_main_info['current_price'] = current_price
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
            # handle save on differently some items not available
            # small business here
            if cfg.get("type") != StoreType.SUPERSTORE:
                flipp_aside_info = parse_flipp_aside(driver, cfg)
            else:
                flipp_aside_info = {}
                pass
            # handle superstore
            try:
                # swap to main frame?
                # Retrieve the entire HTML of the page
                if cfg.get("type") == StoreType.SUPERSTORE:
                    # swap to default content,
                    driver.switch_to.default_content()
                    # grab page source and swap to iframe
                    html = driver.page_source
                    swap_to_iframe(driver)
                elif cfg.get("type") == StoreType.SAVEON:
                    driver.switch_to.default_content()
                    # grab page source and swap to iframe
                    html = driver.page_source
                    swap_to_iframe(driver)
                elif cfg.get("type") == StoreType.LOBLAWS:
                    # swap to default content,
                    driver.switch_to.default_content()
                    # grab page source and swap to iframe
                    html = driver.page_source
                    swap_to_iframe(driver)
                else:
                    html = driver.page_source
                # Parse the HTML with BeautifulSoup
                soup = BeautifulSoup(html, "html.parser")
                # with open("data/superstore.html", "w", errors="ignore", encoding="utf-8") as f:
                #     f.write(soup.prettify())
                # Try to select elements with the class 'product-details-link__link'
                product_details_links = soup.select(".product-details-link__link")
                
                see_more_links = []
                if product_details_links:
                    # Collect all href attributes from matching elements
                    see_more_links = [
                        link.get("href")
                        for link in product_details_links
                        if link.get("href")
                    ]
                else:
                    # If not found, scan all <a> elements for the text "View Product Details"
                    all_links = soup.find_all("a")
                    print("Scanning all <a> tags. Total links found:", len(all_links))
                    for link in all_links:
                        link_text = link.get_text(strip=True)

                        if "view product details" in link_text.lower():
                            see_more_links.append(link.get("href"))
                            # Break after finding the first matching link
                            break  
                
                if see_more_links:
                    relative_see_more_link = see_more_links[0]
                    if cfg.get("type") == StoreType.WALMART:
                        base_url = "https://www.walmart.ca"
                    elif cfg.get("type") == StoreType.SUPERSTORE:
                        base_url = "https://www.realcanadiansuperstore.ca"
                    elif cfg.get("type") == StoreType.SAVEON:
                        base_url = "https://www.saveonfoods.com"
                    elif cfg.get("type") == StoreType.LOBLAWS:
                        base_url = "https://www.loblaws.ca"
                    else:
                        raise Exception("Not implemented yet")
                    # Update your dictionary with the first found link
                    flipp_aside_info["see_more_link"] = f"{base_url}/{relative_see_more_link}"
                else:
                    print("No product details links found in the flipp aside.")
                    # hardcode it for save on, its not in the flyer and hard to get to
                    if cfg.get("type") == StoreType.SAVEON:
                        flipp_aside_info["see_more_link"] = "https://www.saveonfoods.com/sm/planning/rsid/907/circular"
                
                print("see_more_links:", see_more_links)
                
            except Exception as e:
                print("An error occurred:", e)
            item_main_info.update(flipp_aside_info)
            # merge data
            # attempt to match for words, pack. or each.
            # frozen, true or false
            print("flipp_aside_info: ", item_main_info)
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

    # driver.switch_to.default_content()

    return cfg

async def get_walmart():
    """
    Get the information about Walmart.
    Returns:
        None
    """

    tab = await setup_walmart()
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
        'type': StoreType("walmart"),
    }
    time.sleep(2)
    await scrap_flyer(tab, cfg)
    return cfg

def get_saveon():
    """
    Get the information about Save on.
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

    return cfg 

def get_loblaws():
    """
    Get the information about Save on.
    Returns:
        None
    """
    driver = selenium_setup_loblaws()
    cfg = {
        'url': "https://www.loblaws.ca/en/store-locator/details/7491",
        'postal_code': "V5H 4M1",
        'error_file': "data/error_save_on.html",
        'cookies_file': "data/loblaws.json",
        'html_file': "data/loblaws.html",
        'data_file': "data/loblaws.json",
        'item_text': 'Select for details',
        'rollbar_regex': r'Rollback, (\d+)',
        'save_regex': r'Save \$([\d*?]+), \$([\d.]+)',
        'max_items': 75,
        'type': StoreType("loblaws"),
    }
    scrap_flyer(driver, cfg)

    return cfg 


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
        'max_items': 5,
        'type': StoreType("superstore"),
    }
    scrap_flyer(driver, cfg)
    return cfg


def add_to_db(data, params):

    # db_user = os.getenv('DB_USER')
    # db_password = os.getenv('DB_PASSWORD')
    # db_host = os.getenv('DB_HOST')
    # db_name = os.getenv('DB_NAME')
    # # Optional: DB_PORT, if not using the default 5432
    # db_port = os.getenv('DB_PORT', 5432)
    connection_url = os.getenv("DATABASE_URL")
    store_type = params.get('type')
    # if enum type convert to string
    if isinstance(store_type, StoreType):
        store_type = store_type.value
    else:
        store_type = str(store_type)

    print("store_type: ", store_type)
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            connection_url
        )

        # Create a new database session and return a cursor
        cursor = conn.cursor()

        # SQL insert statement
        insert_grocery = """
            INSERT INTO grocery (
                label,
                flyer_path,
                product_name,
                data_product_id,
                savings,
                current_price,
                start_date,
                end_date,
                description,
                size,
                quantity,
                product_type,
                frozen,
                see_more_link,
                store
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        print("json_data: ", data)

        for json_data in data:
            # Extract and manipulate fields as needed
            start_date = json_data.get('start_date')
            if start_date:
                start_date = start_date[:10]
            else:
                # No start_date provided:
                # 1) Find today's date
                today = datetime.date.today()
                
                # 2) Calculate how many days until the next (or current) Thursday
                #    weekday(): Monday=0, Tuesday=1, Wednesday=2, Thursday=3, ...
                #    So, if it's already Thursday, days_until_thursday becomes 0
                #    Otherwise, it calculates how many days until the next Thursday
                days_until_thursday = (3 - today.weekday()) % 7
                
                # 3) Closest Thursday from today
                closest_thursday = today + datetime.timedelta(days=days_until_thursday)
                
                # 4) Format it as YYYY-MM-DD
                start_date = closest_thursday.strftime('%Y-%m-%d')
            
            end_date = json_data.get('end_date')
            if end_date:
                end_date = end_date[:10]

            else:
                # No end_date provided:
                # 1) Convert our new start_date string back to a date object
                start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
                
                # 2) Add 7 days
                end_dt = start_dt + datetime.timedelta(days=7)
                
                # 3) Format as YYYY-MM-DD
                end_date = end_dt.strftime('%Y-%m-%d')
            current_price = json_data.get('current_price', 0)
            if not current_price:
                current_price = 0

            # json_data.get('description', '') cap at 255 characters
            description = json_data.get('description', '')
            if len(description) > 255:
                description = description[:255]
            data_grocery = (
                json_data['label'],
                json_data['flyer_path'],
                json_data['product_name'],
                json_data.get('data_product_id', 0),
                json_data['savings'],
                current_price,
                start_date,
                end_date,
                description,
                json_data.get('size'),
                json_data.get('quantity'),
                json_data.get('product_type'),
                json_data.get('frozen'),
                json_data.get('see_more_link'),
                store_type
            )
            print("Data: ", data_grocery)

            # Execute and commit
            cursor.execute(insert_grocery, data_grocery)
        
            conn.commit()

    except psycopg2.Error as err:
        print(f"Error: {err}")
        if conn:
            conn.rollback()  # rollback if something goes wrong

    finally:
        # Close the connection properly
        if conn:
            cursor.close()
            conn.close()
            print("PostgreSQL connection is closed")



async def main(args):
    type_value = args.type
    # convert type_value to enum

    store_value = StoreType(type_value)
    if store_value == StoreType.SAVEON:
        # Do something for saveon option
        cfg = get_saveon()
    elif store_value == StoreType.WALMART:
        # Do something for walmart option
        cfg = await get_walmart()
    elif store_value == StoreType.SUPERSTORE:
        # Do something for superstore option
        cfg = get_superstore()

    elif store_value == StoreType.LOBLAWS:
        # Do something for superstore option
        cfg = get_loblaws()
        
    else:
        raise Exception("Not implemented yet")

    # grab data file from cfg
    data_file = cfg.get("data_file")
    if os.path.exists(data_file):
        # read data file and sync with db, add current date as argument.
        # read data from data_file into dictionary
        # with open(data_file, 'r') as f:
        #     json_data = json.load(f)
        # # save data to db
        # print("what is json data: ", json_data)
        # add_to_db(json_data, cfg)
        pass
    else:
        pass

if __name__ == '__main__':
    # Set up the argument parser to get command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t", '--type', 
        type=str, 
        choices=['saveon', 'walmart', 'superstore', 'loblaws'], 
        default="walmart"
    )
    args = parser.parse_args()

    # Run the main async function using the event loop
    # The 'args' object must be passed to your main function
    uc.loop().run_until_complete(main(args))