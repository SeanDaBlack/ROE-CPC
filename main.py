import argparse
import csv
import random
import time
import requests
from faker import Faker
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium import webdriver
from bs4 import BeautifulSoup
from prompts import *
from cap import installCaptcha
from emails import MAIL_GENERATION_WEIGHTS
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

CLOUD_DESCRIPTION = 'Puts script in a \'cloud\' mode where the Chrome GUI is invisible'
CLOUD_DISABLED = False
CLOUD_ENABLED = True
MAILTM_DISABLED = False
MAILTM_ENABLED = True
EPILOG = ''
SCRIPT_DESCRIPTION = ''

account_created = False

# Option parsing
parser = argparse.ArgumentParser(SCRIPT_DESCRIPTION, epilog=EPILOG)
parser.add_argument('--cloud', action='store_true', default=CLOUD_DISABLED,
                    required=False, help=CLOUD_DESCRIPTION, dest='cloud')
parser.add_argument('--mailtm', action='store_true', default=MAILTM_ENABLED,
                    required=False, dest='mailtm')
parser.add_argument('-r', '--retry_amount', type=int, required=False, default=10,
                    help="Number of times to retry creating an account", dest='retry_amount')
args = parser.parse_args()

fake = Faker()


def pickCenter():

    # import csv file
    with open('./fake-clinic.csv', 'r') as csvfile:
        # create a csv reader
        reader = csv.reader(csvfile)
        # create a list of rows
        rows = list(reader)
        # create a list of columns

        # pick random number between 0 and the length of the list
        random_number = random.randint(0, len(rows)-1)

        names = [row[0] for row in rows]
        zips = [row[4] for row in rows]

        center = {'name': names[random_number], 'zip': zips[random_number]}

    return center


def start_driver(url):

    if (args.cloud == CLOUD_ENABLED):

        #driver = geckodriver("./extensions/Tampermonkey.xpi")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        options.add_argument("window-size=1200x600")
        driver = webdriver.Chrome(
            'chromedriver', options=options)

    else:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")
        # chrome_options.add_extension("./extensions/Tampermonkey.crx")
        driver = webdriver.Chrome(
            ChromeDriverManager().install(), options=options)

    '''
    ENABLE WHEN CAPTCHA IS NEEDED
    '''

    # installCaptcha(driver)

    driver.get(url)

    return driver


def doReview(driver, fake_identity, center, account_created, place_url):

    # If no account was created, create one
    if not account_created:
        try:
            account_created = createAccount(driver, fake_identity, center)
        except Exception as e:
            raise e
        getMailCode(driver, fake_identity)
        writeReview(driver, fake_identity, place_url)

    # If account was created, just write review
    else:
        writeReview(driver, fake_identity, place_url)


def createAccount(driver, fake_identity, center):

    print("No Account Created: Creating Account")
    # click on sign up button
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
        (By.XPATH, '/html/body/yelp-react-root/div[1]/div[2]/header/div/div[1]/div[3]/nav/div/div[2]/div/span[3]/a[2]'))).click()

    # wait for new screen to load
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
        (By.ID, 'signup-button')))

    # sleep random amount of time
    time.sleep(random.randint(1, 2))

    # send keys to first name
    driver.find_element(By.ID, 'first_name').send_keys(
        fake_identity['first_name'])

   # sleep random amount of time
    time.sleep(random.randint(0, 1))

    # send keys to last name
    driver.find_element(By.ID, 'last_name').send_keys(
        fake_identity['last_name'])

   # sleep random amount of time
    time.sleep(random.randint(0, 1))

    # send keys to email
    driver.find_element(By.ID, 'email').send_keys(fake_identity['email'])

   # sleep random amount of time
    time.sleep(random.randint(0, 1))

    # send keys to password
    driver.find_element(By.ID, 'password').send_keys(fake_identity['password'])

   # sleep random amount of time
    time.sleep(random.randint(0, 1))

    # send keys to zip code
    driver.find_element(By.ID, 'zip').send_keys(center['zip'])

    time.sleep(2)
    # click on sign up button
    driver.find_element(By.ID, 'signup-button').click()

    time.sleep(1)

    # Check if captcha is present
    if check_exists_by_xpath(driver, '//*[@id="extra-form-save"]'):
        print("No Captcha Present")

        driver.get(driver.find_element(By.XPATH,
                   '//*[@id="extra-form"]/div[3]/div[2]/a').get_attribute('href'))

        time.sleep(3)
        # print(driver.current_url)
        print('Confirming Email')

    else:
        print("Captcha Present, Solving Captcha")

        # switch to frame
        # driver.switch_to.frame("0rfap4u3001")
        driver.switch_to.frame(driver.find_element(
            by=By.TAG_NAME, value="iframe"))
        time.sleep(1)
        WebDriverWait(driver, 600).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'check')))
        # WebDriverWait(driver, 600).until(lambda _: len(visible(
        #     driver, '//div[@class="h-captcha"]/iframe').get_attribute('data-hcaptcha-response')) > 0)
        # driver.switch_to.default_content()
        print('Captcha Solved')

        driver.find_element(By.ID, 'signup-button').click()
        try:
            WebDriverWait(driver, 180).until(EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="extra-form-save"]'))).click()
        except:
            raise Exception("Captcha Failed")

    return True


def getMailCode(driver, fake_identity):

    for i in range(120):
        time.sleep(2)
        print("Checking for mail...")

        time.sleep(.5)

        mail = requests.get("https://api.mail.tm/messages?page=1", headers={
            'Authorization': 'Bearer ' + fake_identity['sid']}).json().get('hydra:member')

        #print("Checking if mail was received...")
        if mail:

            print("Mail received")
            # print((mail[0]['intro'].split('(')[1].split('&')[0]))

            driver.get((mail[0]['intro'].split('(')[1].split('&')[0]))

            break

    driver.execute_script("window.history.go(-1)")


def writeReview(driver, fake_idenity, url):

    # Open review page
    driver.get(url)

    # Click on the review button
    try:
        WebDriverWait(driver, 8).until(EC.element_to_be_clickable(
            (By.XPATH, '/html/body/yelp-react-root/div[1]/div[3]/div/div/div[2]/div/div[1]/main/div[2]/div[1]/a'))).click()
    except Exception as e:
        print(e)
        pass

    #print("review button clicked")

    # Select Rating
    try:
        WebDriverWait(driver, 8).until(EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(@name,'rating')]")))
        for i in range(len(driver.find_elements(
                By.XPATH, "//*[contains(@name,'rating')]"))):
            if i == 0:
                driver.find_elements(
                    By.XPATH, "//*[contains(@name,'rating')]")[i].click()

    except Exception as e:
        print(e)
        pass

    #print("Star Clicked")

    # Select Prompt for Review
    p = random.choice(PROMPTS)

    # Send prompt to text area
    actions = ActionChains(driver)
    actions.key_down(Keys.SPACE).send_keys(p)
    actions.perform()

    print(f"Prompt Sent: {p}")

    # Find Post button

    last_height = driver.execute_script("return document.body.scrollHeight")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    source_element = driver.find_element(
        By.XPATH, "//*[contains(text(),'Post Review')]")
    driver.execute_script(
        "arguments[0].setAttribute('data-activated',arguments[1])", source_element, 'true')

    # THIS IS AN ESSENTIAL SLEEP!!!
    time.sleep(5)

    # Click on the post review button
    ActionChains(driver).move_to_element(source_element).click(driver.find_element(
        By.XPATH, "//*[contains(text(),'Post Review')]")).perform()

    time.sleep(3)
    print(f"Review Created: {driver.current_url}")


def check_exists_by_xpath(driver, xpath):
    try:
        driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True


def createFakeIdentity():
    fake_identity = {}
    fake_identity['first_name'] = fake.first_name()
    fake_identity['last_name'] = fake.last_name()
    fake_identity['email'] = random_email(
        fake_identity['first_name'] + ' ' + fake_identity['last_name'] + str(random.randint(1, 999999)))
    fake_identity['password'] = fake.password()

    return fake_identity


def random_email(name=None):
    if name is None:
        name = fake.name()

    mailGens = [lambda fn, ln, *names: fn + ln,
                lambda fn, ln, *names: fn + "_" + ln,
                lambda fn, ln, *names: fn[0] + "_" + ln,
                lambda fn, ln, *names: fn + ln +
                str(int(1 / random.random() ** 3)),
                lambda fn, ln, *names: fn + "_" + ln +
                str(int(1 / random.random() ** 3)),
                lambda fn, ln, *names: fn[0] + "_" + ln + str(int(1 / random.random() ** 3)), ]

    return random.choices(mailGens, MAIL_GENERATION_WEIGHTS)[0](*name.split(" ")).lower() + "@" + requests.get(
        'https://api.mail.tm/domains').json().get('hydra:member')[0].get('domain')


def updateReviewNumber(fake_identity):
    # send post request to the server with the data to track the number of reviews
    requests.post('https://change-is-brewing.herokuapp.com/roe', fake_identity)


def createMail(fake_identity):
    # Create Email with MailTM

    ran_email = random_email(
        fake_identity['first_name'] + ' ' + fake_identity['last_name'] + str(random.randint(1, 99999)))

    print(f"USING MAILTM TO CREATE EMAIL")
    fake_email = requests.post('https://api.mail.tm/accounts', data='{"address":"'+ran_email+'","password":" "}', headers={
        'Content-Type': 'application/json'}).json().get('address')
    mail_sid = requests.post('https://api.mail.tm/token', data='{"address":"'+fake_email+'","password":" "}', headers={
        'Content-Type': 'application/json'}).json().get('token')

    fake_identity['sid'] = mail_sid
    fake_identity['email'] = fake_email
    print(f"EMAIL CREATED")

    return fake_identity


if __name__ == "__main__":

    total_reviews = 0
    account_created = False
    center_counter = 0

    while True:

        print("Picking Center")
        center = pickCenter()
        center_counter += 1
        if center_counter > (args.retry_amount):
            print("Request Limit Reached, Please Try Again Later")
            exit()
        c = center['name'].replace(
            " - ", "-").replace(" ", "+").replace("&", "%26")
        url = 'https://www.google.com/search?q={0}+{1}+{2}'.format(
            c, center['zip'], "\"yelp\"")

        page = requests.get(url)

        soup = BeautifulSoup(page.text, "html.parser")

        for link in soup.find_all('a'):
            if 'https://www.yelp.com/biz/' in link.get('href'):

                # print(link.get('href').split('&')[0])
                url = link.get('href').split('=')[1].split('&')[0]

                page = requests.get(url)
                soup = BeautifulSoup(page.text, "html.parser")

                # check for string in page
                if "Crisis Pregnancy Centers" in page.text:

                    if not account_created:
                        print(f"Picked Center: {center['name']}")
                        driver = start_driver(url)
                        fake_identity = createFakeIdentity()

                        fake_identity = createMail(fake_identity)
                        print(fake_identity['email'],
                              fake_identity['password'])
                    else:
                        print(f"Picked Center: {center['name']}")
                        driver.get(url)

                    try:
                        doReview(driver, fake_identity,
                                 center, account_created, url)
                    except Exception as e:
                        print(e)
                        break
                    time.sleep(10)
                    account_created = True
                    total_reviews += 1
                    print(f'{total_reviews} Review Posted')
                    updateReviewNumber(fake_identity)
                    center_counter = 0
                    break
