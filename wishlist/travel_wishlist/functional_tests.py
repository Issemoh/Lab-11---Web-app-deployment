from django.test import LiveServerTestCase
from selenium.webdriver.chrome.webdriver import WebDriver


class TitleTest(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver("D:/Python programs/Travel wishlist/wishlist/travel_wishlist/chromedriver.exe")
        cls.selenium.implicitly_wait(20)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_title_in_homepage(self):
        self.selenium.get(self.live_server_url)
        # c
        self.assertIn("Travel Wishlist", self.selenium.title)


class AddPlacesTest(LiveServerTestCase):

    fixtures = ["test_places"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver("D:/Python programs/Travel wishlist/wishlist/travel_wishlist/chromedriver.exe")
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_add_a_new_place(self):
        self.selenium.get(self.live_server_url)
        input_name = self.selenium.find_element_by_id("id_name")  # Finding text box
        input_name.send_keys("Japan")  # Putting "Japan" in textbox

        add_button = self.selenium.find_element_by_id("add-new-place")
        add_button.click()  # Click on @add button

        japan = self.selenium.find_element_by_class_name("place-name")
        self.assertEqual("Japan", japan.text)  # Checking if "Japan" is added or not

        # Checking all added unvisited data in page sources
        self.assertIn("Japan", self.selenium.page_source)
        self.assertIn("New York", self.selenium.page_source)
        self.assertIn("Tokyo", self.selenium.page_source)
