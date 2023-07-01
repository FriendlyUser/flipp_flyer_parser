import undetected_chromedriver as uc
import time
import json
import re
import selenium.webdriver.support.expected_conditions as EC
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
def get_walmart():
    """
    Get the information about Walmart.
    Returns:
        None
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
    main_element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.TAG_NAME, "main")))
    time.sleep(5)
    # Switch to the iframe
    iframe = main_element.find_element(By.CLASS_NAME, "flippiframe.mainframe")
    driver.switch_to.frame(iframe)
    # save content as data/walmart.html
    cookies = driver.get_cookies()
    # save cookies are cookies.json
    with open("data/cookies.json", "w") as f:
        json.dump(cookies, f)
    
    # get source html for driver
    html = driver.page_source

    # save to data/html
    with open("data/walmart.html", "w", errors="ignore", encoding="utf-8") as f:
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

    for flyer_image in flyer_images:
        # time sleep 5
        # get each button from flyer
        buttons = flyer_image.find_elements(By.TAG_NAME, "button")
        # iterate through each button
        for index, button in enumerate(buttons):
            if index == 0:
                continue
            # click on button
            # print aria-label for button
            print(button.get_attribute("aria-label"))
            # scroll so button is centered
            # driver.execute_script("arguments[0].scrollIntoView();", button)
            button.click()
            time.sleep(5)
            # screenshot
            driver.save_screenshot("data/full_screenshot.png")

            exit(1)
        exit(1)
    driver.witch_to.default_content()

    time.sleep(5)

if __name__ == '__main__':    
    get_walmart()