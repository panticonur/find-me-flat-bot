from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import utils


def open(page_name):
    try:
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        # driver.set_window_position(0, 1500)

        return open_page(driver, page_name)
    
    except WebDriverException as e:
        utils.log("WebDriver error: {e}")
    except Exception as e:
        utils.log("Iteration failed: {e}")


def open_page(driver, page_name):
    try:
        driver.get(page_name)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        page_source = driver.page_source
        driver.quit()
        return page_source
    
    except WebDriverException as e:
        utils.log("WebDriver error while opening page: {e}")
    except Exception as e:
        utils.log("Failed to open page: {e}")