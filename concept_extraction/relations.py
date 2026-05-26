import spacy

nlp = spacy.load("en_core_web_sm")

def extract_relationships(text):
    doc = nlp(text)
    relations = []

    for token in doc:
        if token.dep_ in ("nsubj", "dobj", "pobj"):
            relations.append((token.head.text, token.text))

    return relations
