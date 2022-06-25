import argparse
import csv
import random
import time
import requests
from faker import Faker
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from bs4 import BeautifulSoup

from emails import MAIL_GENERATION_WEIGHTS
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import NoSuchElementException

CLOUD_DESCRIPTION = 'Puts script in a \'cloud\' mode where the Chrome GUI is invisible'
CLOUD_DISABLED = False
CLOUD_ENABLED = True
MAILTM_DISABLED = False
MAILTM_ENABLED = True
EPILOG = ''
SCRIPT_DESCRIPTION = ''

FAKE_CLINIC_REVIEW = '''
Crisis Pregnancy Centers such as this don't provide abortion services or refer to anywhere that does. Although their name and site might make it sound like they will provide ALL choices for a pregnancy; they will only coerce you into keeping the fetus, even if that wouldn't be best for your situation. For full resouces, please visit https://innedana.com or https://www.plannedparenthood.org/.
'''

user_name = ''
yelp_password = ''

account_created = False

# Option parsing
parser = argparse.ArgumentParser(SCRIPT_DESCRIPTION, epilog=EPILOG)
parser.add_argument('--cloud', action='store_true', default=CLOUD_DISABLED,
                    required=False, help=CLOUD_DESCRIPTION, dest='cloud')
parser.add_argument('--mailtm', action='store_true', default=MAILTM_DISABLED,
                    required=False, dest='mailtm')
args = parser.parse_args()

fake = Faker()


def pickCenter():

    # import csv file
    with open('fake-clinic.csv', 'r') as csvfile:
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

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-running-insecure-content')
        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
        chrome_options.add_argument(f'user-agent={user_agent}')

        driver = webdriver.Chrome('chromedriver', options=chrome_options)
    else:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled")
        # chrome_options.add_extension("./extensions/cap.crx")
        driver = webdriver.Chrome(
            ChromeDriverManager().install(), options=chrome_options)

    driver.get(url)
    # driver.implicitly_wait(10)
    # WebDriverWait(driver, 10).until(
    #     expected_conditions.presence_of_element_located((By.XPATH, APPLY_NOW_BUTTON_1)))

    # time.sleep(1000)

    return driver


def doReview(driver, fake_identity, center, account_created):

    if not account_created:

        try:
            account_created = createAccount(driver, fake_identity, center)
        except Exception as e:
            raise e
        getMailCode(driver, fake_identity)
        writeReview(driver, fake_identity)
    else:
        #loginAccount(driver, fake_identity)
        writeReview(driver, fake_identity)


def loginAccount(driver, fake_identity):
    # Click Log in button
    driver.find_element(
        By.XPATH, '/html/body/yelp-react-root/div[1]/div[2]/header/div/div[1]/div[3]/nav/div/div[2]/div/span[3]/a[1]')

    driver.find_element(By.ID, 'email').send_keys(
        fake_identity['email'])
    driver.find_element(By.ID, 'password').send_keys(
        fake_identity['password'])

    # Click Log in button
    driver.find_element(
        By.XPATH, '/html/body/div[2]/div[2]/div/div[4]/div[1]/div/div/div[5]/div[1]/form/button').click()


def writeReview(driver, fake_idenity):
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
        (By.XPATH, '/html/body/yelp-react-root/div[1]/div[3]/div/div/div[2]/div/div[1]/main/div[2]/div[1]/a'))).click()


def createAccount(driver, fake_identity, center):
    # click on sign up button
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
        (By.XPATH, '/html/body/yelp-react-root/div[1]/div[2]/header/div/div[1]/div[3]/nav/div/div[2]/div/span[3]/a[2]'))).click()

    # wait for new screen to load

    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
        (By.ID, 'signup-button')))

    # sleep random amount of time
    time.sleep(random.randint(1, 3))

    # send keys to first name
    driver.find_element(By.ID, 'first_name').send_keys(
        fake_identity['first_name'])

   # sleep random amount of time
    time.sleep(random.randint(0, 2))

    # send keys to last name
    driver.find_element(By.ID, 'last_name').send_keys(
        fake_identity['last_name'])

   # sleep random amount of time
    time.sleep(random.randint(0, 2))

    # send keys to email
    driver.find_element(By.ID, 'email').send_keys(fake_identity['email'])

   # sleep random amount of time
    time.sleep(random.randint(0, 2))

    # send keys to password
    driver.find_element(By.ID, 'password').send_keys(fake_identity['password'])

   # sleep random amount of time
    time.sleep(random.randint(0, 2))

    # send keys to zip code
    driver.find_element(By.ID, 'zip').send_keys(center['zip'])

    time.sleep(2)
    # click on sign up button
    driver.find_element(By.ID, 'signup-button').click()

    time.sleep(15)

    if check_exists_by_xpath(driver, 'extra-form-save'):
        driver.find_element(By.XPATH, '//*[@id="extra-form-save"]').click()
    else:
        print('Solve Captcha')
        try:
            WebDriverWait(driver, 120).until(EC.visibility_of_element_located(
                (By.XPATH, '//*[@id="extra-form-save"]'))).click()
        except:
            raise Exception("Captcha Failed")

    return True


def check_exists_by_xpath(driver, xpath):
    try:
        driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True


def getMailCode(driver, fake_identity):

    # original_window = driver.current_window_handle

    for i in range(120):
        time.sleep(1.5)
        print("Checking for mail...")
        if (args.mailtm == MAILTM_DISABLED):
            mail = requests.get(
                f'https://api.guerrillamail.com/ajax.php?f=check_email&seq=1&sid_token={fake_identity.get("sid")}').json().get('list')

            if mail:
                print(mail)
                # passcode = re.findall('(?<=n is ).*?(?=<)', requests.get(
                #     f'https://api.guerrillamail.com/ajax.php?f=fetch_email&email_id={mail[0].get("mail_id")}&sid_token={fake_identity.get("sid")}').json().get('mail_body'))[0]
                break

        elif (args.mailtm == MAILTM_ENABLED):
            print("Retrieving mail...")
            time.sleep(.5)

            mail = requests.get("https://api.mail.tm/messages?page=1", headers={
                'Authorization': f'Bearer {fake_identity.get("sid")}'}).json().get('hydra:member')
            while not mail:
                time.sleep(1)
                mail = requests.get("https://api.mail.tm/messages?page=1", headers={
                    'Authorization': f'Bearer {fake_identity.get("sid")}'}).json().get('hydra:member')
            print("Checking if mail was received...")
            if mail:

                print((mail[0]['intro'].split('(')[1].split('&')[0]))

                driver.get((mail[0]['intro'].split('(')[1].split('&')[0]))

                print("Mail received")
            break

    driver.execute_script("window.history.go(-1)")


def createFakeIdentity():
    fake_identity = {}
    fake_identity['first_name'] = fake.first_name()
    fake_identity['last_name'] = fake.last_name()
    fake_identity['email'] = random_email(
        fake_identity['first_name'] + ' ' + fake_identity['last_name'] + str(random.randint(1, 99999)))
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


def createMail(fake_identity):
    # Create Email with MailTM
    if (args.mailtm == MAILTM_DISABLED):
        print(f"USING GUERRILLA TO CREATE EMAIL")
        response = requests.get(
            'https://api.guerrillamail.com/ajax.php?f=get_email_address').json()

        fake_email = response.get('email_addr')
        mail_sid = response.get('sid_token')
        print(f"EMAIL CREATED")
        fake_identity['sid'] = mail_sid
        fake_identity['email'] = fake_email
    elif (args.mailtm == MAILTM_ENABLED):

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

    fake_identity = createFakeIdentity()

    fake_identity = createMail(fake_identity)
    account_created = False
    print(fake_identity)

    while True:

        print("Picking Center")
        center = pickCenter()
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
                        driver = start_driver(url)
                    else:
                        driver.get(url)
                    try:
                        doReview(driver, fake_identity,
                                 center, account_created)
                    except Exception as e:
                        print(e)
                        break
                    time.sleep(10)
                    account_created = True
                    print('Review Posted')