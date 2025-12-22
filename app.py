import streamlit as st
import streamlit.components.v1 as components
from ocr import extract_text
from text_processing import clean_text, extract_keywords, detect_main_topic
from mindmap import generate_mindmap
import os

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Smart Notes to Mind Map",
    page_icon="🧠",
    layout="wide"
)

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
/* App background */
.stApp {
    background: linear-gradient(to right, #f8fbff, #eef3ff);
}

/* Header */
.header-card {
    background: linear-gradient(135deg, #4B8BBE, #306998);
    padding: 30px;
    border-radius: 18px;
    color: white;
    text-align: center;
    margin-bottom: 25px;
}

/* Cards */
.card {
    background-color: white;
    padding: 25px;
    border-radius: 18px;
    box-shadow: 0px 10px 25px rgba(0,0,0,0.06);
    margin-bottom: 25px;
}

/* Buttons */
.stButton>button {
    background-color: #4B8BBE;
    color: white;
    border-radius: 12px;
    padding: 0.6em 1.3em;
    font-size: 16px;
}

/* Inputs */
.stTextInput>div>div>input,
.stTextArea textarea {
    border-radius: 10px;
}

/* Black sidebar */
section[data-testid="stSidebar"] {
    background-color: #0f172a;
}
section[data-testid="stSidebar"] * {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
<div class="header-card">
    <h1>🧠 Smart Notes to Mind Map</h1>
    <p>AI-powered conversion of handwritten or typed notes into structured mind maps</p>
</div>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ Controls")

input_mode = st.sidebar.radio(
    "📥 Input Method",
    ["🖼️ Handwritten Image", "⌨️ Typed Text"]
)

max_nodes = st.sidebar.slider(
    "🔢 Max Mind Map Nodes",
    min_value=5,
    max_value=20,
    value=10
)

show_text = st.sidebar.checkbox("📄 Show Extracted Text", value=True)

view_mode = st.sidebar.radio(
    "🧭 Mind Map View",
    ["🖼️ Static Image", "🧠 Interactive"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ About Project")
st.sidebar.markdown(
    "This AI system converts handwritten or typed notes into **structured mind maps** using OCR and NLP."
)

raw_text = ""

# ---------------- INPUT SECTION ----------------
st.markdown('<div class="card">', unsafe_allow_html=True)

if input_mode == "🖼️ Handwritten Image":
    uploaded_file = st.file_uploader(
        "📤 Upload Handwritten Notes Image",
        type=["jpg", "png", "jpeg"]
    )

    if uploaded_file:
        st.image(uploaded_file, use_column_width=True)

        os.makedirs("images", exist_ok=True)
        image_path = "images/temp.jpg"

        with open(image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if st.button("✨ Generate Mind Map"):
            with st.spinner("🔍 Extracting text from image..."):
                raw_text = extract_text(image_path)

else:
    raw_text = st.text_area(
        "✍️ Paste your notes here",
        height=220,
        placeholder="Enter or paste your study notes here..."
    )

    if st.button("✨ Generate Mind Map"):
        if not raw_text.strip():
            st.warning("Please enter some text first.")

st.markdown('</div>', unsafe_allow_html=True)

# ---------------- PROCESS PIPELINE ----------------
if raw_text.strip():

    os.makedirs("output", exist_ok=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)

    cleaned = clean_text(raw_text)
    keywords = extract_keywords(cleaned)[:max_nodes]
    detected_topic = detect_main_topic(cleaned, keywords)

    main_topic = st.text_input(
        "✏️ Edit Main Topic (Optional)",
        value=detected_topic
    )

    # 🔥 Generates BOTH PNG + Interactive HTML
    generate_mindmap(keywords, main_topic)

    st.success("🎉 Mind Map Generated Successfully")

    st.subheader("🎯 Final Main Topic")
    st.info(main_topic)

    if show_text:
        st.subheader("📄 Processed Text")
        st.text_area("", cleaned, height=140)

    st.subheader("🗺️ Generated Mind Map")

    if view_mode == "🖼️ Static Image":
        if os.path.exists("output/mindmap.png"):
            st.image("output/mindmap.png", use_column_width=True)

            with open("output/mindmap.png", "rb") as file:
                st.download_button(
                    "⬇️ Download PNG",
                    file,
                    file_name="mindmap.png",
                    mime="image/png"
                )

    else:
        if os.path.exists("output/interactive_mindmap.html"):
            with open("output/interactive_mindmap.html", "r", encoding="utf-8") as f:
                html = f.read()
            components.html(html, height=650, scrolling=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- FOOTER ----------------
st.markdown("""
<p style='text-align:center; font-size:13px; color:gray;'>
Resume-Ready AI Project • Interactive Visualization Enabled
</p>
""", unsafe_allow_html=True)
