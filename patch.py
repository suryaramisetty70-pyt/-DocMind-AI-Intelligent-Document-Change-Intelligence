import sys

with open('docfinder/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add import diff_engine
import_statement = 'from diff_engine import compute_diff_report, extract_text_from_pdf, extract_text_from_excel, extract_text_from_csv, image_diff, extract_text_from_docx, extract_text_from_pptx, get_ai_analysis, GROQ_OK\nimport tempfile\nimport os\n'
if 'from diff_engine import' not in content:
    content = content.replace('from fastapi import FastAPI', import_statement + 'from fastapi import FastAPI')

# 2. Replace the endpoints
start_marker = '@app.post("/api/compare/text")'
end_marker = '@app.post("/api/report/pdf/{comparison_id}")'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print('Markers not found')
    sys.exit(1)

new_endpoints = """@app.post("/api/compare/text")
async def compare_text(
    text1: str = Form(...),
    text2: str = Form(...),
    level: str = Form("word"),
    to_lowercase: str = Form("false"),
    remove_extra_spaces: str = Form("false"),
    sort_lines: str = Form("false"),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    report = compute_diff_report(text1, text2)
    report["file_type"] = "text"
    
    if use_ai.lower() == "true":
        report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

    # Save history
    comparison = Comparison(
        user_id=current_user.id if current_user else 0,
        file1_name="Text Input 1",
        file2_name="Text Input 2",
        file1_type="text",
        file2_type="text",
        comparison_type="text",
        similarity_score=report["stats"]["similarity_percent"],
        status="completed",
        results=report
    )
    db.add(comparison)
    await db.commit()
    await db.refresh(comparison)

    report["comparison_id"] = comparison.id
    return report

@app.post("/api/compare/pdf")
async def compare_pdf(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t1, \\
         tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as t2:
        t1.write(await file1.read()); t1_path = t1.name
        t2.write(await file2.read()); t2_path = t2.name

    try:
        text1 = extract_text_from_pdf(t1_path)
        text2 = extract_text_from_pdf(t2_path)
        report = compute_diff_report(text1, text2)
        report["file_type"] = "pdf"
        
        if use_ai.lower() == "true":
            report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

        # Save history
        comparison = Comparison(
            user_id=current_user.id if current_user else 0,
            file1_name=file1.filename,
            file2_name=file2.filename,
            file1_type="pdf",
            file2_type="pdf",
            comparison_type="pdf",
            similarity_score=report["stats"]["similarity_percent"],
            status="completed",
            results=report
        )
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)

        report["comparison_id"] = comparison.id
        return report
    finally:
        os.unlink(t1_path); os.unlink(t2_path)

@app.post("/api/compare/docx")
async def compare_docx(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as t1, \\
         tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as t2:
        t1.write(await file1.read()); t1_path = t1.name
        t2.write(await file2.read()); t2_path = t2.name

    try:
        text1 = extract_text_from_docx(t1_path)
        text2 = extract_text_from_docx(t2_path)
        report = compute_diff_report(text1, text2)
        report["file_type"] = "docx"
        
        if use_ai.lower() == "true":
            report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

        # Save history
        comparison = Comparison(
            user_id=current_user.id if current_user else 0,
            file1_name=file1.filename,
            file2_name=file2.filename,
            file1_type="docx",
            file2_type="docx",
            comparison_type="docx",
            similarity_score=report["stats"]["similarity_percent"],
            status="completed",
            results=report
        )
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)

        report["comparison_id"] = comparison.id
        return report
    finally:
        os.unlink(t1_path); os.unlink(t2_path)

@app.post("/api/compare/pptx")
async def compare_pptx(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as t1, \\
         tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as t2:
        t1.write(await file1.read()); t1_path = t1.name
        t2.write(await file2.read()); t2_path = t2.name

    try:
        text1 = extract_text_from_pptx(t1_path)
        text2 = extract_text_from_pptx(t2_path)
        report = compute_diff_report(text1, text2)
        report["file_type"] = "pptx"
        
        if use_ai.lower() == "true":
            report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

        # Save history
        comparison = Comparison(
            user_id=current_user.id if current_user else 0,
            file1_name=file1.filename,
            file2_name=file2.filename,
            file1_type="pptx",
            file2_type="pptx",
            comparison_type="pptx",
            similarity_score=report["stats"]["similarity_percent"],
            status="completed",
            results=report
        )
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)

        report["comparison_id"] = comparison.id
        return report
    finally:
        os.unlink(t1_path); os.unlink(t2_path)

@app.post("/api/compare/excel")
async def compare_excel(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    suffix = ".xlsx" if "xlsx" in file1.filename else ".xls"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as t1, \\
         tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as t2:
        t1.write(await file1.read()); t1_path = t1.name
        t2.write(await file2.read()); t2_path = t2.name

    try:
        text1 = extract_text_from_excel(t1_path)
        text2 = extract_text_from_excel(t2_path)
        report = compute_diff_report(text1, text2)
        report["file_type"] = "excel"
        
        if use_ai.lower() == "true":
            report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

        # Save history
        comparison = Comparison(
            user_id=current_user.id if current_user else 0,
            file1_name=file1.filename,
            file2_name=file2.filename,
            file1_type="excel",
            file2_type="excel",
            comparison_type="excel",
            similarity_score=report["stats"]["similarity_percent"],
            status="completed",
            results=report
        )
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)

        report["comparison_id"] = comparison.id
        return report
    finally:
        os.unlink(t1_path); os.unlink(t2_path)

@app.post("/api/compare/csv")
async def compare_csv(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as t1, \\
         tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as t2:
        t1.write(await file1.read()); t1_path = t1.name
        t2.write(await file2.read()); t2_path = t2.name

    try:
        text1 = extract_text_from_csv(t1_path)
        text2 = extract_text_from_csv(t2_path)
        report = compute_diff_report(text1, text2)
        report["file_type"] = "csv"
        
        if use_ai.lower() == "true":
            report["ai_analysis"] = await get_ai_analysis(text1, text2, report)

        # Save history
        comparison = Comparison(
            user_id=current_user.id if current_user else 0,
            file1_name=file1.filename,
            file2_name=file2.filename,
            file1_type="csv",
            file2_type="csv",
            comparison_type="csv",
            similarity_score=report["stats"]["similarity_percent"],
            status="completed",
            results=report
        )
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)

        report["comparison_id"] = comparison.id
        return report
    finally:
        os.unlink(t1_path); os.unlink(t2_path)

@app.post("/api/compare/image")
async def compare_image(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form("false"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    ext1 = os.path.splitext(file1.filename)[1] or ".png"
    ext2 = os.path.splitext(file2.filename)[1] or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext1) as t1, \\
         tempfile.NamedTemporaryFile(delete=False, suffix=ext2) as t2:
        t1.write(await file1.read()); t1_path = t1.name
        t2.write(await file2.read()); t2_path = t2.name

    try:
        report = image_diff(t1_path, t2_path)
        report["file_type"] = "image"
        
        if use_ai.lower() == "true" and GROQ_OK:
            report["ai_analysis"] = "AI image analysis: " + \\
                f"Found {report['stats']['changed_pixels']} different pixels " \\
                f"({report['stats']['difference_percent']}% of image changed)."

        # Save history
        comparison = Comparison(
            user_id=current_user.id if current_user else 0,
            file1_name=file1.filename,
            file2_name=file2.filename,
            file1_type="image",
            file2_type="image",
            comparison_type="image",
            similarity_score=report["stats"]["similarity_percent"],
            status="completed",
            results=report
        )
        db.add(comparison)
        await db.commit()
        await db.refresh(comparison)

        report["comparison_id"] = comparison.id
        return report
    finally:
        os.unlink(t1_path); os.unlink(t2_path)

@app.post("/api/ai/chat")
async def ai_chat(
    message: str = Form(...),
    context: str = Form(""),
    current_user: User = Depends(get_current_user)
):
    from groq import Groq
    GROQ_CLIENT = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
    try:
        response = GROQ_CLIENT.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": f"You are a document analysis assistant. Context from compared documents:\\n{context[:2000]}"},
                {"role": "user", "content": message}
            ],
            max_tokens=800,
            temperature=0.5
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(500, f"AI error: {str(e)}")

"""

new_content = content[:start_idx] + new_endpoints + content[end_idx:]

with open('docfinder/main.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Successfully patched main.py')
