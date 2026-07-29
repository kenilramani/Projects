import os
import json
import fitz  # PyMuPDF
import pandas as pd
from typing import Any, Dict, List
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
import time
import pdfplumber

# =========================================================
# CONFIGURATION
# =========================================================

FILE_INPUT_PATH = r"C:\Users\User1\Downloads\error_partywise\orgfile\Sri Sai Sandhya - PWS Rajamundry.pdf"
JSON_OUTPUT_PATH = r"C:\Users\User1\Downloads\Sri Sai Sandhya - PWS Rajamundry.json"

OPENAI_MODEL = "gpt-4.1"
GROQ_MODEL = "llama-3.3-70b-versatile"

# =========================================================
# LOAD KEYS
# =========================================================
load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

GROQ_KEYS = [
    os.getenv("GROQ_API_KEY1"),
    os.getenv("GROQ_API_KEY2"),
    os.getenv("GROQ_API_KEY3"),
]


def extract_input_text(input_path: str) -> str:
    ext = os.path.splitext(input_path.lower())[1]

    if ext == ".pdf":
        return extract_pdfs_text_pdfplumber(input_path)

    elif ext == ".txt":
        return extract_txt_text(input_path)

    elif ext == ".xlsx":
        return extract_xlsx_text(input_path)

    else:
        raise ValueError(
            f"Unsupported input type: {ext}. Allowed: .pdf, .txt, .xlsx"
        )


def extract_pdfs_text_pdfplumber(pdf_path: str) -> str:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

     # Extract text using pdfplumber
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                all_text.append(page_text)
    return "\n".join(all_text)


def extract_txt_text(txt_path: str) -> str:
    if not os.path.exists(txt_path):
        raise FileNotFoundError(f"TXT not found: {txt_path}")

    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_xlsx_text(xlsx_path: str) -> str:
    if not os.path.exists(xlsx_path):
        raise FileNotFoundError(f"XLSX not found: {xlsx_path}")

    excel_file = pd.ExcelFile(xlsx_path)
    all_sheets_text = []

    for sheet_name in excel_file.sheet_names:
        df = excel_file.parse(sheet_name)
        df = df.fillna("")
        all_sheets_text.append(
            f"\n--- SHEET: {sheet_name} ---\n" + df.to_string(index=False)
        )

    return "\n".join(all_sheets_text)


def build_prompt(pdf_text: str) -> str:
    prompt = f"""
You are a **PHARMA STATEMENT → STRUCTURED SALES INTELLIGENCE ENGINE**.

You operate under a **STRICT DATA CONTRACT**.  
Deviation from the required JSON structure is a **critical failure**.

Your objective is to extract sales data from messy wholesale / pharma PDFs and return **ONLY valid JSON** in the **EXACT structure defined below**.

===========================================================
1. DOCUMENT-LEVEL METADATA (MANDATORY)
===========================================================

- Extract the **first non-empty line of the PDF** as:
  → `"name"`
    - Names will be like: "MEDICAL AGENCIES", "MEDICAL & SURGICAL AGENCIES", "PHARMA", "MEDICAL CORPORATION", etc.
    - "DAXINSOFT" is not a valid name, ignore it and go to next line for name if DAXINSOFT appears first.
    - If no valid name is found:
        → `"name": ""`

- Extract the **address ONLY if it appears within the first 3–4 lines** of the PDF.
  - Address typically contains door numbers, floor, street names, locality, city, PIN code.
  - If no address is clearly present in the first 3–4 lines:
    → `"address": ""`
  - Do NOT infer, hallucinate, or reuse any other text.
  - Do NOT populate values like:
    - "Customer"
    - "Company"
    - "Product Sales"
    - Headings or report titles

===========================================================
2. OUTPUT JSON ROOT STRUCTURE (NON-NEGOTIABLE)
===========================================================

Return an ARRAY with exactly this structure:

[
  {{
    "name": string,
    "address": string,
    "chemist": [ ... ]
  }}
]

- `"name"` MUST come first
- `"address"` MUST come second
- `"chemist"` MUST come third
- Do NOT add extra keys
- Do NOT change key names
- Do NOT nest differently

===========================================================
3. CHEMIST (CUSTOMER) GROUPING RULES
===========================================================

- `"chemist"` is an ARRAY of customer blocks.
- Each chemist/customer MUST appear **ONLY ONCE**.
- Whenever product name appears before a list of different customers, assign those customers to that product.
- A chemist block structure:

{{
  "name": string,
  "medicines": [ ... ]
}}

Rules:
- Chemist name must NEVER be treated as a product.
- Chemist names typically include:
  “Medical”, “MEDICAL AND GENERAL STORES”, “Pharmacy”, “PHARMCY”, “Medicals”, “Med&Gen”, “MEDICAL AND SURGICAL DISTRIBUTORS”, “Enterprises”, “Agency”, “Store”, “Distributors”, “Traders”, “Surgical”, “Healthcare”
- Sometimes the product name might appear before the list of chemist names in the text.
- If products continue under the same chemist (e.g., "contd", "continued"):
  → reuse the SAME chemist until a new chemist name appears.
- NEVER duplicate a chemist just because multiple products exist.
- "SAI LAKSHMIPRIYANKA MEDIPCGRAM", "SAI LAKSHMIPRIYANKA MEDINCINE", "SAI LAKSHMIPRIYANKA MEDITCRAMP" if appear, treat them as same chemist "SAI LAKSHMIPRIYANKA MEDI"


4. MEDICINES ARRAY (PRODUCT-LEVEL RULES)


Each `"medicines"` entry MUST follow EXACTLY this schema:

{{
  "name": string,
  "free": number,
  "sales": number,
  "amount": number,
  "damage": number,
  "expired": number,
  "returned": number
}}

STRICT RULES:
- `"name"` = product name ONLY (including codes, packs, batch-like suffixes)
- NEVER remove numbers or codes from product names.
- If same product name appears more than one time under the same chemist, then also REPEAT the product entry as its Inv. No or date will differ. Do not write total value of such products and never make single entry.
- Sometimes Total values might be written before the word "Total", never write totals by ignoring actual values.
- Do not enter medicines on your own and enter '0' in all fields, only extract what is present in the text.
- **Make sure** no product name and customer is missed at any cost even if product is at last of the particular customer.
- When product name is written before customer name, make sure to assign product to correct customer name only without mixing with other customer names.
- When "MRP" is written before "Qty" and "Free", handle those files properly without writing "MRP" as "Qty" and "Free".
- These are VALID product names:
  - "CARTISTRONG 10,S"
  - "CARNITIME"
  - "TELMIVAZ TRIO"
  - "TRAMPOZ"
  - "CITAGIN 50         10'S"
  - "BOOSTB12 SPARY"
  - "NINE OD SYP 200 ML"

- These are NOT product names, so do NOT extract them, find for other similar names in the text:
  - "CARNIT 10S"
  - "TELMIV 10S"
  - "GLIMYJ 10S"
  - "BOOST" fetch product name from starting of such product names
  - "BOOST D1X1" it is an ICode not product name
  - "PGRAM 10S"
  - Customer names
  - Totals
  - Headings

===========================================================
5. NUMERIC NORMALIZATION (CRITICAL)
===========================================================

If ANY numeric value is:
- "-"
- empty
- null
- missing

You MUST output:
→ 0.00

This applies to:
- free
- sales
- amount
- damage
- expired
- returned

DO NOT output "-"  
DO NOT output null  
DO NOT omit numeric keys  

===========================================================
6. SALES / FREE / AMOUNT MAPPING
===========================================================

- `"sales"` → Quantity sold, Never mix with "MRP", "Rate" or "Area" even if these are null or zero.
- `"free"` → Free quantity, Never mix with "Qty" or "Quantity" even if both data are one after another in text
- `"amount"` → fetch from columns like "amount" and "Gross" only, never from SRate or rate as "amount" will be total value only and not per unit rate.
- Ignore totals, subtotals, summaries, page totals

===========================================================
7. DAMAGE / EXPIRED / RETURNED
===========================================================

- Populate ONLY if explicitly present as columns or values
- Otherwise ALWAYS set:
  damage = 0.00
  expired = 0.00
  returned = 0.00

===========================================================
8. DATE HANDLING (IMPORTANT)
===========================================================

- ONLY include date values IF a DATE column exists in the TABLE HEADER.
- If date exists:
  - Attach it at the medicine level ONLY.
- If date does NOT exist in the header:
  - DO NOT fetch date from top text
  - DO NOT infer
  - DO NOT add date field

===========================================================
9. HARD CONSTRAINTS
===========================================================

- Ignore ALL totals (even without the word "TOTAL")
- Ignore summary rows
- Ignore customer-level financial summaries
- NEVER invent columns
- NEVER rename keys
- NEVER return markdown
- NEVER return explanations
- NEVER return partial JSON

===========================================================
10. OUTPUT FORMAT
===========================================================

Return ONLY valid JSON.
No markdown.
No commentary.
No explanations.

---------------- BEGIN PDF TEXT ----------------
{pdf_text}
---------------- END PDF TEXT ----------------
"""
    return prompt.strip()


# =========================================================
# API CLIENT ROTATION SYSTEM
# =========================================================


def try_openai_api(prompt: str) -> str:
    if not OPENAI_KEY:
        return None

    print("Trying OpenAI API...")

    try:
        client = OpenAI(api_key=OPENAI_KEY)
        res = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Return ONLY valid JSON."},
                {"role": "user", "content": prompt},
            ],
        )
        usage = res.usage
        print(
            f"Tokens used | Prompt: {usage.prompt_tokens}, "
            f"Completion: {usage.completion_tokens}, "
            f"Total: {usage.total_tokens}"
        )
        return res.choices[0].message.content

    except Exception as e:
        print(f"OpenAI API failed: {e}")
        return None


def try_groq_api(prompt: str) -> str:
    """Try all Groq keys until one succeeds. Return JSON string."""
    for idx, key in enumerate(GROQ_KEYS, start=1):
        if not key:
            continue

        print(f"Trying Groq API key {idx} as fallback...")

        try:
            client = Groq(api_key=key)
            res = client.chat.completions.create(
                            model=GROQ_MODEL,
                            temperature=0,
                            response_format={"type": "json_object"},
                            messages=[
                                {"role": "system", "content": "Return ONLY valid JSON."},
                                {"role": "user", "content": prompt},
                            ],
                        )

            usage = res.usage
            print(
                f"Tokens used | Prompt: {usage.prompt_tokens}, "
                f"Completion: {usage.completion_tokens}, "
                f"Total: {usage.total_tokens}"
            )

            return res.choices[0].message.content


        except Exception as e:
            print(f"Groq key {idx} failed: {e}")
            time.sleep(1)

    return None

def call_llm_with_failover(prompt: str) -> str:
    """Full failover logic: OpenAI → Groq."""
    json_result = try_openai_api(prompt)
    if json_result:
        return json_result

    json_result = try_groq_api(prompt)
    if json_result:
        return json_result

    raise RuntimeError("All API keys failed (OpenAI + Groq).")


# MAIN Pipeline

def pdf_to_json(pdf_path: str, json_output_path: str):
    print("Extracting text (fitz)...")
    input_text = extract_input_text(pdf_path)

    print("Building prompt...")
    prompt = build_prompt(input_text)

    print("Calling LLM with failover...")
    json_output = call_llm_with_failover(prompt)

    # Parse JSON string to Python object
    parsed_json = json.loads(json_output)

    # JSON to file
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(parsed_json, f, indent=2, ensure_ascii=False)

    # print(f"JSON successfully written to: {json_output_path}")
    # print("JSON Output:", json_output)
    return json_output


if __name__ == "__main__":
    pdf_to_json(FILE_INPUT_PATH, JSON_OUTPUT_PATH)