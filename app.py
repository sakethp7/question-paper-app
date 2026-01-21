import streamlit as st
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json
from PIL import Image
import io

from models import QuestionPaperBase
from prompts import get_system_prompt
from utils import convert_pdf_to_images, process_uploaded_file

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Question Paper Extractor",
    page_icon="📄",
    layout="wide"
)

# Initialize Gemini client
@st.cache_resource
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("Please set GEMINI_API_KEY in your .env file")
        st.stop()
    return genai.Client(api_key=api_key)

def extract_questions_from_images(client, images, model_name, thinking_level="medium", media_resolution="medium"):
    """Extract questions from question paper images using Gemini API."""
    
    # Prepare content parts with all images
    content_parts = []
    for idx, img in enumerate(images):
        # Convert PIL Image to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        content_parts.append(
            types.Part.from_bytes(
                data=img_byte_arr,
                mime_type="image/png"
            )
        )
    
    # Add instruction text
    content_parts.append(
        types.Part.from_text(
            text="Extract all questions from this question paper following the schema and instructions provided."
        )
    )
    
    # Create content
    contents = [
        types.Content(
            role="user",
            parts=content_parts
        )
    ]
    
    # Map media resolution to API enum
    media_resolution_map = {
        "low": types.MediaResolution.MEDIA_RESOLUTION_LOW,
        "medium": types.MediaResolution.MEDIA_RESOLUTION_MEDIUM,
        "high": types.MediaResolution.MEDIA_RESOLUTION_HIGH
    }
    
    # Configure generation with schema
    # Gemini 2.5 Flash doesn't use thinking config
    if "2.5" in model_name or "gemini-2.5" in model_name.lower():
        generate_content_config = types.GenerateContentConfig(
            temperature=1.0,
            response_mime_type="application/json",
            response_schema=QuestionPaperBase,
            system_instruction=[types.Part.from_text(text=get_system_prompt())],
            media_resolution=media_resolution_map.get(media_resolution, types.MediaResolution.MEDIA_RESOLUTION_MEDIUM)
        )
    else:
        # Gemini 3 Flash uses thinking_level parameter
        generate_content_config = types.GenerateContentConfig(
            temperature=1.0,
            response_mime_type="application/json",
            response_schema=QuestionPaperBase,
            system_instruction=[types.Part.from_text(text=get_system_prompt())],
            thinking_config=types.ThinkingConfig(
                thinking_level=thinking_level,
            ),
            media_resolution=media_resolution_map.get(media_resolution, types.MediaResolution.MEDIA_RESOLUTION_MEDIUM)
        )
    
    # Generate content
    with st.spinner("🤖 Analyzing question paper with Gemini..."):
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=generate_content_config,
        )
    
    return response.text

def display_question_paper(question_paper_data):
    """Display extracted question paper in a formatted manner."""
    
    try:
        data = json.loads(question_paper_data)
        
        # Display total marks
        st.markdown("---")
        st.markdown(f"### 📊 Total Maximum Marks: **{data['total_max_marks']}**")
        st.markdown("---")
        
        # Display each question
        for idx, question in enumerate(data['questions'], 1):
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"#### Question {question['question_number']}")
                
                with col2:
                    st.markdown(f"**Marks:** {question['marks']}")
                
                # Question Type Badge
                type_color = "blue" if question['question_type'] == "MCQ" else "green"
                st.markdown(f"**Type:** :{type_color}[{question['question_type']}]")
                
                # Choice question indicator
                if question.get('is_choice_question', False):
                    st.info(f"🔀 Choice Question: {question.get('choice_instruction', '')}")
                
                # Question text in LaTeX
                st.markdown("**Question:**")
                try:
                    # Display using st.latex for mathematical expressions
                    # For mixed text and math, use markdown with $ delimiters
                    question_text = question['question_text']
                    st.markdown(question_text)
                except Exception as e:
                    st.write(question['question_text'])
                
                # Diagram description
                if question.get('diagram_description'):
                    st.markdown(f"**📐 Diagram:** {question['diagram_description']}")
                
                # Sub-parts mapping
                if question.get('sub_parts_mapping'):
                    st.markdown(f"**Sub-parts:** {question['sub_parts_mapping']}")
                
                st.markdown("---")
        
        # Download option
        st.download_button(
            label="📥 Download as JSON",
            data=question_paper_data,
            file_name="extracted_questions.json",
            mime="application/json"
        )
        
    except json.JSONDecodeError as e:
        st.error(f"Error parsing response: {e}")
        st.text("Raw response:")
        st.code(question_paper_data)

def main():
    st.title("📄 Question Paper Extractor")
    st.markdown("Upload a question paper PDF or images to extract questions in structured format with LaTeX rendering.")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Model selection
        model_name = st.selectbox(
            "Select Model",
            options=[
                "gemini-3-flash-preview",
                "gemini-2.5-flash"
            ],
            index=0,
            help="Choose between Gemini 3 Flash (latest) or Gemini 2.5 Flash"
        )
        
        # Thinking level/budget
        if "2.5" in model_name:
            st.info("Gemini 2.5 Flash doesn't use thinking configuration")
        else:
            thinking_level = st.selectbox(
                "Thinking Level",
                options=["low", "medium", "high"],
                index=1,
                help="Higher thinking level may produce more accurate results but takes longer"
            )
        
        # Media resolution
        media_resolution = st.selectbox(
            "Media Resolution",
            options=["low", "medium", "high"],
            index=1,
            help="Higher resolution improves text recognition but increases processing time and cost"
        )
        
        st.markdown("---")
        st.markdown("### 📋 Model Info")
        
        if "3-flash" in model_name:
            st.markdown("""
            **Gemini 3 Flash Preview**
            - Latest generation model
            - Advanced reasoning capabilities
            - Configurable thinking levels
            - Best for complex questions
            """)
        else:
            st.markdown("""
            **Gemini 2.5 Flash**
            - Fast and efficient
            - No thinking configuration
            - Good for standard extraction
            - Cost-efficient
            """)
        
        st.markdown("---")
        st.markdown("### 💡 About")
        st.markdown("""
        This app extracts questions from question papers with:
        - Mathematical notation in LaTeX
        - Question type identification
        - Choice question detection
        - Sub-parts preservation
        - Total marks calculation
        """)
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload Question Paper",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Upload a PDF or image of the question paper"
    )
    
    if uploaded_file is not None:
        # Process the uploaded file
        images = process_uploaded_file(uploaded_file)
        
        if images:
            # Display preview
            with st.expander("📋 Preview Uploaded Pages", expanded=False):
                cols = st.columns(min(len(images), 3))
                for idx, img in enumerate(images):
                    with cols[idx % 3]:
                        st.image(img, caption=f"Page {idx + 1}", use_container_width=True)
            
            # Extract button
            if st.button("🚀 Extract Questions", type="primary"):
                client = get_gemini_client()
                
                try:
                    # Set thinking_level based on model
                    current_thinking_level = "medium"  # default for 2.5
                    if "3-flash" in model_name:
                        current_thinking_level = thinking_level
                    
                    # Extract questions
                    result = extract_questions_from_images(
                        client, 
                        images,
                        model_name=model_name,
                        thinking_level=current_thinking_level,
                        media_resolution=media_resolution
                    )
                    
                    # Store in session state
                    st.session_state['extracted_data'] = result
                    st.success("✅ Questions extracted successfully!")
                    
                except Exception as e:
                    st.error(f"Error during extraction: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # Display results if available
    if 'extracted_data' in st.session_state:
        st.markdown("## 📋 Extracted Questions")
        display_question_paper(st.session_state['extracted_data'])

if __name__ == "__main__":
    main()
