from typing import Optional
from fastapi import UploadFile
from docx import Document
import io


def extract_text_from_upload(file: UploadFile) -> str:
    """
    Given an UploadFile (.docx or .txt), return its plain text as a single string.
    
    Supported formats:
      - .docx using python-docx
      - .txt using simple decode
    
    For unsupported types, raise a ValueError.
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        Extracted plain text as a string
    """
    if not file or not file.filename:
        return ""
    
    filename_lower = file.filename.lower()
    
    file.file.seek(0)
    content = file.file.read()
    file.file.seek(0)
    
    if filename_lower.endswith(".docx"):
        doc = Document(io.BytesIO(content))
        paragraphs = [p.text for p in doc.paragraphs]
        return "\n".join(paragraphs)
    
    elif filename_lower.endswith(".txt"):
        return content.decode("utf-8", errors="ignore")
    
    else:
        raise ValueError(f"Unsupported file type: {file.filename}. Only .docx and .txt are supported.")
