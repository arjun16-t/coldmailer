import pdfplumber
import pandas as pd
import os
import re

EMAIL_REGEX = r'[\w\.-]+@[\w\.-]+\.\w+'

def parse_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        return _parse_pdf(file_path)
    elif ext in ['.xlsx', '.xls']:
        return _parse_excel(file_path)
    elif ext == '.csv':
        return _parse_csv(file_path)
    else:
        raise ValueError(f'Unsupported file format: {ext}')

# PDF Parsing
def _parse_pdf(pdf_path):
    records = []

    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    lines = text.splitlines()

    current = {"name": None, "company": None, "email": None}

    for line in lines:
        email_match = re.search(EMAIL_REGEX, line)
        if email_match:
            current["email"] = email_match.group()

        name_match = re.search(r'Name[:\s]+(.+)', line, re.I)
        if name_match:
            current["name"] = name_match.group(1).strip()

        company_match = re.search(r'Company[:\s]+(.+)', line, re.I)
        if company_match:
            current["company"] = company_match.group(1).strip()

        # If we have an email, assume one complete record
        if current["email"]:
            records.append({
                "name": current["name"] or "Hiring Manager",
                "company": current["company"] or "your company",
                "email": current["email"]
            })
            current = {"name": None, "company": None, "email": None}

    return records

def _parse_excel(path):
    df = pd.read_excel(path)
    return _parse_dataframe(df)

def _parse_csv(path):
    df = pd.read_csv(path)
    return _parse_dataframe(df)

def _parse_dataframe(df):
    df.columns = df.columns.str.lower().str.strip()

    required = {"email"}
    if not required.issubset(df.columns):
        raise ValueError("File must contain email columns")

    df["name"] = df.get("name", "").fillna("").replace("", "Hiring Manager")
    df["company"] = df.get("company", "").fillna("").replace("", "your company")
    
    df = df.dropna(subset=["email"])

    records = []
    for _, row in df.iterrows():
        records.append({
            "name": row["name"],
            "company": row["company"],
            "email": row["email"]
        })

    return records
