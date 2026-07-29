# It has dynamic column detection, no fixed column schema in prompt.
import os
import json
import fitz  # PyMuPDF
import pandas as pd
from typing import Any, Dict, List
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
import time

# =========================================================
# CONFIGURATION
# =========================================================

PDF_INPUT_PATH = r"C:\Users\User1\Downloads\SS_ERROR\Rainbow Party Wise june_25.pdf"
JSON_OUTPUT_PATH = r"C:\Users\User1\Downloads\Rainbow Party Wise june_25_2.json"

GROQ_MODEL = "llama-3.3-70b-versatile"
OPENAI_MODEL = "gpt-4.1"

# =========================================================
# LOAD KEYS
# =========================================================
load_dotenv()

GROQ_KEYS = [
    os.getenv("GROQ_API_KEY1"),
    os.getenv("GROQ_API_KEY2"),]
#     os.getenv("GROQ_API_KEY3"),
#     os.getenv("GROQ_API_KEY4"),
#     os.getenv("GROQ_API_KEY5"),
#     os.getenv("GROQ_API_KEY6"),
# ]

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# =========================================================
# FITZ PDF EXTRACTION
# =========================================================

def extract_pdf_text_fitz(pdf_path: str) -> str:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    pages = [page.get_text("text") for page in doc]
    doc.close()

    return "\n".join(pages)


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
- A chemist block structure:

{{
  "name": string,
  "medicines": [ ... ]
}}

Rules:
- Chemist name must NEVER be treated as a product.
- Chemist names typically include:
  “Medical”, “Pharmacy”, “PHARMCY”, “Medicals”, “Med&Gen”, “MEDICAL AND SURGICAL DISTRIBUTORS”, “Enterprises”, “Agency”, “Store”, “Distributors”, “Traders”, “Surgical”, “Healthcare”
- If products continue under the same chemist (e.g., "contd", "continued"):
  → reuse the SAME chemist until a new chemist name appears.
- NEVER duplicate a chemist just because multiple products exist.

===========================================================
4. MEDICINES ARRAY (DYNAMIC, HEADER-DRIVEN)
===========================================================

The `"medicines"` key MUST be populated dynamically based on the
ACTUAL TABLE COLUMNS detected in the PDF.

RULES:

- Do NOT assume fixed column names.
- Do NOT hardcode fields like free, sales, amount, damage, expired, returned.
- The structure of each medicine object MUST be derived ONLY from:
  → the detected table header of the current file.

PROCESS:

    1. Detect the exact set of column headers present in the product table.
        - Headers may be broken, split across lines, or misaligned.
        - Reconstruct headers where required.
        - Do NOT invent new headers.
        - Do NOT drop existing headers.

    2. For each product row:
        - Create a JSON object where:
            - Keys = detected header names (exactly as reconstructed)
            - Values = corresponding row values

    3. Product name column:
        - Whichever column represents the product/item/description MUST be included
            exactly as detected (e.g., DESCRIPTION, ITEM NAME, PRODUCT, etc.).
        - "DR/CR" and "NET AMOUNT" are different columns, fill their values in different key values.
        - NEVER remove numbers, codes, packs, batch references from product values.

    4. Customer names, totals, headings, summaries must NEVER appear inside
    `"medicines"`.

Result:
    - `"medicines"` becomes a list of **row-wise dynamic objects**
    - Each file may produce a DIFFERENT medicine schema
    - This variability is EXPECTED and CORRECT

===========================================================
5. VALUE NORMALIZATION (CRITICAL, UNIVERSAL)
===========================================================

For ANY column inside `"medicines"`:

If the extracted value is:
- "-"
- empty
- missing
- null
- blank string

You MUST replace it with:
→ 0.00

STRICT ENFORCEMENT:
    - NEVER output "-"
    - NEVER output null
    - NEVER omit a key that exists in the detected header
    - Zero-fill is mandatory for ALL missing values, regardless of column meaning

===========================================================
6. ROW MAPPING RULES (HEADER-FIRST)
===========================================================

- Values MUST map strictly by column position and header alignment.
- Do NOT shift values left or right to "make sense".
- If a row has more values than headers:
  - Attach extra values using their detected header or leave them as-is
  - Do NOT drop them
- If a row has fewer values than headers:
  - Populate missing columns with 0.00

IMPORTANT:
- Ignore totals, subtotals, page summaries, bill summaries
- Only true product-level rows belong inside `"medicines"`

===========================================================
7. CONDITIONAL COLUMN HANDLING
===========================================================

- Columns related to damage, expiry, returns, shortages, adjustments, etc.
  MUST be included ONLY IF they exist in the detected header.

- If such columns exist:
  - Populate them row-wise
  - Apply zero-fill rules where values are missing

- If such columns do NOT exist:
  - DO NOT create them
  - DO NOT infer them
  - DO NOT inject placeholder columns

This ensures:
- No schema hallucination
- No forced standardization
- Full fidelity to source document structure


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

def try_groq_api(prompt: str) -> str:
    """Try all Groq keys until one succeeds. Return JSON string."""
    for idx, key in enumerate(GROQ_KEYS, start=1):
        if not key:
            continue

        print(f"Trying Groq API key {idx}...")

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
    """Fallback to OpenAI."""
    if not OPENAI_KEY:
        return None

    print("Trying OpenAI API as fallback...")

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
        return res.choices[0].message.content

    except Exception as e:
        print(f"OpenAI API failed: {e}")
        return None


def call_llm_with_failover(prompt: str) -> str:
    """Full failover logic: Groq → OpenAI."""
    json_result = try_groq_api(prompt)
    if json_result:
        return json_result

    json_result = try_openai_api(prompt)
    if json_result:
        return json_result

    raise RuntimeError("All API keys failed (Groq + OpenAI).")


# =========================================================
# MAIN PIPELINE
# =========================================================

def pdf_to_json(pdf_path: str, json_output_path: str):
    print("Extracting text (fitz)...")
    pdf_text = extract_pdf_text_fitz(pdf_path)

    print("Building prompt...")
    prompt = build_prompt(pdf_text)

    print("Calling LLM with failover...")
    json_output = call_llm_with_failover(prompt)

    # Parse JSON string to Python object
    parsed_json = json.loads(json_output)

    # Write JSON to file
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(parsed_json, f, indent=2, ensure_ascii=False)

    print(f"JSON successfully written to: {json_output_path}")
    # print(json_output)


if __name__ == "__main__":
    pdf_to_json(PDF_INPUT_PATH, JSON_OUTPUT_PATH)