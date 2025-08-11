# from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sentence_transformers import SentenceTransformer
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
prompt_dataset = os.path.join(script_dir, "prompt_dataset.csv")

# Ensure the directory exists for saving models
os.makedirs(script_dir, exist_ok=True)

df = pd.read_csv(prompt_dataset)  
prompts = df["prompt"].tolist()
labels = df["type"].tolist()
x_train,x_test,y_train,y_test = train_test_split(prompts,labels,test_size=0.2,random_state=42)

model_name = "all-MiniLM-L6-v2"
embedder = SentenceTransformer(model_name)

x = embedder.encode(x_train) 
y = y_train

# Train model
model = LGBMClassifier(max_depth=2)
model.fit(x, y)

# Save model using absolute paths
classifier_path = os.path.join(script_dir, "classifier_model.joblib")

joblib.dump(model, classifier_path)

print(model.predict(embedder.encode(["what is a planet"])))
