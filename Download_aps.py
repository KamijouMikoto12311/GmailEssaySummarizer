import os
import requests
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from util.single_download_aps import download


def _modify_aps_url(url: str) -> str:
    """
    Convert an APS abstract URL into a PDF URL.

    For example, convert:
    https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.134.098401?utm_source=email&utm_medium=email&utm_campaign=prl-alert
    to:
    https://journals.aps.org/prl/pdf/10.1103/PhysRevLett.134.098401

    Parameters:
        url (str): The URL after redirection.

    Returns:
        str: The modified URL pointing to the PDF.
    """
    parsed = urllib.parse.urlsplit(url)
    scheme = parsed.scheme
    netloc = parsed.netloc
    path = parsed.path

    new_path = path.replace("/abstract/", "/pdf/")
    new_url = f"{scheme}://{netloc}{new_path}"
    return new_url


def get_original_urls(file_name: str):
    """
    Read the input file and extract lines containing URLs.
    """
    with open(file_name, "r", encoding="utf-8") as file:
        links = [line.strip() for line in file if "http" in line]
    return links


def get_download_url(url: str) -> str:
    """
    Follow redirections for the provided URL and modify it to obtain the PDF URL.
    """
    try:
        response = requests.get(url, allow_redirects=True)
        clean_url = response.url
        download_url = _modify_aps_url(clean_url)
        return download_url
    except requests.exceptions.RequestException as e:
        print(f"Error processing URL {url}: {e}")
        return None


def download_multiple_pdfs(urls: list, download_dir: str) -> None:
    """
    Download multiple PDFs concurrently using a thread pool.
    """
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(download, url, download_dir): url for url in urls if url}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error downloading {futures[future]}: {e}")


def process_urls_and_download(input_file: str, download_dir: str):
    """
    Process URLs from the input file: modify them to point to the PDF,
    then download them concurrently.
    """
    original_urls = get_original_urls(input_file)

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(get_download_url, url): url for url in original_urls}
        urls_to_download = []
        for future in as_completed(futures):
            try:
                download_url = future.result()
                if download_url:
                    urls_to_download.append(download_url)
            except Exception as e:
                print(f"Error modifying URL: {e}")

    download_multiple_pdfs(urls_to_download, download_dir)


if __name__ == "__main__":
    download_directory = os.path.abspath("./data/aps_downloaded_pdfs")
    os.makedirs(download_directory, exist_ok=True)

    input_file = "./data/aps_email_links.txt"
    process_urls_and_download(input_file, download_directory)
