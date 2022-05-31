from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium_stealth import stealth
from bs4 import BeautifulSoup
from time import sleep
from random import uniform, randint
import re
import json
import logging
import coloredlogs
import ctypes


class Worker:
    def __init__(self):
        self._contests_host = 'https://lolz.guru/forums/contests/'
        self._config = self._load_config()
        self._stealth_options = self._setup_stealth_options()
        self._driver = self._create_webdriver()
        self._logger = self._create_logger()
        
        self._set_command_prompt_title('LZT SOLUTINS | 0')
    
    def _set_command_prompt_title(self, text):
        ctypes.windll.kernel32.SetConsoleTitleW(text)
    
    def _create_logger(self):
        logger = logging.getLogger('logger')

        COLOREDLOGS_LOG_FORMAT = '\033[1m\033[92m[LZT SOLUTIONS]\033[0m | %(asctime)s | %(levelname)s | %(message)s'
        COLOREDLOGS_DATE_FORMAT = '%H:%M:%S'
        COLOREDLOGS_FIELD_STYLES = {
            'asctime': {'color': 'yellow'},
            'levelname': {'color': 'blue', 'bold': True},
            'message': {'color': 'blue', 'bold': True},
        }
        COLOREDLOGS_LEVEL_STYLES = {
            'warning': {'color': 'red'},
            'debug': {'color': 'green'}
        }
        coloredlogs.install(level='DEBUG',
                            logger=logger,
                            isatty=True,
                            fmt=COLOREDLOGS_LOG_FORMAT,
                            datefmt=COLOREDLOGS_DATE_FORMAT,
                            level_styles=COLOREDLOGS_LEVEL_STYLES,
                            field_styles=COLOREDLOGS_FIELD_STYLES,
                            )

        return logger   
    
    def _load_config(self):
        with open('config.json', 'r', encoding='utf-8') as file:
            return json.load(file)

    def _setup_stealth_options(self):
        options = webdriver.ChromeOptions()

        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("--disable-impl-side-painting")
        options.add_argument("--disable-accelerated-2d-canvas")
        options.add_argument("--disable-accelerated-jpeg-decoding")
        options.add_argument("--no-sandbox")
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument("--disable-extensions")
        options.add_argument("--headless")
        options.add_argument('--window-size=1920,1080')
        options.add_argument(f'--user-agent={self._config["user-agent"]}')
        options.add_argument("--test-type=ui")
        options.add_argument(f'--user-data-dir={self._config["chrome_dir"]}')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("prefs", {
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })

        return options

    def _add_cookies(self, driver):
        raw_cookies = self._config['cookies']

        driver.get(self._contests_host)
        
        if len(raw_cookies) > 0:
            splited_by_semicolon = raw_cookies.split('; ')
            cookies = [{'name': line.split('=')[0], 'value': line.split('=')[
                1]} for line in splited_by_semicolon]

            for cookie in cookies:
                self._driver.add_cookie(cookie)
            
            driver.get(self._contests_host)
        else:
            self._logger.warning('Cookies was didnt set')

    def _create_webdriver(self):
        caps = DesiredCapabilities().CHROME
        caps["pageLoadStrategy"] = "eager"

        driver = webdriver.Chrome(
            executable_path='chromedriver.exe', options=self._stealth_options, desired_capabilities=caps)

        stealth(driver,
                vendor='Google Inc.',
                renderer=self._config['webgl']['renderer'],
                webgl_vendor=self._config['webgl']['vendor'],
                platform=self._config['webgl']['platform'],
                languages=self._config['webgl']['language'],
                fix_hairline=True,
                )

        return driver

    def _get_thread_urls(self, page_source):
        soup = BeautifulSoup(page_source, 'lxml')
        latest_threads = soup.find('div', {'class': 'latestThreads _insertLoadedContent'})
        
        if latest_threads:
            threads = latest_threads.find_all('div', {'id': re.compile('thread-')})

            return [f'https://lolz.guru/threads/{thread["id"].split("-")[1]}/' for thread in threads if not thread.find('i', {'class': 'fa fa fa-check alreadyParticipate Tooltip'})]
        else:
            return False

    def _is_logged(self, page_source):
        soup = BeautifulSoup(page_source, 'lxml')

        return False if soup.find('a', {'class': 'button primary login-and-signup-btn'}) else (True, soup.find('b', {'id': 'NavigationAccountUsername'}).find('span', {'class': 'style2'}).getText())
        
    def main(self):
        logger = self._logger

        good_threads_count = 0
        
        logger.info('Creating web driver')
        driver = self._driver
        
        logger.info('Adding cookies')
        self._add_cookies(driver)
        
        logger.info('Checking if the account is logged')
        is_logged = self._is_logged(driver.page_source)
        
        if is_logged[0]:
            action = webdriver.ActionChains(driver)
            logger.info(f'Successful login with a nickname \033[1m\033[92m{is_logged[1]}\033[0m')
            
            while True:
                threads_list = self._get_thread_urls(driver.page_source)
                
                if threads_list:
                    logger.info(f'{len(threads_list)} threads parsed')
                    
                    for thread in threads_list:
                        logger.info(f'Loading {thread}')
                        
                        sleep(uniform(0.5, 3))
                        
                        driver.get(thread)
                        button = driver.find_element_by_xpath('.//a[contains(@class,"LztContest--Participate button mn-15-0-0 primary")]')
                        
                        if button:
                            sleep(uniform(5, 30))
                            action.move_to_element(button).click().perform()
                            
                            good_threads_count += 1
                            self._set_command_prompt_title(f'LZT SOLUTIONS | {good_threads_count}')
                            
                            logger.info(f'\033[1m\033[92mSuccessfully participating in the {thread}\033[0m')
                            sleep(uniform(0.1, 1))
                            driver.get(self._contests_host)
                            
                logger.info('Waiting 120 second for new threads')    
                sleep(120)
                driver.get(self._contests_host)
        else:
            logger.warning('Cant log into account')
            
        driver.close()
        driver.quit()
