from concept_extraction.embeddings import get_embeddings

sentences = ["Process", "Thread", "CPU Scheduling"]

embeddings = get_embeddings(sentences)

print("Embedding shape:", embeddings.shape)
