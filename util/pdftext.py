import fitz  # PyMuPDF


def extract_section(pdf_path, type="acs"):
    text_content = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text_content += page.get_text() + " "

    text_content = text_content.replace("\n", " ")

    if type == "acs":
        ref_marker = "REFERENCES"
        ref_index = text_content.find(ref_marker)
        text_content = text_content[:ref_index]

    elif type == "aps":
        ref_marker = "[1]"
        ref_index = text_content.rfind(ref_marker)
        text_content = text_content[:ref_index]

    return text_content


if __name__ == "__main__":
    pdf_path = "data/aps_downloaded_pdfs/PhysRevLett.134.090202.pdf"

    section_text = extract_section(pdf_path, type="aps")

    with open("extract.txt", "w", encoding="utf-8") as f:
        f.write(section_text)
