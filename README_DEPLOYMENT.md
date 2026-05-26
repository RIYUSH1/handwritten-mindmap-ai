# 🚀 Streamlit Cloud Deployment Instructions

This guide provides step-by-step instructions to successfully deploy the **Handwritten MindMap AI** application to Streamlit Cloud with stable, headless-safe, and memory-optimized operations.

---

## 📂 Deployment Configuration Files

All required files are already configured and pushed to your repository root:
1. **`requirements.txt`**: Standardized dependencies, pinning lightweight, CPU-only PyTorch and replacing graphical OpenCV with `opencv-python-headless`.
2. **`packages.txt`**: Tells Streamlit Cloud to download required Linux system dependencies: Tesseract OCR, Mesa OpenGL graphics libraries, and Poppler utilities.
3. **`runtime.txt`**: Locks Python environment to version `3.12` to match the local Windows environment.

---

## 🛠️ Step-by-Step Streamlit Cloud Deployment

1. **Push Changes to GitHub**:
   Make sure all your latest local commits (including the new `packages.txt`, `runtime.txt`, `requirements.txt`, `image_utils.py`, `app.py`, and `concept_extraction/` changes) are pushed to your GitHub repository.
   ```bash
   git add -A
   git commit -m "Deploy production fix: OpenCV headless, lazy-load AI engines, and PIL fallbacks"
   git push origin main
   ```

2. **Login to Streamlit Share**:
   - Go to [Streamlit Share](https://share.streamlit.io/).
   - Log in using your GitHub account.

3. **Deploy the App**:
   - Click the **"New app"** button.
   - Choose your repository: `RIYUSH1/handwritten-mindmap-ai`.
   - Select your branch: `main`.
   - Set the Main file path: `app.py`.
   - Click **"Deploy"**.

4. **Advanced Settings (Optional - Safe-Guards)**:
   - On the deployment page, click **"Settings"** in the bottom-right corner.
   - Under **"Secrets"**, if you have any sensitive API tokens, add them (not strictly needed for this offline CPU model pipeline).
   - Watch the build console. The initial deployment may take 3-5 minutes as the container installs Linux binary packages (`packages.txt`) and downloads Python libraries (`requirements.txt`).

---

## ⚙️ How it Works Under the Hood

### 1. Headless Safe Preprocessing Fallback
In `image_utils.py`, if OpenCV (`cv2`) fails to import or crashes due to missing graphical libraries inside a server container, the application automatically catches the import error and activates a high-fidelity **PIL/Pillow fallback image processing engine**. 

This fallback matches all critical OpenCV preprocessing steps:
- **Grayscale conversion**: via `Image.convert("L")`
- **Median filter denoising**: via `ImageFilter.MedianFilter` (which preserves edges)
- **High-pass stroke sharpening**: via `ImageFilter.SHARPEN` + custom `ImageEnhance` scale boost (recovers pen/pencil strokes)
- **Local Adaptive Thresholding**: via NumPy-based 15x15 uniform local mean comparison (emulates OpenCV Gaussian Adaptive thresholding)

### 2. Startup & Lazy Loading Optimizations
AI models (Sentence-Transformers and spaCy) are no longer loaded at import time. Instead, they are lazy loaded inside caching decorators only when the user triggers the concept extraction pipeline. 
This prevents Streamlit from timing out or hitting memory bounds during container initialization.

### 3. Automatic Model Recovery
If the spaCy English NLP model (`en_core_web_sm`) is not found, the system downloads it automatically on the fly via `spacy.cli.download("en_core_web_sm")`, removing manual CLI download requirements.

### 4. Interactive Live System Diagnostics
The sidebar displays a live **🛡️ System Status** panel giving you visual green/yellow checkmarks for every critical engine:
- **OpenCV Engine** status (Headless Active vs PIL Fallback)
- **PDF Parser** status (PyMuPDF vs Poppler Fallback)
- **EasyOCR Engine** status (Ready, CPU/GPU detection)
- **Tesseract OCR** status (Auto-Discovered paths)

---

## 💻 Local Windows Execution Check

To verify these changes locally:
1. Double-click `setup.bat` to rebuild the virtual environment using the new light CPU configurations.
2. Double-click `run_app.bat` to launch the workspace locally in your browser.
