# README

## Project Overview

This project is designed to extract links containing specific keywords from designated email addresses (e.g., `journalalerts@acs.org`) and automatically download the PDF files that those links point to. It utilizes the Gmail API to read emails and Selenium to automate the browser for PDF downloads.

## Dependencies Installation

Before running the project, please ensure that all necessary dependencies are installed. You can install them using the following command:

```sh
pip install -r requirements.txt
```

## Run the Program

Copy your SiliconFlow api to `./config/api.txt`

Execute `main.py` to extract essays from Gmail, download them, and automatically generate summary in `./summary.txt`

```sh
python main.py
```

## Important Notes

- Ensure that the Chrome browser and ChromeDriver are installed, and that ChromeDriver is added to your system PATH.
- Currently works for Gmails only.
