from selenium import webdriver
from selenium.common.exceptions import TimeoutException as TE
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as WDW
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service as SG
from webdriver_manager.firefox import GeckoDriverManager as GDM

import requests

SCRIPT_URL = 'https://greasyfork.org/fr/scripts/445478-hcaptcha-solver'


def installCaptcha(driver):
    print("Installing captcha script...")
    download_userscript(driver)


def installCloudCaptcha(driver):
    print("Installing captcha script...")
    download_clouduserscript(driver)


def clickable(driver, element: str) -> None:
    """Click on an element if it's clickable using Selenium."""
    try:
        WDW(driver, 5).until(EC.element_to_be_clickable(
            (By.XPATH, element))).click()
    except Exception:  # Some buttons need to be visible to be clickable,
        driver.execute_script(  # so JavaScript can bypass this.
            'arguments[0].click();', visible(driver, element))


def visible(driver, element: str):
    """Check if an element is visible using Selenium."""
    return WDW(driver, 5).until(
        EC.visibility_of_element_located((By.XPATH, element)))


def window_handles(driver, window_number: int) -> None:
    """Check for window handles and wait until a specific tab is opened."""
    WDW(driver, 10).until(lambda _: len(
        driver.window_handles) > window_number)
    driver.switch_to.window(  # Switch to the asked tab.
        driver.window_handles[window_number])


def updateReviewNumber():
    # send post request to the server with the data
    requests.post('"https://change-is-brewing.herokuapp.com/roe')


def download_userscript(driver):
    """Download the hCaptcha solver userscript."""

    try:  # Download and install the userscript.
        print('Adding the hCAPTCHA solver userscript.', end=' ')
        window_handles(driver, 1)  # Wait that Tampermonkey tab loads.
        driver.get(SCRIPT_URL)  # Go to the userscript URL page.
        # Click on the "Install" GreasyFork button.
        clickable(driver, '//*[@id="install-area"]/a[1]')
        # Click on "Install" Tampermonkey button.
        window_handles(driver, 2)  # Switch to the Tampermonkey tab.
        clickable(driver, '//*[@value="Install"]')
        window_handles(driver, 1)  # Switch to the GreasyFork tab.
        driver.close()  # Close the GreasyFork tab.
        window_handles(driver, 0)  # Switch to main tab.

        print(f'Installed.')
    except TE:  # Something went wrong.
        print(f'Failed.')
        quit()  # Close the webdriver.
        exit()  # Exit the program.


def download_clouduserscript(driver):
    """Download the hCaptcha solver userscript."""
    original_context = driver.window_handles[0]
    # print(original_context)
    try:  # Download and install the userscript.
        print('Adding the hCAPTCHA solver userscript.', end=' ')
        window_handles(driver, 0)  # Wait that Tampermonkey tab loads.
        driver.get(SCRIPT_URL)  # Go to the userscript URL page.

        # Click on the "Install" GreasyFork button.
        clickable(driver, '//*[@id="install-area"]/a[1]')
        # Click on "Install" Tampermonkey button.
        for i in range(len(driver.window_handles)):
            window_handles(driver, i)  # Switch to the Tampermonkey tab.
            try:
                clickable(driver, '//*[@value="Install"]')
            except:
                # print('failed')
                continue

        # window_handles(driver, 2)  # Switch to the GreasyFork tab.
        # print(driver.window_handles)
        # driver.close()  # Close the GreasyFork tab.
        window_handles(driver, 0)  # Switch to main tab.

        # print(driver.window_handles)

        print(f'Installed.')
    except TE:  # Something went wrong.
        print(f'Failed.')
        quit()  # Close the webdriver.
        exit()  # Exit the program.


def geckodriver(extension_path):
    binary = '/usr/bin/firefox/firefox'
    options = webdriver.FirefoxOptions()  # Options for the GeckoDriver.
    # Set the webdriver language to English (US).
    options.set_preference('intl.accept_languages', 'en,en-US')
    # add binary to options
    options.binary_location = binary
    options.add_argument('--headless')
    options.add_argument('--log-level=3')  # Not logs will be displayed.
    options.add_argument('--mute-audio')  # Audio is muted.
    options.add_argument(  # Enable the WebGL Draft extension.
        '--enable-webgl-draft-extensions')
    options.add_argument('--disable-infobars')  # Disable popup
    options.add_argument('--disable-popup-blocking')  # and info bars.
    driver = webdriver.Firefox(service=SG(GDM(  # Start the webdriver.
        log_level=0).install()), options=options)
    driver.install_addon(extension_path)  # Add extension.
    driver.maximize_window()  # Maximize window to reach all elements.
    return driver
