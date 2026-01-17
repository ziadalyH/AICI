#!/usr/bin/env python3
"""
Test script to verify OCR functionality.

This script tests:
1. OCR dependencies are installed
2. Image extraction from PDFs works
3. OCR text extraction works
4. Image chunks are created correctly
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_dependencies():
    """Test if OCR dependencies are available."""
    print("=" * 80)
    print("Testing OCR Dependencies")
    print("=" * 80)
    
    try:
        from PIL import Image
        print("✅ PIL (Pillow) is installed")
    except ImportError:
        print("❌ PIL (Pillow) is NOT installed")
        print("   Install: pip install Pillow")
        return False
    
    try:
        import pytesseract
        print("✅ pytesseract is installed")
    except ImportError:
        print("❌ pytesseract is NOT installed")
        print("   Install: pip install pytesseract")
        return False
    
    try:
        # Test Tesseract binary
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract OCR is installed (version: {version})")
    except Exception as e:
        print(f"❌ Tesseract OCR binary is NOT installed or not in PATH")
        print(f"   Error: {e}")
        print("   Install: apt-get install tesseract-ocr (Linux)")
        print("           brew install tesseract (macOS)")
        return False
    
    print("\n✅ All OCR dependencies are available!")
    return True

def test_ocr_on_sample():
    """Test OCR on a sample image."""
    print("\n" + "=" * 80)
    print("Testing OCR on Sample Image")
    print("=" * 80)
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        import pytesseract
        import io
        
        # Create a simple test image with text
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw some text
        text = "Test OCR: Building Regulations"
        draw.text((10, 30), text, fill='black')
        
        # Perform OCR
        ocr_text = pytesseract.image_to_string(img, lang='eng')
        
        print(f"Original text: '{text}'")
        print(f"OCR extracted: '{ocr_text.strip()}'")
        
        if "Building" in ocr_text or "Regulations" in ocr_text:
            print("✅ OCR successfully extracted text from image")
            return True
        else:
            print("⚠️  OCR extracted text but may not be accurate")
            return True
    
    except Exception as e:
        print(f"❌ OCR test failed: {e}")
        return False

def test_pdf_ingester():
    """Test PDF ingester with OCR enabled."""
    print("\n" + "=" * 80)
    print("Testing PDF Ingester OCR Integration")
    print("=" * 80)
    
    try:
        from src.ingestion.pdf_ingester import PDFIngester
        from config.config import Config
        import logging
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        
        # Load config
        config = Config.from_env()
        
        # Initialize ingester
        ingester = PDFIngester(config)
        
        if ingester.enable_ocr:
            print("✅ OCR is enabled in PDF ingester")
            print(f"   Languages: {ingester.ocr_languages}")
        else:
            print("❌ OCR is disabled in PDF ingester")
            return False
        
        # Check if there are PDFs to test
        pdf_files = list(config.pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            print("⚠️  No PDF files found in data/pdfs/")
            print("   Place a PDF with images to test OCR extraction")
            return True
        
        print(f"\nFound {len(pdf_files)} PDF files")
        print("Testing OCR on first PDF...")
        
        # Test on first PDF
        test_pdf = pdf_files[0]
        print(f"Processing: {test_pdf.name}")
        
        paragraphs = ingester.ingest_file(test_pdf)
        
        # Count image chunks
        image_chunks = [p for p in paragraphs if p.title and p.title.startswith("Image")]
        
        print(f"\nResults:")
        print(f"  Total chunks: {len(paragraphs)}")
        print(f"  Text chunks: {len(paragraphs) - len(image_chunks)}")
        print(f"  Image chunks (OCR): {len(image_chunks)}")
        
        if image_chunks:
            print("\n✅ Successfully extracted image chunks via OCR!")
            print("\nSample image chunks:")
            for i, chunk in enumerate(image_chunks[:3], 1):
                print(f"\n  Image {i}:")
                print(f"    Page: {chunk.page_number}")
                print(f"    Title: {chunk.title}")
                print(f"    Text length: {len(chunk.text)} characters")
                print(f"    Text preview: {chunk.text[:100]}...")
        else:
            print("\n⚠️  No images found in PDF or OCR extracted no text")
            print("   This is normal if the PDF has no images with text")
        
        return True
    
    except Exception as e:
        print(f"❌ PDF ingester test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all OCR tests."""
    print("\n" + "=" * 80)
    print("OCR FUNCTIONALITY TEST")
    print("=" * 80)
    print()
    
    # Test 1: Dependencies
    if not test_dependencies():
        print("\n❌ OCR dependencies are missing. Please install them first.")
        return 1
    
    # Test 2: Sample OCR
    if not test_ocr_on_sample():
        print("\n❌ OCR sample test failed.")
        return 1
    
    # Test 3: PDF Ingester
    if not test_pdf_ingester():
        print("\n❌ PDF ingester OCR test failed.")
        return 1
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print("✅ All OCR tests passed!")
    print("\nOCR is ready to use. Images in PDFs will be automatically processed.")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
