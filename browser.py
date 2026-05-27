from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import utils
from pyvirtualdisplay.display import Display


def open(page_name):
    driver = None
    display = None
    try:
        display = Display(visible=False, size=(1920, 1080))
        display.start()

        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=options)
        # driver.set_window_position(0, 1500)

        return open_page(driver, page_name)
    
    except WebDriverException as e:
        utils.log(f"WebDriver error: {e}")
    except Exception as e:
        utils.log(f"Iteration failed: {e}")
    finally:
        if driver is not None:
            driver.quit()
        if display is not None:
            display.stop()


def open_page(driver, page_name):
    try:
        driver.get(page_name)
        print(f"Page Title: {driver.title}")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        page_source = driver.page_source
        return page_source
    
    except WebDriverException as e:
        utils.log("WebDriver error while opening page: {e}")
    except Exception as e:
        utils.log("Failed to open page: {e}")
