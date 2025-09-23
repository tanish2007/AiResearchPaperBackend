# This file contains the function of data extraction.

import pdfplumber
import re
from collections import defaultdict

def extract_sections(pdf_path) -> dict:
    """Improved PDF section extraction using font analysis and spatial positioning"""
    sections = defaultdict(list)
    current_section = "Introduction"
    heading_pattern = re.compile(r'^(\d+\.\d*)\s+(.*)$')  # Improved pattern
    prev_doctop = None
    min_gap = 15  # Minimum vertical gap between sections

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Extract words with font attributes and positions
            words = page.extract_words(
                x_tolerance=3,
                y_tolerance=3,
                extra_attrs=["fontname", "size", "doctop"]
            )
            
            current_block = []
            for word in words:
                # Detect headings using font size/style and numbering pattern
                is_bold = 'Bold' in word['fontname']
                is_large = word['size'] > 12  # Adjust based on your document
                
                if (is_bold or is_large) and heading_pattern.match(word['text']):
                    if current_block:
                        sections[current_section].append(" ".join(current_block))
                        current_block = []
                    current_section = word['text']
                else:
                    # Group words into paragraphs using vertical positioning
                    if prev_doctop and (word['doctop'] - prev_doctop > min_gap):
                        if current_block:
                            sections[current_section].append(" ".join(current_block))
                            current_block = []
                    current_block.append(word['text'])
                    prev_doctop = word['doctop']

            if current_block:
                sections[current_section].append(" ".join(current_block))

    # Clean up results and convert to regular dict
    return {
        section: "\n".join(paragraphs).strip()
        for section, paragraphs in sections.items()
        if paragraphs
    }

# Usage
'''
document_sections = extract_sections("research.pdf")
print("Available sections:", list(document_sections.keys()))
'''