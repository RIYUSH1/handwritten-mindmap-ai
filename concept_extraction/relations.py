import logging
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Relations")

# Global NLP engine cache
_nlp = None

def get_spacy_nlp():
    """
    Lazy-loads and caches the spaCy language model.
    If the model is not found in the environment, it automatically downloads it on the fly.
    """
    global _nlp
    if _nlp is None:
        try:
            import spacy
            logger.info("Attempting to load spaCy model 'en_core_web_sm'...")
            _nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model 'en_core_web_sm' loaded successfully.")
        except ImportError:
            logger.error("spaCy is not installed in the current environment.")
            raise RuntimeError("spaCy package is missing from runtime dependencies.")
        except Exception as e:
            logger.warning(f"spaCy model 'en_core_web_sm' not found ({e}). Attempting automatic download on-demand...")
            try:
                import spacy.cli
                spacy.cli.download("en_core_web_sm")
                # Reload model
                _nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy model 'en_core_web_sm' downloaded and loaded successfully.")
            except Exception as download_err:
                logger.error(f"Failed to download spaCy model programmatically: {download_err}")
                # We will trigger the fallback pipeline instead of raising an error
                _nlp = None
    return _nlp


def fallback_relations_extractor(text) -> list:
    """
    Emergency rule-based relationship extractor if spaCy is missing or fails to load.
    Splits text, identifies potential concept words, and extracts basic associations.
    """
    logger.info("Executing rule-based fallback relationship extractor...")
    relations = []
    try:
        # Split text into simple sentences
        sentences = re.split(r"[.!?\n]", text)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 15:
                continue
            
            # Simple keyword associations: e.g. "X is Y", "X includes Y", "X defines Y"
            connectors = [
                r"\bis\b", r"\bare\b", r"\bincludes\b", r"\bcontains\b", 
                r"\bdefines\b", r"\brequires\b", r"\buses\b", r"\bcreates\b", r"\bcauses\b"
            ]
            
            for conn in connectors:
                match = re.split(conn, sentence, maxsplit=1, flags=re.IGNORECASE)
                if len(match) == 2:
                    sub = match[0].strip().strip("*,-\"\'")
                    obj = match[1].strip().strip("*,-\"\'")
                    # Clean words and take first few words
                    sub_words = " ".join(sub.split()[-3:])  # last 3 words of subject
                    obj_words = " ".join(obj.split()[:3])   # first 3 words of object
                    if len(sub_words) > 3 and len(obj_words) > 3:
                        relations.append((sub_words.title(), obj_words.title()))
                        
        logger.info(f"Fallback extracted {len(relations)} associations.")
    except Exception as fallback_err:
        logger.error(f"Fallback relationship extraction failed: {fallback_err}")
        
    return relations


def extract_relationships(text) -> list:
    """
    Extracts semantic relations from text.
    Primary: spaCy dependency parsing (nsubj, dobj, pobj).
    Secondary/Fallback: Custom pattern-matching heuristics.
    """
    if not text:
        return []

    try:
        nlp = get_spacy_nlp()
        if nlp is None:
            return fallback_relations_extractor(text)
            
        doc = nlp(text)
        relations = []

        for token in doc:
            # Check subject, direct object, or prepositional object relations
            if token.dep_ in ("nsubj", "dobj", "pobj"):
                # Capitalize for clean node names in mindmap
                subj = token.head.text.title()
                obj = token.text.title()
                if len(subj) > 2 and len(obj) > 2:
                    relations.append((subj, obj))

        return relations
    except Exception as e:
        logger.warning(f"Primary spaCy relation extraction failed: {e}. Switching to rule-based fallback...")
        return fallback_relations_extractor(text)
