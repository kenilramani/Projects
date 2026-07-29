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

FILE_INPUT_PATH = r"C:\Users\User1\Downloads\error_stockistwise\orgfile\SRI SURYA LINES-PWS SPD.pdf"
JSON_OUTPUT_PATH = r"C:\Users\User1\Downloads\SRI SURYA LINES-PWS SPD.json"

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
    print(all_sheets_text)
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
    "medicines": [ ... ]
  }}
]

- `"name"` MUST come first
- `"address"` MUST come second
- `"medicines"` MUST come third
- Do NOT add extra keys
- Do NOT change key names
- Do NOT nest differently

===========================================================
3. MEDICINES ARRAY (PRODUCT-LEVEL RULES)
===========================================================

Each `"medicines"` entry MUST follow EXACTLY this schema:

{{
  "name": string,
  "opening": number,
  "sales": number,
  "total": number,
  "amount": number,
  "closing": number,
  "free": number,
  "purchase": number
}}

STRICT RULES:
- `"name"` = product name ONLY (including codes, packs, batch-like suffixes)
- NEVER remove numbers or codes from product names.
- If same product name appears more than one time under the same chemist, then also repeat the product entry as its date or Inv. No might differ.
- Fetch negative numbers as it is. Do not ignore "-" sign.
- If and only if "Sale Ret" column exists with these exact letters:
    - Assume these column to be empty and do not put values of next columns in "Sale Ret".
- These are VALID product names:
  - "CARTISTRONG 10,S"
  - "ACBILL 100 1*10"
  - "BAKOFIN 10"
  - "SALETROL F 250MDI 1X30"
  - "NINE OD SYP 200 ML"
  - "PGRAM 1 1X10"

- These are NOT product names:
  - Customer names
  - Totals
  - Headings

===========================================================
4. NUMERIC NORMALIZATION (CRITICAL)
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
- opening
- closing
- total
- purchase

DO NOT output "-"  
DO NOT output null  
DO NOT omit numeric keys  

===========================================================
5. SALES / OPENING / CLOSING / TOTAL / AMOUNT MAPPING
===========================================================

- `"sales"` → Issue Quantity sold, if no issue quantity found then  0.00
- `"opening"` → Opening/ Opening Qty ONLY, IGNORE ALL OTHER COLUMNS strictly, as it is a Quantity field ONLY. DO NOT fetch from "age" column.
- `"closing"` → Closing/ Closing Qty/ Closing Stock ONLY, If no closing qty found then 0.00 and do not infer other columns' data
- `"total"` → Total Quantity ONLY, no rates, no amounts, no Qoh, no closing qty or opening qty. NEVER FETCH from Closing. Remember it is a QUANTITY field ONLY so not fetching from "salevalue".
- `"amount"` → Closing Value / amount / VALUE ONLY
- Ignore totals, subtotals, summaries, page totals

===========================================================
6. PURCHASE
===========================================================

- Search out for columns like "RE"+"ORDER" or "RE-ORDER" or "Purc" or "Receive Quantity", and if exists map that to `"purchase"`.
- Fetch from quantity related columns ONLY, and not from purvalue or value columns.
- Otherwise ALWAYS set:
  purchase = 0.00

===========================================================
7. DATE HANDLING (IMPORTANT)
===========================================================

- ONLY include date values IF a DATE column exists in the TABLE HEADER.
- If date exists:
  - Attach it at the medicine level ONLY.
- If date does NOT exist in the header:
  - DO NOT fetch date from top text
  - DO NOT infer
  - DO NOT add date field

===========================================================
8. HARD CONSTRAINTS
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
9. OUTPUT FORMAT
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


def call_llm_with_failover(prompt: str) -> str:
    """Full failover logic: Groq → OpenAI."""
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

    # print("Building prompt...")
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