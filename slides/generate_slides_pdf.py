"""Render slides.html into a 16:9 presentation PDF using Playwright."""
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(r"C:\Users\2006s\.gemini\antigravity\scratch\G9-DBMS-Assignment-1")
SLIDES_DIR = ROOT / "slides"
HTML_PATH = SLIDES_DIR / "slides.html"
PDF_PATH = SLIDES_DIR / "G9_Presentation_Slides.pdf"
ROOT_PDF_PATH = ROOT / "G9_Presentation_Slides.pdf"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto(f"file:///{HTML_PATH.as_posix()}", wait_until="networkidle")

    # Inject print-friendly styling to display all slides sequentially for PDF printing
    page.add_style_tag(content="""
        @page {
            size: 1920px 1080px;
            margin: 0;
        }
        html, body {
            background: #0d1117 !important;
            margin: 0 !important;
            padding: 0 !important;
            width: 1920px !important;
            height: auto !important;
            overflow: visible !important;
        }
        .nav-controls, .progress-bar { display: none !important; }
        .deck-container {
            width: 1920px !important;
            max-width: none !important;
            height: auto !important;
            max-height: none !important;
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
            border-radius: 0 !important;
        }
        .slide {
            display: flex !important;
            box-sizing: border-box !important;
            width: 1920px !important;
            height: 1080px !important;
            padding: 60px 80px !important;
            page-break-after: always !important;
            break-after: page !important;
        }
    """)

    page.pdf(
        path=str(PDF_PATH),
        width="1920px",
        height="1080px",
        print_background=True,
        margin={"top": "0px", "bottom": "0px", "left": "0px", "right": "0px"}
    )
    browser.close()

shutil.copy2(PDF_PATH, ROOT_PDF_PATH)
print(f"Generated {PDF_PATH} and {ROOT_PDF_PATH} successfully!")
