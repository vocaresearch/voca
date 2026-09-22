#!/usr/bin/env python3
"""Copy the supplied publication PDFs and render faithful web previews.
Requires PyMuPDF and Pillow only when regenerating previews.
"""
from pathlib import Path
import shutil
import fitz
from PIL import Image

PAGE = Path(__file__).resolve().parents[1]
SOURCES = {
    'overall': PAGE.parent / 'Fig/Overall.pdf',
    'vocaagent': PAGE.parent / 'VocaAgent.pdf',
    'agreement_summary': PAGE.parent / 'Fig/agreement_summary.pdf',
    'emotion_proactive_transfer': PAGE.parent / 'Fig/emotion_proactive_transfer.pdf',
}

def main():
    for name, source in SOURCES.items():
        pdf = PAGE / 'static/figures' / (name + '.pdf')
        preview = PAGE / 'static/images' / (name + '.webp')
        pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, pdf)
        with fitz.open(source) as document:
            assert len(document) == 1
            page = document[0]
            scale = 2800 / page.rect.width
            pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            image = Image.frombytes('RGB', (pixmap.width, pixmap.height), pixmap.samples)
            image.save(preview, 'WEBP', quality=95, method=6)
        print(f'{name}: {pixmap.width} × {pixmap.height}')

if __name__ == '__main__':
    main()
