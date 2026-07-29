

def build_prompt(pdf_text: str) -> str:
    prompt = f"""
You are a UNIVERSAL BILL/TABLE EXTRACTOR for messy wholesale, pharma, medical and FMCG statements.

The input is raw text extracted from a PDF using PyMuPDF (fitz). It may contain:
- broken headers split across lines (VAL + UE → VALUE, SPLDI + S → SPLDIS)
- customer names mixed with product names
- multi-customer invoices
- product codes mixed with item names
- dates appearing once or per-row
- empty columns
- misaligned values
- mid-table totals without the word "TOTAL"
- multiple table structures

Your tasks:

===========================================================
1. **DETECT REAL HEADERS (even if broken or split)**  
===========================================================
- Reconstruct real column names by merging line fragments.  
- Examples:  
  - "SPLDI" + "S" → "SPLDIS"  
  - "VAL" + "UE" → "VALUE"  
- Do NOT invent new column names.  
- Keep all original columns exactly as the table contains.

===========================================================
2. **OUTPUT EMPTY COLUMNS EXACTLY AS PRESENT IN THE PDF**  
===========================================================
If a column exists in the header but a row has no value, output:
Do **NOT** shift values from next/previous columns.

===========================================================
3. **SEPARATE CUSTOMER / PARTY NAMES FROM PRODUCT NAMES**  
===========================================================
- Customer/Party name should NEVER appear as item/product name.
- Do not generate customer name on your own.
- Customer names typically contain words like:
  - “Medical”, “Pharmacy”, “PHARMCY”, “Medicals”, “Med&Gen”, “MEDICAL AND SURGICAL DISTRIBUTORS”, “Enterprises”, “Agency”, “Store”, “Distributors”, “Traders”, “Surgical”, “Healthcare”
- Product names typically look like:
  - Brands, medicines, FMCG items, SKUs, item codes  
  Example: “NINE OD”, “ACBILL PLUS”, “ SUNNY CAPS D3”, “BAKOFIN 10”, “CMD04488    19/06 AOT-6056”, “CMD03715    07/06 404TTL001”, “DOLO 650”, “CETRIMIDE LOTION”, “PARACETAMOL 500MG”

**Rule:**
- Create a **separate field `"customer_name"`**.
- Each product row must contain **product_name**, not customer_name.
- Do not ignore products written just after "continued.." or "contd".
- If continued is written then customer name remains same as previous customer name until next customer name is encountered.
- If one invoice contains multiple customer/group blocks, infer the correct customer for each product group.

===========================================================
4. **DO NOT REMOVE PRODUCT CODES**  
===========================================================
If a product name is written with a code:
- “CETRIMIDE LOTION 20ML (CT20)”
- “NINE OD TAB 10’S 0045”
- “CMD04488    19/06 AOT-6056”
- “DMA1295     23-06 2409297E”
You MUST include the code in `product_name`.  
Never discard or split it.

===========================================================
5. **DATE HANDLING (IMPORTANT)**  
===========================================================
- If the date appears **once at the top**, apply that single date to all rows in the CSV.  
- If a date is present for every product row, preserve row-wise dates. But if time period is given once at top, the row-wise dates should be in that time period only no month/year should be outside that time period. 
- Name the column: `date`.

===========================================================
6. **HANDLE DISTINCT COLUMNS (DO NOT MERGE THEM)**  
===========================================================
These are **NOT** the same and must remain separate columns:
- `"Sales Ret."`
- `"Exp/Dmg"`
- `"Shortage"`
- `"SALE VALUE"` and `"CLOSING VALUE"` are different columns.
- Pack and Batch are different columns, Batch can have alphanumeric values like "SXX90724", "AOT-6094". Such values can never appear in Pack column.

LLM must NEVER merge or combine these into one.

===========================================================
7. **IGNORE ALL TOTALS**  
===========================================================
- Ignore totals even if they appear without the word “TOTAL”.  
- Ignore subtotal blocks, summaries, page-level totals.

===========================================================
8. **STRICT JSON OUTPUT FORMAT**  
===========================================================
Return ONLY:
{{
  "party_name": string or null,
  "rows": [
      {{
         "col1": value_or_null,
         "col2": value_or_null,
         ...
      }}
  ]
}}

Where:
- `party_name` = primary party or customer for the whole document.  
- `rows` = extracted product line items.  
- Every inferred column **must appear even if empty**.

===========================================================
9. **NO MARKDOWN. NO EXPLANATIONS. ONLY VALID JSON**  
===========================================================

---------------- BEGIN PDF TEXT ----------------
{pdf_text}
---------------- END PDF TEXT ----------------
"""
    return prompt.strip()
