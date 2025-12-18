#!/usr/bin/env python3
"""
Convert Word documents (.doc, .docx) to Markdown format.
Uses LibreOffice to convert .doc to .docx first, then pandoc to convert to Markdown.
"""

import os
import subprocess
import shutil
from pathlib import Path

# Directories
DOWNLOADS_DIR = "/Users/miguelgarcia/Desktop/FOF/Downloads"
MARKDOWN_DIR = "/Users/miguelgarcia/Desktop/FOF/Markdown"
TEMP_DIR = "/Users/miguelgarcia/Desktop/FOF/.temp_docx"


def convert_doc_to_docx(input_path, output_dir):
    """Convert a .doc file to .docx using LibreOffice."""
    try:
        result = subprocess.run(
            ["/opt/homebrew/bin/soffice", "--headless", "--convert-to", "docx", 
             "--outdir", str(output_dir), str(input_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            print(f"      ⚠️  LibreOffice error: {result.stderr}")
            return None
        
        # Return path to converted file
        docx_name = Path(input_path).stem + ".docx"
        return Path(output_dir) / docx_name
    except Exception as e:
        print(f"      ⚠️  Exception: {e}")
        return None


def convert_to_markdown(input_path, output_path):
    """Convert a Word document to Markdown using pandoc."""
    try:
        result = subprocess.run(
            ["pandoc", str(input_path), "-t", "gfm", "-o", str(output_path)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"      ⚠️  Pandoc error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"      ⚠️  Exception: {e}")
        return False


def main():
    print("=" * 60)
    print("Word to Markdown Converter (with .doc support)")
    print("=" * 60)
    
    # Create temp directory for .doc -> .docx conversions
    Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)
    
    total_converted = 0
    total_skipped = 0
    
    # Process each subfolder
    for folder_name in sorted(os.listdir(DOWNLOADS_DIR)):
        folder_path = Path(DOWNLOADS_DIR) / folder_name
        
        if not folder_path.is_dir():
            continue
            
        print(f"\n📂 Processing folder: {folder_name}")
        
        # Create corresponding markdown folder
        md_folder = Path(MARKDOWN_DIR) / folder_name
        md_folder.mkdir(parents=True, exist_ok=True)
        
        converted = 0
        
        # Process each file in the folder
        for file_name in sorted(os.listdir(folder_path)):
            file_path = folder_path / file_name
            file_lower = file_name.lower()
            
            # Skip non-Word files
            if not file_lower.endswith(('.doc', '.docx')):
                if file_lower.endswith('.pdf'):
                    print(f"   ⏭️  Skipping PDF: {file_name}")
                    total_skipped += 1
                continue
            
            # Create output filename
            md_name = Path(file_name).stem + ".md"
            output_path = md_folder / md_name
            
            print(f"   📄 Converting: {file_name}")
            
            # If .doc, first convert to .docx
            if file_lower.endswith('.doc') and not file_lower.endswith('.docx'):
                print(f"      🔄 Converting .doc to .docx first...")
                docx_path = convert_doc_to_docx(file_path, TEMP_DIR)
                if docx_path is None or not docx_path.exists():
                    print(f"      ❌ Failed to convert to .docx")
                    continue
                source_for_pandoc = docx_path
            else:
                source_for_pandoc = file_path
            
            # Convert to Markdown
            if convert_to_markdown(source_for_pandoc, output_path):
                print(f"      ✅ -> {md_name}")
                converted += 1
            else:
                print(f"      ❌ Failed to convert to Markdown")
        
        print(f"   📊 Converted {converted} files")
        total_converted += converted
    
    # Cleanup temp directory
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    
    print("\n" + "=" * 60)
    print(f"✅ Conversion complete!")
    print(f"📊 Total converted: {total_converted} files")
    print(f"⏭️  Skipped PDFs: {total_skipped}")
    print(f"📁 Markdown files saved to: {MARKDOWN_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
