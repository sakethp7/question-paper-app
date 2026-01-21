import io
from PIL import Image
import pymupdf
import streamlit as st
from typing import List

def convert_pdf_to_images(pdf_bytes: bytes, dpi: int = 300) -> List[Image.Image]:
    """
    Convert PDF bytes to a list of PIL Images using PyMuPDF.

    Args:
        pdf_bytes: PDF file content as bytes
        dpi: Resolution for conversion (higher = better quality but slower)

    Returns:
        List of PIL Image objects, one per page
    """
    try:
        images = []
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        zoom = dpi / 72  # PyMuPDF default is 72 DPI
        mat = pymupdf.Matrix(zoom, zoom)

        for page in doc:
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)

        doc.close()
        return images
    except Exception as e:
        st.error(f"Error converting PDF to images: {str(e)}")
        return []

def process_uploaded_file(uploaded_file) -> List[Image.Image]:
    """
    Process uploaded file (PDF or image) and return list of images.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
    
    Returns:
        List of PIL Image objects
    """
    images = []
    
    try:
        file_bytes = uploaded_file.read()
        file_type = uploaded_file.type
        
        if file_type == "application/pdf":
            # Convert PDF to images
            with st.spinner("📄 Converting PDF to images..."):
                images = convert_pdf_to_images(file_bytes, dpi=200)
            
            if images:
                st.success(f"✅ Converted PDF to {len(images)} page(s)")
        
        elif file_type in ["image/png", "image/jpeg", "image/jpg"]:
            # Handle image files
            image = Image.open(io.BytesIO(file_bytes))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            images = [image]
            st.success("✅ Image loaded successfully")
        
        else:
            st.error(f"Unsupported file type: {file_type}")
        
        return images
    
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return []

def validate_latex(text: str) -> bool:
    """
    Basic validation to check if text contains valid LaTeX delimiters.
    
    Args:
        text: String potentially containing LaTeX
    
    Returns:
        True if LaTeX syntax appears valid, False otherwise
    """
    # Check for balanced $ delimiters
    single_dollar_count = text.count('$') - text.count('$$') * 2
    double_dollar_count = text.count('$$')
    
    # Single $ should appear in pairs
    if single_dollar_count % 2 != 0:
        return False
    
    # Double $$ should appear in pairs
    if double_dollar_count % 2 != 0:
        return False
    
    return True

def format_question_for_display(question_text: str) -> str:
    """
    Format question text for better display in Streamlit.
    Ensures proper LaTeX rendering with markdown.
    
    Args:
        question_text: Raw question text with LaTeX
    
    Returns:
        Formatted text ready for st.markdown()
    """
    # Split by line breaks
    lines = question_text.split('\n')
    formatted_lines = []
    
    for line in lines:
        # Preserve LaTeX math delimiters
        formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

def estimate_processing_time(num_pages: int) -> str:
    """

    """
    # Rough estimate: 10-15 seconds per page with Gemini 3
    base_time = num_pages * 12
    
    if base_time < 60:
        return f"~{base_time} seconds"
    else:
        minutes = base_time // 60
        return f"~{minutes} minute(s)"
