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
        if not any(fname.endswith(".crdownload") for fname in os.listdir(download_dir)):
            return True
        time.sleep(1)
        seconds += 1
    return False  # Timeout reached


def download(url: str, download_dir: str) -> None:
    """
    Use Selenium-driven Chrome to download a PDF from the given URL.

    Parameters:
        url (str): The direct PDF URL to download.
        download_dir (str): The directory where the PDF will be saved.
    """
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1,1")
    chrome_options.add_argument("--window-position=0,1280")

    # Set preferences to automatically download PDFs instead of opening them.
    prefs = {
        "download.default_directory": os.path.abspath(download_dir),  # Must be an absolute path
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": os.path.abspath(download_dir)})
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        # Allow some time for the download to be triggered.
        time.sleep(8)
        if _wait_for_download(download_dir, timeout=60):
            print("Download completed.")
        else:
            print("Download did not complete within the timeout period.")
    finally:
        driver.quit()

    print(f"File should be downloaded to '{download_dir}' for URL: {url}")


if __name__ == "__main__":
    # Example usage for a single APS PDF download.
    file_url = "https://journals.aps.org/prl/pdf/10.1103/PhysRevLett.134.098401"
    download_directory = os.getcwd()
    download(file_url, download_directory)
