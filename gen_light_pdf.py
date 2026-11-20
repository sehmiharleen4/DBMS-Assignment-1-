"""Generate a light-theme slides PDF — one slide per page, guaranteed."""
import asyncio, pathlib, shutil, io
from playwright.async_api import async_playwright
from pypdf import PdfReader, PdfWriter

REPO = pathlib.Path(r"C:\Users\2006s\.gemini\antigravity\scratch\G9-DBMS-Assignment-1")
SRC = REPO / "slides" / "slides.html"
OUT = REPO / "slides" / "G9_Presentation_Slides.pdf"

async def main():
    html = SRC.read_text(encoding="utf-8")
    # Force light theme
    html = html.replace('<html lang="en">', '<html lang="en" data-theme="light">')
    
    LIGHT = REPO / "slides" / "slides_print.html"
    LIGHT.write_text(html, encoding="utf-8")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 810})
        await page.goto(LIGHT.as_uri(), wait_until="networkidle")
        await page.wait_for_timeout(2000)

        total = await page.evaluate("document.querySelectorAll('.slide').length")
        print(f"Found {total} slides")

        writer = PdfWriter()

        for i in range(total):
            # Show only current slide
            await page.evaluate(f"""
                document.querySelectorAll('.slide').forEach((s, j) => {{
                    if (j === {i}) {{
                        s.style.display = 'flex';
                        s.style.opacity = '1';
                        s.style.position = 'relative';
                        s.style.width = '1440px';
                        s.style.height = '810px';
                        s.style.overflow = 'hidden';
                    }} else {{
                        s.style.display = 'none';
                    }}
                }});
                // Hide nav elements
                document.querySelectorAll('.nav-controls, .progress-bar, .slide-counter, .keyboard-hint, footer, .speaker-notes, .notes-panel').forEach(e => e.style.display = 'none');
            """)
            await page.wait_for_timeout(300)

            pdf_bytes = await page.pdf(
                width="1440px",
                height="810px",
                print_background=True,
                prefer_css_page_size=False,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )

            reader = PdfReader(io.BytesIO(pdf_bytes))
            # Take only the first page (the one with content)
            writer.add_page(reader.pages[0])
            print(f"  Slide {i+1}/{total} captured")

        with open(OUT, "wb") as f:
            writer.write(f)

    size_kb = OUT.stat().st_size // 1024
    print(f"Wrote {OUT} ({size_kb} KB, {len(writer.pages)} pages)")

    shutil.copy2(OUT, REPO / "G9_Presentation_Slides.pdf")
    shutil.copy2(OUT, REPO / "slides.pdf")
    print("Copied to root")

asyncio.run(main())
