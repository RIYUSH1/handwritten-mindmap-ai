from sklearn.cluster import KMeans

def group_topics(embeddings, sentences, k=2):
    kmeans = KMeans(n_clusters=k, random_state=42)
    labels = kmeans.fit_predict(embeddings)

    topics = {}
    for label, sentence in zip(labels, sentences):
        topics.setdefault(label, []).append(sentence)

    return topics
