import difflib
import io
import base64
import os

try:
    import fitz
    FITZ_OK = True
except ImportError:
    FITZ_OK = False

try:
    import pandas as pd
    PANDAS_OK = True
except ImportError:
    PANDAS_OK = False

try:
    from PIL import Image
    import numpy as np
    IMAGE_OK = True
except ImportError:
    IMAGE_OK = False

try:
    import docx
    DOCX_OK = True
except ImportError:
    DOCX_OK = False

try:
    from pptx import Presentation
    PPTX_OK = True
except ImportError:
    PPTX_OK = False

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
try:
    from groq import Groq
    GROQ_CLIENT = Groq(api_key=GROQ_API_KEY)
    GROQ_OK = bool(GROQ_API_KEY)
except Exception:
    GROQ_OK = False

def get_inline_diff(old: str, new: str) -> list:
    matcher = difflib.SequenceMatcher(None, old, new)
    result = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            result.append({"type": "equal", "text": old[i1:i2]})
        elif op == "replace":
            result.append({"type": "removed", "text": old[i1:i2]})
            result.append({"type": "added", "text": new[j1:j2]})
        elif op == "delete":
            result.append({"type": "removed", "text": old[i1:i2]})
        elif op == "insert":
            result.append({"type": "added", "text": new[j1:j2]})
    return result

def compute_diff_report(text1: str, text2: str) -> dict:
    lines1 = text1.splitlines(keepends=True)
    lines2 = text2.splitlines(keepends=True)

    differ = difflib.Differ()
    delta = list(differ.compare(lines1, lines2))

    differences = []
    added = removed = changed = 0
    line_num1 = line_num2 = 0

    i = 0
    while i < len(delta):
        line = delta[i]
        code = line[:2]
        content = line[2:].rstrip("\n")

        if code == "  ":
            line_num1 += 1
            line_num2 += 1
        elif code == "- ":
            if i + 1 < len(delta) and delta[i+1][:2] == "+ ":
                next_content = delta[i+1][2:].rstrip("\n")
                differences.append({
                    "type": "changed",
                    "line_num1": line_num1 + 1,
                    "line_num2": line_num2 + 1,
                    "old": content,
                    "new": next_content,
                    "inline": get_inline_diff(content, next_content)
                })
                changed += 1
                line_num1 += 1
                line_num2 += 1
                i += 2
                continue
            else:
                differences.append({
                    "type": "removed",
                    "line_num1": line_num1 + 1,
                    "line_num2": None,
                    "old": content,
                    "new": None,
                    "inline": None
                })
                removed += 1
                line_num1 += 1
        elif code == "+ ":
            differences.append({
                "type": "added",
                "line_num1": None,
                "line_num2": line_num2 + 1,
                "old": None,
                "new": content,
                "inline": None
            })
            added += 1
            line_num2 += 1
        i += 1

    similarity = difflib.SequenceMatcher(None, text1, text2).ratio() * 100

    unified = "".join(difflib.unified_diff(
        lines1, lines2,
        fromfile="Document 1",
        tofile="Document 2"
    ))

    return {
        "full_text1": text1,
        "full_text2": text2,
        "unified_diff": unified,
        "differences": differences,
        "stats": {
            "added": added,
            "removed": removed,
            "changed": changed,
            "total_changes": added + removed + changed,
            "similarity_percent": round(similarity, 2),
            "difference_percent": round(100 - similarity, 2)
        }
    }

def extract_text_from_pdf(path: str) -> str:
    if not FITZ_OK:
        return "PyMuPDF not installed - cannot extract PDF text"
    doc = fitz.open(path)
    pages = []
    for i, page in enumerate(doc):
        pages.append(f"[PAGE {i+1}]\n{page.get_text()}")
    return "\n\n".join(pages)

def extract_text_from_docx(path: str) -> str:
    if not DOCX_OK:
        return "python-docx not installed"
    d = docx.Document(path)
    return "\n".join(p.text for p in d.paragraphs)

def extract_text_from_pptx(path: str) -> str:
    if not PPTX_OK:
        return "python-pptx not installed"
    prs = Presentation(path)
    slides = []
    for i, slide in enumerate(prs.slides):
        texts = []
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                texts.append(shape.text)
        slides.append(f"[SLIDE {i+1}]\n" + "\n".join(texts))
    return "\n\n".join(slides)

def extract_text_from_excel(path: str) -> str:
    if not PANDAS_OK:
        return "pandas not installed - cannot extract Excel text"
    xl = pd.ExcelFile(path)
    sheets = []
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        sheets.append(f"[SHEET: {sheet}]\n{df.to_string(index=True)}")
    return "\n\n".join(sheets)

def extract_text_from_csv(path: str) -> str:
    if not PANDAS_OK:
        return "pandas not installed - cannot extract CSV text"
    df = pd.read_csv(path)
    return df.to_string(index=True)

def image_diff(path1: str, path2: str) -> dict:
    if not IMAGE_OK:
        return {"type": "image", "diff_image_base64": "", "stats": {"total_pixels": 0, "changed_pixels": 0, "similarity_percent": 0, "difference_percent": 0}}
    img1 = Image.open(path1).convert("RGB")
    img2 = Image.open(path2).convert("RGB")

    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.LANCZOS)

    arr1 = np.array(img1, dtype=np.int32)
    arr2 = np.array(img2, dtype=np.int32)
    diff_arr = np.abs(arr1 - arr2).astype(np.uint8)

    mask = np.any(diff_arr > 10, axis=2)
    highlight = img1.copy().convert("RGBA")
    highlight_arr = np.array(highlight)
    highlight_arr[mask] = [255, 0, 0, 200]
    diff_img = Image.fromarray(highlight_arr, "RGBA")

    buf = io.BytesIO()
    diff_img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    total_pixels = arr1.shape[0] * arr1.shape[1]
    changed_pixels = int(mask.sum())
    similarity = round((1 - changed_pixels / total_pixels) * 100, 2)

    return {
        "type": "image",
        "diff_image_base64": b64,
        "stats": {
            "total_pixels": total_pixels,
            "changed_pixels": changed_pixels,
            "similarity_percent": similarity,
            "difference_percent": round(100 - similarity, 2)
        }
    }

async def get_ai_analysis(text1: str, text2: str, diff_report: dict) -> str:
    if not GROQ_OK:
        return "AI unavailable: GROQ_API_KEY not set or groq package missing."

    changes_summary = "\n".join([
        f"- [{d['type'].upper()}] Line {d.get('line_num1') or d.get('line_num2')}: "
        f"'{d.get('old', '')}' -> '{d.get('new', '')}'"
        for d in diff_report.get("differences", [])[:30]
    ])

    prompt = f"""You are a document analysis expert. Analyze these two documents and explain what changed.

DOCUMENT 1 (first 500 chars):
{text1[:500]}

DOCUMENT 2 (first 500 chars):
{text2[:500]}

DETECTED CHANGES:
{changes_summary}

Provide:
1. A concise executive summary of what changed
2. Key differences categorized
3. Significance/impact of the changes

Be specific and professional."""

    try:
        response = GROQ_CLIENT.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI analysis failed: {str(e)}"
