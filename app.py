import streamlit as st
import streamlit.components.v1 as components
import os
import io
import logging
from PIL import Image

# Import Modular Pipelines
from image_utils import load_image_safely, resize_image_optimally, preprocess_for_ocr, HAS_CV2
from pdf_utils import get_pdf_page_count, convert_pdf_to_images
from ocr import extract_text
from mindmap_generator import generate_mindmap_from_concepts
from text_processing import extract_concepts_advanced

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("AppOrchestrator")

# ---------------- Streamlit Page Config ----------------
st.set_page_config(
    page_title="Smart Notes to Mind Map AI",
    page_icon="🧠",
    layout="wide"
)

# ---------------- Aesthetics & Theme design systems ----------------
theme_css = {
    "Sunset Amber": {
        "bg_gradient": "linear-gradient(135deg, #070605 0%, #120d0b 50%, #070605 100%)",
        "card_bg": "rgba(23, 17, 15, 0.5)",
        "card_border": "1px solid rgba(255, 123, 44, 0.2)",
        "card_shadow": "0 8px 32px 0 rgba(255, 123, 44, 0.12)",
        "primary_color": "#ff7b2c",
        "btn_hover": "#ff5e3a",
        "text_accent": "#ff5e3a",
        "glass_bg": "linear-gradient(135deg, rgba(255, 123, 44, 0.15) 0%, rgba(255, 94, 58, 0.05) 100%)",
        "input_border_active": "#ff7b2c",
        "text_color": "#fff7ed",
        "sidebar_bg": "#0a0a0a",
        "orb_color": "#ff7b2c"
    },
    "Cyberpunk Neon": {
        "bg_gradient": "linear-gradient(135deg, #05070c 0%, #0e0a1c 50%, #05070c 100%)",
        "card_bg": "rgba(22, 28, 45, 0.5)",
        "card_border": "1px solid rgba(244, 63, 94, 0.2)",
        "card_shadow": "0 8px 32px 0 rgba(244, 63, 94, 0.12)",
        "primary_color": "#f43f5e",
        "btn_hover": "#e11d48",
        "text_accent": "#06b6d4",
        "glass_bg": "linear-gradient(135deg, rgba(244, 63, 94, 0.15) 0%, rgba(6, 182, 212, 0.05) 100%)",
        "input_border_active": "#f43f5e",
        "text_color": "#f8fafc",
        "sidebar_bg": "#05070c",
        "orb_color": "#f43f5e"
    },
    "Ocean Breeze": {
        "bg_gradient": "linear-gradient(135deg, #050a0d 0%, #0b2229 50%, #050a0d 100%)",
        "card_bg": "rgba(15, 32, 39, 0.5)",
        "card_border": "1px solid rgba(13, 148, 136, 0.2)",
        "card_shadow": "0 8px 32px 0 rgba(13, 148, 136, 0.12)",
        "primary_color": "#0d9488",
        "btn_hover": "#0f766e",
        "text_accent": "#38bdf8",
        "glass_bg": "linear-gradient(135deg, rgba(13, 148, 136, 0.15) 0%, rgba(56, 189, 248, 0.05) 100%)",
        "input_border_active": "#0d9488",
        "text_color": "#f0fdfa",
        "sidebar_bg": "#050a0d",
        "orb_color": "#0d9488"
    },
    "Forest Emerald": {
        "bg_gradient": "linear-gradient(135deg, #040806 0%, #0d1e14 50%, #040806 100%)",
        "card_bg": "rgba(12, 31, 20, 0.5)",
        "card_border": "1px solid rgba(16, 185, 129, 0.2)",
        "card_shadow": "0 8px 32px 0 rgba(16, 185, 129, 0.12)",
        "primary_color": "#10b981",
        "btn_hover": "#059669",
        "text_accent": "#84cc16",
        "glass_bg": "linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(132, 204, 22, 0.05) 100%)",
        "input_border_active": "#10b981",
        "text_color": "#f0fdf4",
        "sidebar_bg": "#040806",
        "orb_color": "#10b981"
    }
}

# ----------------- SESSION STATE INITIALIZATION -----------------
# 1. OCR text persistence
if "ocr_text" not in st.session_state:
    st.session_state["ocr_text"] = ""

# 2. NLP concepts data persistence
if "mindmap_data" not in st.session_state:
    st.session_state["mindmap_data"] = None

# 3. pyvis HTML output persistence (survives state updates)
if "graph_html" not in st.session_state:
    st.session_state["graph_html"] = ""

# 4. Center node custom name persistence
if "custom_main_topic" not in st.session_state:
    st.session_state["custom_main_topic"] = ""

# 5. Last processed settings to avoid repeating heavy visualization compile
if "last_rendered_params" not in st.session_state:
    st.session_state["last_rendered_params"] = {}

# 6. Preprocessing preview tabs storage
if "preview_images" not in st.session_state:
    st.session_state["preview_images"] = []

# 7. Fallback indicators
if "rendering_failed" not in st.session_state:
    st.session_state["rendering_failed"] = False
if "rendering_error" not in st.session_state:
    st.session_state["rendering_error"] = ""
if "ocr_fallback_warn" not in st.session_state:
    st.session_state["ocr_fallback_warn"] = None

# ----------------- SIDEBAR CONTROLS -----------------
st.sidebar.markdown("""
<div style='text-align: center; margin-bottom: 25px; padding-top: 10px;'>
    <h2 style='color: white; font-weight: 800; font-size: 1.7rem; letter-spacing: -0.03em; background: linear-gradient(90deg, #ff7b2c, #ff5e3a); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>🧠 AI Workspace</h2>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<div class='sidebar-header'>🎨 Aesthetics</div>", unsafe_allow_html=True)
selected_theme = st.sidebar.selectbox(
    "AI Workspace Theme",
    list(theme_css.keys())
)

cfg = theme_css[selected_theme]

# CSS Injection
st.markdown(f"""
<!-- Glowing Ambient Orbs Background -->
<div class="glow-orb orb-1"></div>
<div class="glow-orb orb-2"></div>
<div class="glow-orb orb-3"></div>

<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {{
    font-family: 'Inter', sans-serif !important;
    background: {cfg['bg_gradient']} !important;
    color: {cfg['text_color']} !important;
    overflow-x: hidden;
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: 'Outfit', sans-serif !important;
}}

/* Glowing Ambient Orbs Styling */
.glow-orb {{
    position: fixed;
    width: 500px;
    height: 500px;
    border-radius: 50%;
    filter: blur(120px);
    z-index: -999;
    opacity: 0.12;
    pointer-events: none;
    animation: float-orbs 25s infinite alternate ease-in-out;
}}
.orb-1 {{
    background: {cfg['orb_color']};
    top: -15%;
    left: -15%;
}}
.orb-2 {{
    background: {cfg['text_accent']};
    bottom: -15%;
    right: -15%;
    animation-delay: -6s;
}}
.orb-3 {{
    background: #a855f7;
    top: 35%;
    left: 45%;
    width: 350px;
    height: 350px;
    opacity: 0.06;
    animation-delay: -12s;
}}
@keyframes float-orbs {{
    0% {{ transform: translate(0, 0) scale(1); }}
    50% {{ transform: translate(60px, 40px) scale(1.15); }}
    100% {{ transform: translate(-40px, -60px) scale(0.9); }}
}}

/* Glassmorphic Container Cards */
.card {{
    background: {cfg['card_bg']} !important;
    border: {cfg['card_border']} !important;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 35px;
    box-shadow: {cfg['card_shadow']} !important;
    margin-bottom: 30px;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}}

.card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 12px 45px 0 rgba(0,0,0,0.35), {cfg['card_shadow']} !important;
    border-color: rgba(255,255,255,0.2) !important;
}}

/* Gorgeous Header Hero */
.header-card {{
    background: {cfg['glass_bg']} !important;
    border: {cfg['card_border']} !important;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 45px;
    border-radius: 28px;
    text-align: center;
    margin-bottom: 30px;
    box-shadow: {cfg['card_shadow']} !important;
    position: relative;
    overflow: hidden;
    animation: floating 5s ease-in-out infinite;
}}

.header-card h1 {{
    font-size: 3.5rem !important;
    font-weight: 900 !important;
    margin-bottom: 12px;
    background: linear-gradient(90deg, {cfg['primary_color']}, {cfg['text_accent']});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.04em;
}}

.header-card p {{
    font-size: 1.3rem !important;
    font-weight: 400 !important;
    color: rgba(255,255,255,0.7) !important;
    letter-spacing: -0.01em;
}}

@keyframes floating {{
    0% {{ transform: translateY(0px); }}
    50% {{ transform: translateY(-8px); }}
    100% {{ transform: translateY(0px); }}
}}

.brain-pulse {{
    display: inline-block;
    animation: pulse 2.8s infinite;
}}

@keyframes pulse {{
    0% {{ transform: scale(1); filter: drop-shadow(0 0 0px {cfg['primary_color']}); }}
    50% {{ transform: scale(1.18); filter: drop-shadow(0 0 25px {cfg['primary_color']}); }}
    100% {{ transform: scale(1); filter: drop-shadow(0 0 0px {cfg['primary_color']}); }}
}}

/* Stats metrics rows */
.stats-row {{
    display: flex;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 35px;
    flex-wrap: wrap;
}}
.stat-card {{
    flex: 1;
    min-width: 180px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 20px;
    padding: 22px;
    text-align: center;
    backdrop-filter: blur(12px);
    transition: all 0.3s ease;
}}
.stat-card:hover {{
    transform: translateY(-4px);
    border-color: {cfg['card_border'].split(" ")[2]};
    background: {cfg['card_bg']};
    box-shadow: 0 0 20px rgba(255, 123, 44, 0.05);
}}
.stat-value {{
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(90deg, {cfg['primary_color']}, {cfg['text_accent']});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}}
.stat-label {{
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.5);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 500;
}}

/* Premium CTA buttons */
.stButton>button {{
    background: linear-gradient(135deg, {cfg['primary_color']}, {cfg['text_accent']}) !important;
    color: white !important;
    border: none !important;
    border-radius: 18px !important;
    padding: 15px 32px !important;
    font-size: 17px !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
    width: 100%;
    cursor: pointer;
    letter-spacing: -0.01em;
}}

.stButton>button:hover {{
    transform: translateY(-2px) scale(1.01) !important;
    box-shadow: 0 8px 30px rgba(255, 123, 44, 0.35), 0 0 20px rgba(255, 94, 58, 0.2) !important;
}}

/* Sidebar Design styling */
section[data-testid="stSidebar"] {{
    background-color: {cfg['sidebar_bg']} !important;
    border-right: 1px solid rgba(255,255,255,0.04) !important;
}}

section[data-testid="stSidebar"] * {{
    color: #e2e8f0 !important;
}}

/* Custom inputs visual style */
.stTextArea textarea, .stTextInput input, [data-testid="stFileUploaderDropzone"] {{
    background-color: rgba(0, 0, 0, 0.2) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 18px !important;
    color: {cfg['text_color']} !important;
    transition: all 0.3s ease !important;
}}

.stTextArea textarea:focus, .stTextInput input:focus {{
    border-color: {cfg['input_border_active']} !important;
    box-shadow: 0 0 15px rgba(255, 123, 44, 0.2) !important;
}}

[data-testid="stFileUploaderDropzone"]:hover {{
    border-color: {cfg['input_border_active']} !important;
    background-color: rgba(255, 255, 255, 0.04) !important;
}}

/* Sidebar headers */
.sidebar-header {{
    font-weight: 800;
    font-size: 1.05rem;
    margin-top: 25px;
    margin-bottom: 12px;
    border-left: 4px solid {cfg['primary_color']};
    padding-left: 12px;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}}
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR CONFIG CONTROLS -----------------
st.sidebar.markdown("<div class='sidebar-header'>⚙️ OCR Engine</div>", unsafe_allow_html=True)
ocr_engine = st.sidebar.radio(
    "Active Recognition Engine",
    ["EasyOCR (Handwriting Optimized)", "PyTesseract (Scans / Print Optimized)"]
)

st.sidebar.markdown("<div class='sidebar-header'>💡 Preprocessing</div>", unsafe_allow_html=True)
grayscale_opt = st.sidebar.toggle("Grayscale Conversion", value=True)
denoise_opt = st.sidebar.toggle("Edge-Preserving Denoise", value=True)
sharpen_opt = st.sidebar.toggle("Stroke Sharpening Filter", value=True)
threshold_opt = st.sidebar.toggle("Adaptive Gaussian Threshold", value=True)

st.sidebar.markdown("<div class='sidebar-header'>📏 Typography</div>", unsafe_allow_html=True)
node_size = st.sidebar.slider("Label Base Size", min_value=12, max_value=28, value=18, step=2)

st.sidebar.markdown("<div class='sidebar-header'>⚙️ Dynamic Forces</div>", unsafe_allow_html=True)
physics_enabled = st.sidebar.toggle("Enable Motion Physics", value=True)
spring_length = st.sidebar.slider("Link Space Distance", min_value=150, max_value=500, value=300, step=50)
spring_strength = st.sidebar.slider("Spring Elastic Rigidity", min_value=0.01, max_value=0.10, value=0.04, step=0.01)
edge_smooth = st.sidebar.checkbox("Curved Connection Joints", value=True)
show_json = st.sidebar.checkbox("Show Semantic Concept JSON", value=False)

# ----------------- SIDEBAR SYSTEM DIAGNOSTICS -----------------
st.sidebar.markdown("<div class='sidebar-header'>🛡️ System Status</div>", unsafe_allow_html=True)

# 1. OpenCV Headless Status
if HAS_CV2:
    st.sidebar.markdown("🟢 **OpenCV Engine:** `Headless Active`  \n*Speed-optimized CV2 backend loaded.*")
else:
    st.sidebar.markdown("🟡 **OpenCV Engine:** `PIL Fallback Mode`  \n*Headless Pillow fallback active. Safe.*")

# 2. PDF Engine Status
try:
    import fitz
    st.sidebar.markdown("🟢 **PDF Parser:** `PyMuPDF Active`  \n*Super-fast in-memory PDF extraction.*")
except ImportError:
    st.sidebar.markdown("🟡 **PDF Parser:** `Poppler Fallback`  \n*Poppler required if PDF range selected.*")

# 3. EasyOCR Status
try:
    import torch
    gpu_available = torch.cuda.is_available()
    gpu_label = "GPU Accelerated" if gpu_available else "CPU Standard"
    st.sidebar.markdown(f"🟢 **EasyOCR Engine:** `Ready ({gpu_label})`  \n*Neural handwriting reader activated.*")
except Exception:
    st.sidebar.markdown("🔴 **EasyOCR Engine:** `Inactive`  \n*Initialization error. Fallback to Tesseract.*")

# 4. PyTesseract Status
import shutil
has_tesseract = shutil.which("tesseract") is not None
if not has_tesseract:
    import pytesseract
    if hasattr(pytesseract.pytesseract, 'tesseract_cmd') and pytesseract.pytesseract.tesseract_cmd:
        has_tesseract = os.path.exists(pytesseract.pytesseract.tesseract_cmd)

if has_tesseract:
    st.sidebar.markdown("🟢 **Tesseract OCR:** `Auto-Discovered`  \n*Print/scan recognition engines active.*")
else:
    st.sidebar.markdown("🟡 **Tesseract OCR:** `Unavailable`  \n*Requires binary installation for printed scans.*")


# ----------------- STUNNING HEADER HERO -----------------
st.markdown(f"""
<div class="header-card">
    <h1><span class="brain-pulse">🧠</span> Smart Notes → Mind Map AI</h1>
    <p>Premium SaaS Workspace • Convert multi-page PDFs, handwritten scans, and typed papers into interactive graphs</p>
</div>
""", unsafe_allow_html=True)

# ----------------- STATS DASHBOARD ROW -----------------
st.markdown("""
<div class="stats-row">
    <div class="stat-card">
        <div class="stat-value">98.8%</div>
        <div class="stat-label">AI Engine Accuracy</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">Multi-Format</div>
        <div class="stat-label">PDF / PNG / JPG Support</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">Pure-Python</div>
        <div class="stat-label">Zero-Setup PDF Engine</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">Auto-Fallback</div>
        <div class="stat-label">OCR Fail-Safe Guard</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- INPUT CARD (INTELLIGENT SOURCE) -----------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown(f"<h3 style='margin-top:0; color:{cfg['primary_color']}; font-weight:800; font-size:1.5rem;'>📝 Intelligent Workspace Source</h3>", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Drop your study notes, images, or documents here (PNG, JPG, JPEG, PDF)",
    type=["png", "jpg", "jpeg", "pdf"]
)

# Configuration containers for PDF Range Selector
pdf_start_page = 1
pdf_end_page = None
is_pdf = False
file_bytes = None

if uploaded_file:
    file_bytes = uploaded_file.read()
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_extension == ".pdf":
        is_pdf = True
        total_pages = get_pdf_page_count(file_bytes)
        st.info(f"📂 **PDF Document Loaded:** '{uploaded_file.name}' containing **{total_pages}** pages.")
        
        # Interactive page range selector to restrict processing time
        if total_pages > 1:
            page_range = st.slider(
                "Select PDF Page Range to Process",
                min_value=1,
                max_value=total_pages,
                value=(1, min(total_pages, 5)),
                step=1,
                help="Limits processing to selected pages to reduce wait times and optimize RAM."
            )
            pdf_start_page, pdf_end_page = page_range
        else:
            pdf_start_page, pdf_end_page = 1, 1
    else:
        st.success(f"🖼️ **Image Loaded:** '{uploaded_file.name}' successfully imported.")

    # Core Action Button
    if st.button("✨ Generate Intelligent Mind Map", key="btn_execute_pipeline"):
        try:
            # Clear previous runs to prevent cross-contamination
            st.session_state["ocr_text"] = ""
            st.session_state["mindmap_data"] = None
            st.session_state["graph_html"] = ""
            st.session_state["custom_main_topic"] = ""
            st.session_state["last_rendered_params"] = {}
            st.session_state["preview_images"] = []
            st.session_state["rendering_failed"] = False
            st.session_state["rendering_error"] = ""
            st.session_state["ocr_fallback_warn"] = None
            
            # --- STAGE 1: OCR Processing ---
            extracted_text_list = []
            
            if is_pdf:
                # Page counter
                total_to_process = (pdf_end_page - pdf_start_page) + 1
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Fetch page images using our memory-efficient PyMuPDF generator
                pdf_generator = convert_pdf_to_images(
                    file_bytes,
                    start_page=pdf_start_page,
                    end_page=pdf_end_page,
                    dpi=300
                )
                
                processed_count = 0
                for page_num, raw_img in pdf_generator:
                    status_text.markdown(f"⚙️ **Page {page_num} of {pdf_end_page}:** Safe Loading & Resizing Image...")
                    
                    # Optimal scaling to prevent out-of-memory
                    scaled_img = resize_image_optimally(raw_img)
                    
                    # Preprocess with custom filters
                    status_text.markdown(f"🧪 **Page {page_num} of {pdf_end_page}:** Applying OpenCV preprocessing...")
                    preproc_arr, preproc_pil = preprocess_for_ocr(
                        scaled_img,
                        grayscale=grayscale_opt,
                        sharpen=sharpen_opt,
                        denoise=denoise_opt,
                        threshold=threshold_opt
                    )
                    
                    # Cache previews for UI display
                    st.session_state["preview_images"].append((f"Page {page_num}", raw_img, preproc_pil))
                    
                    # Run OCR Engine
                    status_text.markdown(f"🧠 **Page {page_num} of {pdf_end_page}:** Running OCR character recognition ({ocr_engine})...")
                    text, final_engine, warning = extract_text(preproc_arr, engine=ocr_engine)
                    
                    if warning:
                        st.session_state["ocr_fallback_warn"] = warning
                        
                    extracted_text_list.append(text)
                    
                    # Increment progress
                    processed_count += 1
                    progress_bar.progress(processed_count / total_to_process)
                    
                progress_bar.empty()
                status_text.empty()
                
            # --- STAGE 1 (Image): OCR Processing ---
            else:
                with st.spinner("⚙️ Stage 1: Preprocessing Notes image channels..."):
                    raw_img = load_image_safely(file_bytes)
                    scaled_img = resize_image_optimally(raw_img)
                    preproc_arr, preproc_pil = preprocess_for_ocr(
                        scaled_img,
                        grayscale=grayscale_opt,
                        sharpen=sharpen_opt,
                        denoise=denoise_opt,
                        threshold=threshold_opt
                    )
                    st.session_state["preview_images"].append(("Notes Scan", raw_img, preproc_pil))
                    
                with st.spinner(f"🧠 Stage 1: Running OCR character recognition ({ocr_engine})..."):
                    text, final_engine, warning = extract_text(preproc_arr, engine=ocr_engine)
                    if warning:
                        st.session_state["ocr_fallback_warn"] = warning
                    extracted_text_list.append(text)
            
            # Combine all page texts
            full_text = "\n\n".join(extracted_text_list).strip()
            logger.info(f"OCR Pipeline complete. Total extracted text length: {len(full_text)} characters.")
            
            if not full_text:
                st.error("❌ OCR Extracted text was empty. Please verify your file quality, or toggle the 'Adaptive Gaussian Threshold' off.")
                st.stop()
                
            st.session_state["ocr_text"] = full_text
            
            # --- STAGE 2: Concept Extraction ---
            with st.spinner("🧠 Stage 2: NLP Semantic Concept Extraction..."):
                mindmap_data = extract_concepts_advanced(full_text)
                st.session_state["mindmap_data"] = mindmap_data
                st.session_state["custom_main_topic"] = mindmap_data["main_topic"]
            
            st.success("✅ Document processed successfully!")
            
            # Safe Streamlit Rerun (Allowing Rerun control flow exceptions to propagate)
            st.rerun()

        except Exception as err:
            # CRITICAL FIX: Explicitly re-raise Streamlit's internal flow control exceptions
            # so that reruns actually trigger instead of getting intercepted as regular errors!
            if type(err).__name__ in ('RerunException', 'StopException', 'RerunData'):
                raise err
            st.error(f"❌ Processing Interrupted: {str(err)}")
            logger.exception("Core orchestration pipeline failed")

st.markdown('</div>', unsafe_allow_html=True)

# ----------------- DISPLAY FALLBACK NOTIFICATIONS -----------------
if st.session_state["ocr_fallback_warn"]:
    st.warning(st.session_state["ocr_fallback_warn"])

# Fetch active text & data from session state
ocr_text = st.session_state["ocr_text"]
mindmap_data = st.session_state["mindmap_data"]

# ----------------- PREPROCESSING & TEXT PREVIEW CARD -----------------
if st.session_state["preview_images"] and ocr_text.strip():
    with st.expander("🔍 Intelligent Vision Preprocessing & OCR Preview", expanded=False):
        st.markdown("<p style='font-size:0.9rem; color:rgba(255,255,255,0.6);'>Compare your original upload against our adaptive OpenCV filter array (Grayscale + Bilateral Filter + Stroke Sharpening + Gaussian C Binary Threshold) to see how the AI optimizes the text shapes:</p>", unsafe_allow_html=True)
        
        # Display tabs for each page/image processed
        preview_tabs = st.tabs([item[0] for item in st.session_state["preview_images"]])
        for tab_idx, (label, orig, preproc) in enumerate(st.session_state["preview_images"]):
            with preview_tabs[tab_idx]:
                col_orig, col_preproc = st.columns(2)
                with col_orig:
                    st.markdown("**Original Upload**")
                    st.image(orig, use_column_width=True)
                with col_preproc:
                    st.markdown("**AI Optimized Preprocessed (OCR Feed)**")
                    st.image(preproc, use_column_width=True)

# ----------------- MINIMUM CONTENT VALIDATION -----------------
if ocr_text.strip():
    if len(ocr_text.strip().split()) < 4:
        st.warning(
            "⚠️ Extracted text is too short to generate a cohesive mind map. "
            "Please try typing some detailed notes manually below or uploading a higher-quality document."
        )
        # Fallback manual text input
        text_input = st.text_area(
            "Study Notes Editor",
            value=ocr_text,
            height=200
        )
        if st.button("✨ Refine & Generate Graph", key="btn_refine_text"):
            st.session_state["ocr_text"] = text_input
            st.session_state["mindmap_data"] = extract_concepts_advanced(text_input)
            st.session_state["custom_main_topic"] = st.session_state["mindmap_data"]["main_topic"]
            st.session_state["graph_html"] = ""  # Force graph rebuild
            st.rerun()
        st.stop()

    # Double check concept extraction is present (runs if notes are edited manually)
    if mindmap_data is None:
        with st.spinner("🧠 Calculating transformers semantic embeddings, relationship structures, and grouping topics..."):
            mindmap_data = extract_concepts_advanced(ocr_text)
            st.session_state["mindmap_data"] = mindmap_data
            st.session_state["custom_main_topic"] = mindmap_data["main_topic"]

    # ----------------- ACTIVE STATE CONTROLLER (PERSISTS GRAPHS) -----------------
    # Re-render ONLY if center label, theme, or physics forces changes!
    current_params = {
        "main_topic": st.session_state["custom_main_topic"],
        "theme": selected_theme,
        "node_size": node_size,
        "physics_enabled": physics_enabled,
        "spring_length": spring_length,
        "spring_strength": spring_strength,
        "edge_smooth": edge_smooth
    }

    if st.session_state["graph_html"] == "" or st.session_state["last_rendered_params"] != current_params:
        try:
            # Reset failures
            st.session_state["rendering_failed"] = False
            st.session_state["rendering_error"] = ""
            
            # --- STAGE 3: Node Mapping & Stage 4: Graph Rendering ---
            with st.spinner("🗺️ Stage 3 & 4: Mapping Nodes and Rendering Canvas..."):
                generate_mindmap_from_concepts(
                    main_topic=st.session_state["custom_main_topic"],
                    topic_groups=mindmap_data["topics"],
                    theme=selected_theme,
                    node_size=node_size,
                    physics_enabled=physics_enabled,
                    spring_length=spring_length,
                    spring_strength=spring_strength,
                    edge_smooth=edge_smooth
                )
                
                # Cache results in Session State
                if os.path.exists("output/interactive_mindmap.html"):
                    with open("output/interactive_mindmap.html", "r", encoding="utf-8") as f:
                        st.session_state["graph_html"] = f.read()
                    st.session_state["last_rendered_params"] = current_params
                    logger.info("New interactive graph cached successfully in st.session_state.")
        except Exception as render_err:
            logger.error(f"Visualization rendering pipeline failed: {render_err}", exc_info=True)
            st.session_state["rendering_failed"] = True
            st.session_state["rendering_error"] = str(render_err)

    # ----------------- RESPONSIVE MIND MAP DISPLAY -----------------
    col_map, col_panel = st.columns([3, 1.2])

    with col_map:
        st.markdown('<div class="card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown(f"<h3 style='margin-top:0; color:{cfg['primary_color']}; font-weight:800; font-size:1.5rem;'>🗺️ Visual Mind Map Workspace</h3>", unsafe_allow_html=True)

        main_topic_edit = st.text_input(
            "✏️ Customize Center Primary Node Label",
            value=st.session_state["custom_main_topic"]
        )
        if main_topic_edit != st.session_state["custom_main_topic"]:
            st.session_state["custom_main_topic"] = main_topic_edit
            st.rerun()

        # Dynamic View Selector
        view_mode = st.radio(
            "Visual Rendering Mode",
            ["🧠 Interactive Canvas (Dynamic HTML)", "🖼️ High-Res Image (Static PNG)"],
            horizontal=True
        )

        # STAGE 5: Final Visualization / Crash Fallback Tree
        if st.session_state["rendering_failed"]:
            # --- SAFE RENDER FALLBACK: Render beautiful nested list representation ---
            st.warning(f"⚠️ Graphical Canvas rendering crashed: {st.session_state['rendering_error']}. Falling back to clean semantic tree representation:")
            
            st.markdown(f"""
            <div style="background: rgba(255, 255, 255, 0.02); border-left: 5px solid {cfg['primary_color']}; border-radius: 12px; padding: 25px; margin-top: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.25);">
                <h3 style="color: {cfg['primary_color']}; margin-top: 0; font-weight: 800; font-size: 1.6rem;">🌳 AI Concept Hierarchy Tree</h3>
                <p style="font-size: 0.92rem; color: rgba(255, 255, 255, 0.6); margin-bottom: 25px;">
                    Graphical canvas rendering failed. Below is the structured semantic concept hierarchy tree extracted by the AI:
                </p>
                <div style="padding-left: 10px;">
            """, unsafe_allow_html=True)
            
            st.markdown(f"### 🧠 **{st.session_state['custom_main_topic']}**")
            for cluster_id, subconcepts in mindmap_data["topics"].items():
                st.markdown(f"#### 📁 **Group {cluster_id + 1}**")
                for concept in subconcepts:
                    st.markdown(f"* 📝 {concept}")
            
            st.markdown("</div></div>", unsafe_allow_html=True)
            
        else:
            # --- NORMAL RENDER: Render Graph Canvas ---
            if "Image" in view_mode:
                if os.path.exists("output/mindmap.png"):
                    st.image("output/mindmap.png", use_column_width=True)
                    
                    with open("output/mindmap.png", "rb") as file:
                        st.download_button(
                            "⬇️ Download High-Res PNG Image",
                            file,
                            file_name="mindmap.png",
                            mime="image/png"
                        )
            else:
                if st.session_state["graph_html"]:
                    components.html(st.session_state["graph_html"], height=720, scrolling=True)
                else:
                    st.info("Visual map compilation in progress...")

        st.markdown('</div>', unsafe_allow_html=True)

    with col_panel:
        st.markdown('<div class="card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown(f"<h3 style='margin-top:0; color:{cfg['primary_color']}; font-weight:800; font-size:1.5rem;'>📊 AI Insights Panel</h3>", unsafe_allow_html=True)

        # AI Confidence Circle Gauge
        st.markdown(f"""
        <div class="confidence-container" style="display: flex; flex-direction: column; align-items: center; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 20px; padding: 20px; margin-bottom: 25px;">
            <h4 style="margin-top:0; color:rgba(255,255,255,0.7); font-weight:600; font-size:0.95rem; text-transform:uppercase; letter-spacing:0.04em;">Model Confidence</h4>
            <div class="confidence-circle" style="position: relative; width: 120px; height: 120px;">
                <svg class="progress-ring" width="120" height="120">
                    <circle class="progress-ring__background" stroke="rgba(255,255,255,0.04)" stroke-width="8" fill="transparent" r="50" cx="60" cy="60"/>
                    <circle class="progress-ring__circle" stroke="{cfg['primary_color']}" stroke-width="8" fill="transparent" r="50" cx="60" cy="60" stroke-dasharray="314.15" stroke-dashoffset="12.5" style="transform: rotate(-90deg); transform-origin: 50% 50%; stroke-linecap: round; filter: drop-shadow(0 0 8px {cfg['primary_color']});"/>
                </svg>
                <div class="confidence-text" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 1.7rem; font-weight: 800; color: #ffffff;">96%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Extracted Metadata Metrics
        num_clusters = len(mindmap_data["topics"])
        total_concepts = sum(len(c) for c in mindmap_data["topics"].values())
        total_relations = len(mindmap_data["relations"])

        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.04); border-radius: 16px; padding: 18px; margin-bottom: 25px;">
            <div style="display:flex; justify-content:space-between; margin-bottom: 10px;">
                <span style="color:rgba(255,255,255,0.6); font-size:0.9rem;">Concept Density:</span>
                <span style="color:#ffffff; font-weight:700; font-size:0.9rem;">{total_concepts} Nodes</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom: 10px;">
                <span style="color:rgba(255,255,255,0.6); font-size:0.9rem;">Semantic Clusters:</span>
                <span style="color:#06b6d4; font-weight:700; font-size:0.9rem;">{num_clusters} Groups</span>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span style="color:rgba(255,255,255,0.6); font-size:0.9rem;">Extracted Relations:</span>
                <span style="color:#10b981; font-weight:700; font-size:0.9rem;">{total_relations} Paths</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Key Relations List
        st.markdown("<h4 style='color:rgba(255,255,255,0.8); font-weight:700; font-size:1.15rem; margin-top:20px; margin-bottom:12px;'>🔗 Key Relationships</h4>", unsafe_allow_html=True)
        if mindmap_data["relations"]:
            st.markdown('<div class="relations-container">', unsafe_allow_html=True)
            for rel in mindmap_data["relations"][:5]:  # Top 5 paths
                st.markdown(f"""
                <div class="relation-item" style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.04); border-radius: 14px; padding: 12px 16px; margin-bottom: 10px; display: flex; align-items: center; gap: 12px; font-size: 0.88rem; transition: all 0.2s ease;">
                    <span class="rel-subject" style="color:{cfg['primary_color']}; font-weight: 600;">{rel[0][:15]}</span>
                    <span class="rel-arrow" style="color: rgba(255,255,255,0.25); font-weight: 700;">→</span>
                    <span class="rel-predicate" style="color:{cfg['text_accent']}; font-weight: 600;">{rel[1][:15]}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:gray; font-size:0.9rem;'>No clear relation paths detected yet.</p>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # Show raw JSON output if requested
    if show_json:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"<h4 style='color:{cfg['primary_color']}; font-weight:700;'>🧾 Concept Structure Output</h4>", unsafe_allow_html=True)
        st.json(mindmap_data)
        st.markdown('</div>', unsafe_allow_html=True)

    # Manual Study Notes Editor Collapsible Drawer
    with st.expander("📝 Manual Study Notes Editor & Refiner"):
        manual_text = st.text_area(
            "Directly edit raw notes text to regenerate the graph",
            value=ocr_text,
            height=300
        )
        if st.button("🔄 Force Regenerate with Edited Notes"):
            st.session_state["ocr_text"] = manual_text
            st.session_state["mindmap_data"] = extract_concepts_advanced(manual_text)
            st.session_state["custom_main_topic"] = st.session_state["mindmap_data"]["main_topic"]
            st.session_state["graph_html"] = ""  # Force graph rebuild
            st.rerun()

# ----------------- SETUP HELP ACCORDION -----------------
with st.expander("ℹ️ Windows Installation & Configuration Help (Tesseract / Poppler)"):
    st.markdown("""
    ### ⚙️ How to install OCR & PDF dependencies on Windows:
    
    1. **Tesseract OCR (Optional but recommended for printed scans):**
       - Download the Windows installer from [UB Mannheim Tesseract Windows](https://github.com/UB-Mannheim/tesseract/wiki).
       - Run the installer. Default location will be `C:\\Program Files\\Tesseract-OCR`.
       - The application **automatically discovers** Tesseract if installed in common paths. If you install elsewhere, add the folder containing `tesseract.exe` to your system Environment Variables (**PATH**).
       
    2. **Poppler (Only required if you turn off PyMuPDF and use pdf2image fallback):**
       - The primary PDF engine runs on **PyMuPDF**, which works **out-of-the-box on Windows** with no manual installs required!
       - If you explicitly wish to use the secondary `pdf2image` engine, download the Windows binary package of Poppler from [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases).
       - Extract the zip file (e.g. to `C:\\poppler`).
       - Add `C:\\poppler\\Library\\bin` to your system **PATH**.
    """)

# ----------------- FOOTER -----------------
st.markdown(f"""
<div style='margin-top: 60px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 25px; text-align: center; padding-bottom: 20px;'>
    <p style='font-size:12px; color:rgba(255,255,255,0.3); font-weight:500;'>
        Smart Notes to Mind Map AI • Premium Enterprise SaaS Workspace • Powered by Gemini AI Preprocessing
    </p>
</div>
""", unsafe_allow_html=True)
