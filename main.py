import os
from datetime import datetime
import sys

import GmailExtractor_acs
import GmailExtractor_aps
import Download_acs
import Download_aps
import SiliconFlow


ACS = True
APS = True


if __name__ == "__main__":

    sys.stdout.reconfigure(encoding="utf-8")

    ############################################
    ####            ACS Journals            ####
    ############################################
    if ACS:
        #  Step 1. Get downloading url from Gmail
        with open("./data/acs_email_links.txt", "w") as f:
            f.write("")
        GmailExtractor_acs.check_gmail(max_num=10)

        #  Step 2. Downloading pdfs
        download_directory = os.path.abspath("./data/acs_downloaded_pdfs")
        os.makedirs(download_directory, exist_ok=True)
        Download_acs.process_urls_and_download("./data/acs_email_links.txt", download_directory)

        #  Step 3. Process the pdfs and give them to the LLM
        pdf_directory = os.path.abspath("./data/acs_downloaded_pdfs")

        output_directory = os.path.join(os.getcwd(), "summary/")
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        output_name = f"acs-summary-{datetime.now().strftime('%Y-%m-%d')}.txt"

        processed_dir_acs = "data/acs_summarized_pdfs"

        with open("config/api.txt", "r") as f:
            lines = f.readlines()
        api_key = lines[0]

        num_try = 0
        patience = 5
        while os.listdir(pdf_directory) and num_try < patience:
            num_try += 1
            SiliconFlow.process_pdfs_in_directory(
                pdf_directory, processed_dir_acs, api_key, output_directory, output_name=output_name, j_type="acs"
            )

    ############################################
    ####            APS Journals            ####
    ############################################
    if APS:
        #  Step 1. Get downloading url from Gmail
        with open("./data/aps_email_links.txt", "w") as f:
            f.write("")
        GmailExtractor_aps.check_gmail(max_num=10)

        #  Step 2. Downloading pdfs
        download_directory = os.path.abspath("./data/aps_downloaded_pdfs")
        os.makedirs(download_directory, exist_ok=True)
        Download_aps.process_urls_and_download("./data/aps_email_links.txt", download_directory)

        #  Step 3. Process the pdfs and give them to the LLM
        pdf_directory = os.path.abspath("./data/aps_downloaded_pdfs")

        output_directory = os.path.join(os.getcwd(), "summary/")
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        output_name = f"aps-summary-{datetime.now().strftime('%Y-%m-%d')}.txt"

        processed_dir_acs = "data/aps_summarized_pdfs"

        with open("config/api.txt", "r") as f:
            lines = f.readlines()
        api_key = lines[0]

        num_try = 0
        patience = 5
        while os.listdir(pdf_directory) and num_try < patience:
            num_try += 1
            SiliconFlow.process_pdfs_in_directory(
                pdf_directory, processed_dir_acs, api_key, output_directory, output_name=output_name, j_type="aps"
            )
