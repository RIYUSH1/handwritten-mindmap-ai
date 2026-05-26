from concept_extraction.embeddings import get_embeddings
from concept_extraction.topic_modeling import group_topics

sentences = ["Process", "Thread", "CPU Scheduling", "Deadlock"]

embeddings = get_embeddings(sentences)
topics = group_topics(embeddings, sentences, k=2)

print(topics)
