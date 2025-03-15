import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from util.single_download_acs import download


def _modify_acs_url(url):
    base_url = "https://pubs.acs.org/doi/pdf/"
    if "doi/" in url:
        doi = url.split("doi/")[1].split("?")[0]
        return f"{base_url}{doi}?download=true"
    return url


def get_original_urls(file_name):
    with open(file_name, "r") as file:
        links = [line.strip() for line in file if "http" in line]
    return links


def get_download_url(url):
    try:
        response = requests.get(url, allow_redirects=True)
        clean_url = response.url
        download_url = _modify_acs_url(clean_url)
        return download_url
    except requests.exceptions.RequestException as e:
        print(f"Error processing URL {url}: {e}")
        return None


def download_multiple_pdfs(urls: list, download_dir: str) -> None:
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(download, url, download_dir): url for url in urls if url}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error downloading {futures[future]}: {e}")


def process_urls_and_download(input_file: str, download_dir: str):
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
    download_directory = os.path.abspath("./data/acs_downloaded_pdfs")
    os.makedirs(download_directory, exist_ok=True)

    input_file = "./data/acs_email_links.txt"
    process_urls_and_download(input_file, download_directory)
