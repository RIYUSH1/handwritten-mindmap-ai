import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Embeddings")

# Global cache for the embedding model
_embedding_model = None

def get_sentence_transformer_model():
    """
    Lazy-loads and caches the SentenceTransformer model on demand.
    Avoids loading heavy neural network weights at import time, preventing startup timeouts.
    """
    global _embedding_model
    if _embedding_model is None:
        logger.info("Initializing SentenceTransformer Model (all-MiniLM-L6-v2) on-demand...")
        try:
            from sentence_transformers import SentenceTransformer
            # Load model
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("SentenceTransformer model successfully initialized and cached.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer model: {e}")
            raise RuntimeError(f"❌ AI Embedding Engine failed to initialize. Details: {str(e)}")
    return _embedding_model

def get_embeddings(sentences):
    """
    Generates semantic embeddings for a list of sentences/phrases.
    """
    if not sentences:
        return []
    
    logger.info(f"Generating embeddings for {len(sentences)} text blocks...")
    try:
        model = get_sentence_transformer_model()
        embeddings = model.encode(sentences)
        logger.info("Embeddings successfully generated.")
        return embeddings
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        # Fallback empty embeddings (could cause clustering to fail, but prevents total crash)
        raise RuntimeError(f"❌ Embedding generation failed: {str(e)}")
