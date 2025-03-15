import os
import shutil
import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from util.pdftext import extract_section


DEBUGGING = False


def _summarize_pdf_text(pdf_text, api_key, model="Pro/deepseek-ai/DeepSeek-V3"):
    """
    Sends the extracted PDF text to the SiliconFlow API for summarization.

    Parameters:
      pdf_text (str): The text extracted from the PDF.
      api_key (str): Your SiliconFlow API key.

    Returns:
      The summary  returned by the API.
    """
    prompt = (
        "你是一位专业的文章摘要生成器，你的任务是分析提供的文本，并用中文生成结构清晰、准确且简明的摘要。"
        "请确保摘要能够准确捕捉文章的要点、论点和结论，着重介绍论文本身的工作内容和价值，避免冗余信息或遗漏重要内容，严禁直接翻译抄袭文章中Abstract中的内容！"
        "摘要应易于理解，并且长度应合理，不应过长或过短，约在500字左右，严格控制不得超过800字！"
        "在开头应指出文章的几个关键词."
    )

    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    payload = {
        "model": f"{model}",
        "messages": [
            {
                "role": "system",
                "content": prompt,
            },
            {"role": "user", "content": pdf_text},
        ],
        "stream": False,
        "max_tokens": 2048,
        "stop": ["null"],
        "temperature": 0.3,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "n": 1,
        "response_format": {"type": "text"},
    }

    response = requests.post(url, json=payload, headers=headers)
    response = response.text
    return response


def _write_summary_to_file(pdf_name: str, summary, output_dir: str, output_name: str):
    summary_json = json.loads(summary)
    summary_filename = os.path.join(output_dir, output_name)
    with open(summary_filename, "a", encoding="utf-8") as summary_file:
        summary_file.write(f"Summary of {pdf_name}\n\n")
        try:
            summary_file.write(summary_json["choices"][0]["message"]["content"])
        except:
            summary_file.write(summary)
        summary_file.write("\n\n")
        summary_file.write("#" + "-" * 120 + "#\n")


def _check_summary(summary):
    try:
        summary_json = json.loads(summary)
        if "choices" in summary_json:
            return True
        else:
            return False
    except:
        return False


def _process_single_pdf(
    pdf_path: str,
    filename: str,
    processed_dir: str,
    api_key: str,
    output_dir: str,
    output_name: str,
    file_lock: threading.Lock,
    cool_down: int = 0,
    j_type="acs",
):
    """
    Parameters:
        pdf_path (str): Full path to the PDF file.
        filename (str): Name of the PDF file.
        api_key (str): API key for the summarization service.
        processed_dir (str): Directory where the processed pdfs are moved to.
        output_dir (str): Directory where the summary file is saved.
        output_name (str): Name of the output summary file.
        file_lock (threading.Lock): Lock to ensure thread-safe file operations.
        cool_down (0): Seconds to wait after processing.
    """

    pdf_text = extract_section(pdf_path, j_type)

    if DEBUGGING:
        with file_lock:
            with open("content.txt", "w", encoding="utf-8") as f:
                f.write(pdf_text)

    summary = _summarize_pdf_text(pdf_text, api_key, model="Pro/deepseek-ai/DeepSeek-V3")

    if not os.path.exists(processed_dir):
        os.mkdir(processed_dir)

    if _check_summary(summary):
        with file_lock:
            _write_summary_to_file(filename, summary, output_dir=output_dir, output_name=output_name)
        print(f"[{time.ctime().split()[3]}] Summary for {filename} written to file.")
        print("-" * 120)
        shutil.move(pdf_path, processed_dir)

    else:
        print(f"FAILED to write summary for {filename} to file.")
        print("Original output as follows:")
        print(summary)
        print("-" * 120)

    time.sleep(cool_down)


def process_pdfs_in_directory(
    pdf_dir: str, processed_dir: str, api_key: str, output_dir: str, output_name: str = "summary.txt", j_type="acs"
):
    file_lock = threading.Lock()

    pdf_files = [filename for filename in os.listdir(pdf_dir) if filename.lower().endswith(".pdf")]

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = []
        for filename in pdf_files:
            pdf_path = os.path.join(pdf_dir, filename)
            futures.append(
                executor.submit(
                    _process_single_pdf,
                    pdf_path,
                    filename,
                    processed_dir,
                    api_key,
                    output_dir,
                    output_name,
                    file_lock,
                    j_type=j_type,
                )
            )

        for future in as_completed(futures):
            try:
                future.result()
            except:
                print(f"An error occurred while processing a PDF")


def main():
    pdf_directory = "data/acs_downloaded_pdfs"
    processed_dir = "data/acs_summarized_pdfs"
    output_directory = "./"

    with open("config/api.txt", "r") as f:
        lines = f.readlines()
    api_key = lines[0]

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    process_pdfs_in_directory(pdf_directory, processed_dir, api_key, output_directory, j_type="acs")


if __name__ == "__main__":
    main()
