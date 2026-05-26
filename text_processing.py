import re

# 🔥 AI modules
from concept_extraction.embeddings import get_embeddings
from concept_extraction.topic_modeling import group_topics
from concept_extraction.relations import extract_relationships


# -------------------------------------------------
# CLEAN TEXT (OCR POST-PROCESSING)
# -------------------------------------------------
def clean_text(text):
    """
    Cleans OCR or typed text:
    - normalize spaces
    - preserve sentence boundaries
    """
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


# -------------------------------------------------
# SPLIT INTO LINES (FOR HANDWRITTEN / BULLETS)
# -------------------------------------------------
def split_lines(text):
    return [line.strip() for line in text.split("\n") if len(line.strip()) > 3]


# -------------------------------------------------
# SPLIT INTO SENTENCES (FOR PARAGRAPHS)
# -------------------------------------------------
def split_sentences(text):
    sentences = re.split(r"[.!?]", text)
    return [s.strip() for s in sentences if len(s.strip()) > 15]


# -------------------------------------------------
# 🔥 ADVANCED CONCEPT EXTRACTION (FINAL MERGED VERSION)
# -------------------------------------------------
def extract_concepts_advanced(text):
    """
    Unified concept understanding pipeline:
    ✔ Supports handwritten notes
    ✔ Supports paragraph-style academic text
    ✔ Safe main-topic detection
    ✔ Semantic clustering
    """

    # ---------- STEP 1: CLEAN ----------
    text = clean_text(text)

    if not text:
        return {
            "main_topic": "Unknown Topic",
            "topics": {},
            "relations": []
        }

    # ---------- STEP 2: TRY LINE-BASED FIRST ----------
    lines = split_lines(text)

    # Heuristic: if many short lines → handwritten notes
    use_lines = len(lines) >= 3 and all(len(l.split()) <= 8 for l in lines[:3])

    if use_lines:
        units = lines
    else:
        units = split_sentences(text)

    if not units:
        return {
            "main_topic": "Unknown Topic",
            "topics": {},
            "relations": []
        }

    # ---------- STEP 3: MAIN TOPIC ----------
    main_topic = units[0][:60].title()

    # ---------- STEP 4: SUBTOPICS ----------
    subtopics = units[1:]

    # Fallback: if still too few
    if len(subtopics) < 2:
        subtopics = units

    # Normalize subtopics
    subtopics = list(dict.fromkeys([s.title() for s in subtopics]))

    # ---------- STEP 5: EMBEDDINGS ----------
    embeddings = get_embeddings(subtopics)

    # ---------- STEP 6: CLUSTERING ----------
    k = min(4, len(subtopics))
    topic_groups = group_topics(embeddings, subtopics, k=k)

    # ---------- STEP 7: RELATION EXTRACTION ----------
    relations = extract_relationships(text)

    # ---------- FINAL OUTPUT ----------
    return {
        "main_topic": main_topic,
        "topics": topic_groups,
        "relations": relations
    }
