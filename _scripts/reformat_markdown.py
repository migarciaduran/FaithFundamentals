#!/usr/bin/env python3
"""
Reformat FOF lesson markdown files to use native markdown conventions.
- Removes HTML tables used for headers
- Creates clickable Table of Contents with anchor links
- Fixes escaped numbered lists (1\\. -> 1.)
- Standardizes heading hierarchy
- Cleans up formatting issues
"""

import re
from pathlib import Path

# Mapping of lesson numbers to titles
LESSON_TITLES = {
    "00": "Introduction",
    "01": "The Bible",
    "02": "Studying the Bible",
    "03": "Attributes of God",
    "04": "Person of Jesus Christ",
    "05": "Work of Christ",
    "06": "Salvation",
    "07": "Holy Spirit",
    "08": "Prayer",
    "09": "Church, Fellowship and Worship",
    "10": "Spiritual Gifts",
    "11": "Evangelism",
    "12": "Obedience and God's Will (Part 1)",
    "13": "Obedience and God's Will (Part 2)",
}


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug for anchor links."""
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'\s+', '-', text.strip())
    text = re.sub(r'-+', '-', text)
    return text


def remove_html_tables(content: str) -> str:
    """Remove HTML table structures that were used for page headers."""
    pattern = r'<table[^>]*>.*?</table>\s*'
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    return content


def fix_escaped_numbers(content: str) -> str:
    """Fix escaped numbered lists: 1\\. -> 1."""
    content = re.sub(r'(\d+)\\.', r'\1.', content)
    return content


def fix_underline_tags(content: str) -> str:
    """Convert <u>text</u> to _text_ (emphasis)."""
    content = re.sub(r'<u>([^<]+)</u>', r'_\1_', content)
    return content


def remove_duplicate_headers(content: str) -> str:
    """Remove duplicate page headers and lesson titles from the original document."""
    # Remove lines like "***Fundamentals of the Faith***"
    content = re.sub(r'^\*{3}Fundamentals of the Faith\*{3}\s*$', '', content, flags=re.MULTILINE)
    
    # Remove lines like "# Lesson \#3 – God: His Character & Attributes" (original h1 headers)
    content = re.sub(r'^#\s+Lesson\s+\\?#?\d+.*$', '', content, flags=re.MULTILINE)
    
    # Remove decorative lines like "**═════════════════════════════════════════════════════════════════**"
    content = re.sub(r'^\*\*[═=─-]+\*\*\s*$', '', content, flags=re.MULTILINE)
    
    return content


def remove_old_toc(content: str) -> str:
    """Remove the old Word-style Table of Contents section entirely."""
    # The TOC section starts at "**Table of Contents**"
    # and ends when we hit the actual content section
    
    # First, find "**Table of Contents**"
    toc_header_match = re.search(r'\*\*Table of Contents\*\*', content)
    if not toc_header_match:
        return content
    
    toc_start = toc_header_match.start()
    after_header = content[toc_header_match.end():]
    
    # Find the end of TOC. The TOC contains entries with ellipsis/dots.
    # The actual content starts with:
    # - An HTML <table> tag (page break marker), or
    # - "***Fundamentals" (triple asterisk - page header repeat), or
    # - A section header like "**Lesson Outline**" (no dots)
    # We need to skip TOC entries that have ellipsis patterns
    
    end_patterns = [
        r'<table',
        r'\*{3}Fundamentals',  # Triple asterisk page header
        r'\*\*Lesson Outline\*\*',
    ]
    
    toc_end_offset = len(after_header)
    for pattern in end_patterns:
        match = re.search(pattern, after_header, re.IGNORECASE)
        if match and match.start() < toc_end_offset:
            toc_end_offset = match.start()
    
    # Remove the TOC section entirely
    before_toc = content[:toc_start]
    after_toc = after_header[toc_end_offset:]
    
    return before_toc + after_toc


def extract_sections_for_toc(content: str) -> list:
    """Extract section headers from the content for building TOC."""
    sections = []
    seen_titles = set()  # Track seen titles to avoid duplicates
    
    # Pattern for Roman numeral sections in the content
    # Matches: **I. Title** or **II. Title ...** with or without content after
    roman_pattern = r'^\*\*(I{1,3}|IV|VI{0,3}|IX|X{1,3}?)\.\s*([^*\n]+)'
    
    for match in re.finditer(roman_pattern, content, re.MULTILINE):
        numeral = match.group(1)
        title = match.group(2).strip()
        # Clean up title - remove trailing ** and other artifacts
        title = re.sub(r'\*\*.*$', '', title).strip()
        # Remove dotted lines, ellipses, and page numbers
        title = re.sub(r'[\.…]+\s*\d*\s*$', '', title).strip()
        title = re.sub(r'\s+\d+\s*$', '', title).strip()  # Remove trailing page numbers
        # Remove trailing standalone dashes with content after (like " - 1")
        title = re.sub(r'\s+[-–]\s+\d+\s*$', '', title).strip()
        
        if title and len(title) > 2:
            # Normalize for duplicate detection:
            # - lowercase
            # - remove "of the bible", "of the", etc. suffixes
            # - remove special chars
            normalized = title.lower()
            normalized = re.sub(r'\s+(of the bible|of the).*$', '', normalized)
            normalized = re.sub(r'[^\w\s]', '', normalized).strip()
            # Also normalize by roman numeral to catch same section with different titles
            numeral_key = f"{numeral}_{normalized.split()[0] if normalized.split() else ''}"
            
            if normalized not in seen_titles and numeral_key not in seen_titles:
                seen_titles.add(normalized)
                seen_titles.add(numeral_key)
                sections.append((f"{numeral}. {title}", 0))
    
    return sections


def build_toc(sections: list) -> str:
    """Build a markdown Table of Contents from sections."""
    if not sections:
        return ""
    
    lines = ["## Table of Contents\n"]
    for title, level in sections:
        slug = slugify(title)
        indent = "  " * level
        lines.append(f"{indent}- [{title}](#{slug})")
    
    return '\n'.join(lines) + '\n\n---\n\n'


def convert_headers_to_markdown(content: str) -> str:
    """Convert bold headers to proper markdown headers."""
    lines = content.split('\n')
    result = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip lines that are just dots (TOC remnants)
        if re.match(r'^\.+\s*\d*\s*\**$', stripped):
            continue
        if re.match(r'^\d+\**$', stripped):
            continue
            
        # Check for Roman numeral main sections
        roman_match = re.match(r'^\*\*(I{1,3}|IV|VI{0,3}|IX|X{1,3}?)\.\s*(.+?)\*\*\s*$', stripped)
        if roman_match:
            numeral = roman_match.group(1)
            title = roman_match.group(2).strip()
            result.append(f'\n## {numeral}. {title}\n')
            continue
        
        # Roman numeral with trailing content (not closed with **)
        roman_open_match = re.match(r'^\*\*(I{1,3}|IV|VI{0,3}|IX|X{1,3}?)\.\s*([^*]+)$', stripped)
        if roman_open_match:
            numeral = roman_open_match.group(1)
            title = roman_open_match.group(2).strip()
            result.append(f'\n## {numeral}. {title}\n')
            continue
        
        # Letter subsections: **A. Title**
        letter_match = re.match(r'^\*\*([A-Z])\.\s*(.+?)\*\*\s*$', stripped)
        if letter_match:
            letter = letter_match.group(1)
            title = letter_match.group(2).strip()
            result.append(f'\n### {letter}. {title}\n')
            continue
        
        # Letter subsections with dash and scripture: **A. Title** - Scripture
        letter_scripture_match = re.match(r'^\*\*([A-Z])\.\s*([^*]+?)\*\*\s*[-–]\s*(.+)$', stripped)
        if letter_scripture_match:
            letter = letter_scripture_match.group(1)
            title = letter_scripture_match.group(2).strip()
            scripture = letter_scripture_match.group(3).strip()
            result.append(f'\n### {letter}. {title}\n')
            result.append(f'*{scripture}*\n')
            continue
        
        # Numbered sub-subsections: **1. Title**
        number_match = re.match(r'^\*\*(\d+)\.\s*(.+?)\*\*\s*$', stripped)
        if number_match:
            number = number_match.group(1)
            title = number_match.group(2).strip()
            result.append(f'\n#### {number}. {title}\n')
            continue
        
        # Numbered with scripture: **1. Title** - Scripture
        number_scripture_match = re.match(r'^\*\*(\d+)\.\s*([^*]+?)\*\*\s*[-–]\s*(.+)$', stripped)
        if number_scripture_match:
            number = number_scripture_match.group(1)
            title = number_scripture_match.group(2).strip()
            scripture = number_scripture_match.group(3).strip()
            result.append(f'\n#### {number}. {title}\n')
            result.append(f'*{scripture}*\n')
            continue
        
        result.append(line)
    
    return '\n'.join(result)


def clean_orphaned_content(content: str) -> str:
    """Remove orphaned dotted lines, page markers, and broken formatting."""
    lines = content.split('\n')
    result = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip lines that are primarily dots or ellipsis with optional page numbers
        if re.match(r'^[\.…]{3,}', stripped):
            continue
        
        # Skip lines that are just page numbers/markers like "i**" or "1**"
        if re.match(r'^[ivxIVX\d]+\*{0,2}$', stripped):
            continue
        
        # Skip orphaned bold text that's unclosed (starts with ** but no closing **)
        # Matches things like "**Objective & Preliminary Comments" (no closing **)
        if stripped.startswith('**') and stripped.count('**') == 1:
            continue
        
        # Remove trailing dots, ellipsis, and page numbers from lines
        cleaned = re.sub(r'[\.…]{3,}\s*[ivxIVX\d]*\*{0,2}\s*$', '', line)
        # Also clean up trailing page numbers after dots/ellipsis
        cleaned = re.sub(r'[\.…]+\s*\d+\s*$', '', cleaned)
        result.append(cleaned)
    
    return '\n'.join(result)


def clean_extra_whitespace(content: str) -> str:
    """Clean up excessive blank lines and whitespace."""
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    lines = [line.rstrip() for line in content.split('\n')]
    # Remove empty lines at the start
    while lines and not lines[0].strip():
        lines.pop(0)
    return '\n'.join(lines)


def add_document_header(content: str, lesson_num: str, lesson_title: str) -> str:
    """Add a proper markdown document header."""
    header = f"""# Fundamentals of the Faith

## Lesson {lesson_num}: {lesson_title}

---

"""
    return header + content


def process_file(filepath: Path) -> None:
    """Process a single markdown file."""
    print(f"Processing: {filepath.name}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract lesson number from filename
    match = re.search(r'L(\d+)', filepath.name)
    lesson_num = match.group(1) if match else "?"
    
    # Get lesson title from our mapping
    lesson_title = LESSON_TITLES.get(lesson_num, "Unknown")
    
    # Extract sections before modifying content
    sections = extract_sections_for_toc(content)
    
    # Apply transformations
    content = remove_html_tables(content)
    content = fix_escaped_numbers(content)
    content = fix_underline_tags(content)
    content = remove_old_toc(content)
    content = remove_duplicate_headers(content)
    content = convert_headers_to_markdown(content)
    content = clean_orphaned_content(content)
    content = clean_extra_whitespace(content)
    
    # Build and insert new TOC
    toc = build_toc(sections)
    
    # Add document header with TOC
    header = f"""# Fundamentals of the Faith

## Lesson {lesson_num}: {lesson_title}

---

{toc}"""
    
    content = header + content
    
    # Final cleanup
    content = clean_extra_whitespace(content)
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  ✓ Reformatted: Lesson {lesson_num} - {lesson_title}")


def main():
    """Main entry point."""
    lessons_dir = Path(__file__).parent.parent / "Markdown" / "FoF_Lessons"
    
    if not lessons_dir.exists():
        print(f"Error: Directory not found: {lessons_dir}")
        return
    
    # Process all FoF_L*.md files
    lesson_files = sorted(lessons_dir.glob("FoF_L*.md"))
    
    if not lesson_files:
        print("No lesson files found matching FoF_L*.md")
        return
    
    print(f"Found {len(lesson_files)} lesson files to process\n")
    
    for filepath in lesson_files:
        try:
            process_file(filepath)
        except Exception as e:
            print(f"  ✗ Error processing {filepath.name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n✓ Done!")


if __name__ == "__main__":
    main()
