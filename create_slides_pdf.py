#!/usr/bin/env python3
"""Render interactive slides.html into high-resolution 16:9 slides.pdf using Playwright."""
import os
import shutil
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
SLIDES_HTML = ROOT / "slides" / "slides.html"
SLIDES_PDF = ROOT / "slides" / "slides.pdf"
ROOT_PDF = ROOT / "slides.pdf"
PAPER_PDF = ROOT / "paper" / "slides.pdf"


def generate_pdf():
    if not SLIDES_HTML.exists():
        print(f"Error: {SLIDES_HTML} not found!", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {SLIDES_HTML} in headless Chromium...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Create page with 16:9 1080p viewport
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        
        # Open local HTML presentation
        page.goto(SLIDES_HTML.as_uri(), wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Ensure background colors and fonts are loaded
        page.emulate_media(media="print")
        
        print("Rendering 8 slides to PDF (1920x1080 16:9 aspect ratio)...")
        page.pdf(
            path=str(SLIDES_PDF),
            width="1920px",
            height="1080px",
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "0px", "right": "0px", "bottom": "0px", "left": "0px"},
        )
        browser.close()

    print(f"Successfully generated: {SLIDES_PDF}")

    # Copy to root and paper directory
    shutil.copy2(SLIDES_PDF, ROOT_PDF)
    print(f"Copied to: {ROOT_PDF}")
    (ROOT / "paper").mkdir(exist_ok=True)
    shutil.copy2(SLIDES_PDF, PAPER_PDF)
    print(f"Copied to: {PAPER_PDF}")


if __name__ == "__main__":
    generate_pdf()
