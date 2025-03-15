import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def _wait_for_download(download_dir, timeout=60):
    """
    Wait until there are no .crdownload files in the download directory,
    indicating that downloads have completed, or until timeout (in seconds) is reached.
    """
    seconds = 0
    while seconds < timeout:
        # Check if any file in download_dir ends with .crdownload.
        if not any(fname.endswith(".crdownload") for fname in os.listdir(download_dir)):
            return True
        time.sleep(1)
        seconds += 1
    return False  # Timeout reached


def download(url: str, download_dir: str) -> None:
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1,1")
    chrome_options.add_argument("--window-position=0,1280")

    # Set preferences to automatically download PDFs instead of opening them.
    prefs = {
        "download.default_directory": download_dir,  # Must be an absolute path!
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # Initialize the Chrome driver (ensure chromedriver is installed and in PATH)
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": download_dir})
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(8)
        if _wait_for_download(download_dir, timeout=60):
            print("Download completed.")
    finally:
        driver.quit()

    print(f"File should be downloaded to '{download_dir}' for URL: {url}")


if __name__ == "__main__":
    file_url = "https://pubs.acs.org/doi/pdf/10.1021/acs.jcim.4c02240?download=true"
    download_directory = os.getcwd()

    download(file_url, download_directory)
