"""
Document loader for the RAG pipeline.

Extracts raw text from PDF, TXT, and DOCX files so it can be chunked and
embedded in the next stage of the pipeline.
"""

from pathlib import Path


def load_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_pdf(path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(path)
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def load_docx(path: str) -> str:
    # Lazy import — python-docx is only needed if a .docx is actually loaded
    import docx

    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def load_document(path: str) -> str:
    """
    Load a document's raw text based on its file extension.

    Args:
        path: path to a .txt, .pdf, or .docx file

    Returns:
        The extracted plain text.
    """
    suffix = Path(path).suffix.lower()

    if suffix == ".txt" or suffix == ".md":
        return load_txt(path)
    elif suffix == ".pdf":
        return load_pdf(path)
    elif suffix == ".docx":
        return load_docx(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Use .txt, .md, .pdf, or .docx")


def load_directory(directory: str) -> dict:
    """
    Load every supported document in a directory.

    Returns:
        dict mapping filename -> extracted text
    """
    supported = {".txt", ".md", ".pdf", ".docx"}
    results = {}
    for file_path in Path(directory).iterdir():
        if file_path.name.lower() == "readme.md":
            continue  # skip the folder's own instructional README, not demo content
        if file_path.suffix.lower() in supported:
            try:
                results[file_path.name] = load_document(str(file_path))
            except Exception as e:
                print(f"[loader] Skipping {file_path.name}: {e}")
    return results
