import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

df = pd.read_csv("ejemplo.csv")
vectorizer = TfidfVectorizer()
classifier = MultinomialNB()
model = make_pipeline(vectorizer, classifier)
model.fit(df["text"], df["category"])
with open("model.ai", "wb") as f:
    pickle.dump(model, f)
    
print(f"✅ Modelo entrenado con {len(df)} registros y guardado como 'model.ai'") 
