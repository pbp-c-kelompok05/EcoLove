import os
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class MarketplaceFunctionalTest(StaticLiveServerTestCase):

    def setUp(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')

        self.browser = webdriver.Chrome(options=chrome_options)
        self.browser.implicitly_wait(10)

        self.user = User.objects.create_user(
            username='karen',
            password='password123'
        )

    def tearDown(self):
        self.browser.quit()

    def _click(self, element):
        self.browser.execute_script("arguments[0].click();", element)

    def test_full_crud_marketplace_flow(self):
        # 1. Login
        self.browser.get(f"{self.live_server_url}/login/")
        self.browser.find_element(By.NAME, "username").send_keys("karen")
        self.browser.find_element(By.NAME, "password").send_keys("password123")
        login_btn = self.browser.find_element(
            By.XPATH, "//form[.//input[@name='username']]//button[@type='submit']"
        )
        self._click(login_btn)

        # 2. Go to My Marketplace
        self.browser.get(f"{self.live_server_url}/marketplace/my-marketplace/")
        self.assertIn("My Marketplace", self.browser.page_source)

        # 3. Add (Sell New Item)
        add_item_button = self.browser.find_element(By.CLASS_NAME, "add-new-card")
        self._click(add_item_button)

        self.browser.find_element(By.NAME, "name").send_keys("Selenium Eco Mug")
        # price = IntegerField -> harus bilangan bulat (bukan 12.50)
        self.browser.find_element(By.NAME, "price").send_keys("12")
        self.browser.find_element(By.NAME, "description").send_keys("Testing via Selenium.")

        category_select = self.browser.find_element(By.NAME, "category")
        category_select.send_keys("Others")

        add_submit = self.browser.find_element(
            By.XPATH, "//form[.//input[@name='name']]//button[@type='submit']"
        )
        self._click(add_submit)

        # Tunggu redirect balik ke My Marketplace, lalu item muncul
        WebDriverWait(self.browser, 10).until(EC.url_contains("my-marketplace"))
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Selenium Eco Mug')]"))
        )
        self.assertIn("Selenium Eco Mug", self.browser.page_source)

        # 4. Edit Item
        edit_btn = self.browser.find_element(By.XPATH, "//a[contains(text(), 'Edit')]")
        self._click(edit_btn)

        name_input = self.browser.find_element(By.NAME, "name")
        name_input.clear()
        name_input.send_keys("Updated Eco Mug")

        edit_submit = self.browser.find_element(
            By.XPATH, "//form[.//input[@name='name']]//button[@type='submit']"
        )
        self._click(edit_submit)

        WebDriverWait(self.browser, 10).until(EC.url_contains("my-marketplace"))
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Updated Eco Mug')]"))
        )
        self.assertIn("Updated Eco Mug", self.browser.page_source)

        # 5. Delete Item via AJAX
        delete_btn = self.browser.find_element(By.XPATH, "//button[contains(text(), 'Delete')]")
        self._click(delete_btn)

        WebDriverWait(self.browser, 5).until(EC.alert_is_present())
        alert = self.browser.switch_to.alert
        alert.accept()

        WebDriverWait(self.browser, 10).until(
            EC.invisibility_of_element_located((By.XPATH, "//*[contains(text(), 'Updated Eco Mug')]"))
        )
        self.assertNotIn("Updated Eco Mug", self.browser.page_source)