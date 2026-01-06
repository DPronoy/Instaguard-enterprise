from analyzer import HybridAnalyzer

print("🧪 Testing Brain...")
engine = HybridAnalyzer()

# Test 1: Blacklist
print(f"Test 1 (Blacklist): {engine.scan('You are a vote chor')}")

# Test 2: AI Model
print(f"Test 2 (AI Model): {engine.scan('I hate you, you are absolutely useless and disgusting')}")