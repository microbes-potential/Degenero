# utils.py
# Simple helper functions for file parsing

import pandas as pd
import io
import base64

def parse_uploaded_file(contents, filename):
    """
    Parse uploaded CSV or XLSX file.
    """
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if filename.endswith('.csv'):
            # Parse CSV
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif filename.endswith('.xlsx'):
            # Parse Excel
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            raise ValueError("Unsupported file format. Only CSV and XLSX are supported.")
    except Exception as e:
        print(f"❌ Error parsing file: {e}")
        return None

    return df

