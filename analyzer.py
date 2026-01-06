import pandas as pd
import os

class HybridAnalyzer:
    def __init__(self):
        print("Initializing Database Engine...")
        self.toxic_phrases = set()
        self.load_database()

    def load_database(self):
        """Loads english.csv, hindi.csv, hinglish.csv into memory"""
        # Configuration: (Filename, Column Name for Text, Column Name for Label)
        # Adjust these column names if your CSVs are slightly different
        files_config = [
            ("english.csv", "tweet", "class"),
            ("hindi.csv", "text", "label"),
            ("hinglish.csv", "text", "hate_label")
        ]
        
        loaded_count = 0
        raw_path = "raw_data"  # Folder where your CSVs are
        
        if not os.path.exists(raw_path):
            print(f"⚠️ Warning: '{raw_path}' folder not found. Please create it and add your CSVs.")
            return

        for filename, text_col, label_col in files_config:
            path = os.path.join(raw_path, filename)
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path)
                    # Normalize headers
                    df.columns = df.columns.str.strip().str.lower()
                    
                    # Verify columns exist
                    if text_col in df.columns and label_col in df.columns:
                        # Filter: Keep only rows where label is '1', 'toxic', 'yes', etc.
                        # We convert to string to handle mixed types (int/str)
                        bad_rows = df[df[label_col].astype(str).str.lower().isin(['1', 'toxic', 'yes', 'hate', 'offensive'])]
                        
                        # Extract the text, lowercase it, and strip whitespace
                        phrases = bad_rows[text_col].astype(str).str.lower().str.strip().tolist()
                        
                        # Add meaningful phrases (ignore tiny words like "is", "the" to prevent false positives)
                        valid_phrases = [p for p in phrases if len(p) > 3]
                        
                        self.toxic_phrases.update(valid_phrases)
                        loaded_count += len(valid_phrases)
                        print(f"   -> Loaded {len(valid_phrases)} threats from {filename}")
                    else:
                        print(f"   ⚠️ Column mismatch in {filename}. Found: {list(df.columns)}")
                except Exception as e:
                    print(f" Error reading {filename}: {e}")
        
        print(f"✅ Database Ready: {loaded_count} known threats active.")

    def scan(self, text):
        """Checks if the comment contains any phrase from the database"""
        clean_text = text.lower().strip()
        
        # Exact/Partial Match Check
        # We look for your database phrases INSIDE the user comment
        for phrase in self.toxic_phrases:
            if phrase in clean_text:
                return {
                    "is_toxic": True, 
                    "reason": f"Database Match: '{phrase}'", 
                    "score": 1.0
                }
        
        return {"is_toxic": False, "reason": "Safe", "score": 0.0}