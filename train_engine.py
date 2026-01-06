import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset
import torch
import os

# CONFIG
MODEL_NAME = "distilbert-base-multilingual-cased"
OUTPUT_DIR = "./engine/model_v1"

def train():
    print(f"Initializing RTX 4060 Training Pipeline...")
    
    # 1. Load the Big Dataset
    if not os.path.exists("data/training_data.csv"):
        print(" Error: data/training_data.csv not found. Run ingest_data.py first.")
        return

    df = pd.read_csv("data/training_data.csv").dropna()
    print(f"📚 Training on {len(df)} examples...")

    # Split: 90% Train, 10% Test
    train_df, val_df = train_test_split(df, test_size=0.1, random_state=42)
    
    # 2. Tokenization
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)
    
    def tokenize(batch):
        # We limit text to 64 tokens to keep it fast on your GPU
        return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=64)
    
    train_ds = Dataset.from_pandas(train_df).map(tokenize, batched=True)
    val_ds = Dataset.from_pandas(val_df).map(tokenize, batched=True)

    # 3. Model Setup
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)
    model.to("cuda") # Force GPU

    # 4. Hyperparameters (RTX 4060 Optimized)

    args = TrainingArguments(
        output_dir="./checkpoints",
        learning_rate=2e-5,
        per_device_train_batch_size=32, 
        gradient_accumulation_steps=1,
        num_train_epochs=3,             
        weight_decay=0.01,
        fp16=True,                      
        logging_steps=100,
        save_strategy="no",             
        eval_strategy="steps",
        eval_steps=500
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
    )

    print("Training Started... (This might take 5-10 minutes)")
    trainer.train()

    # 5. Save the Final Engine
    print(f"Saving High-Performance Model to {OUTPUT_DIR}...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("ENGINE SAVED. The brain is ready.")

if __name__ == "__main__":
    train()