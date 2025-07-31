import chromadb

client = chromadb.PersistentClient(path="./chroma_db")  

# List all collections
collections = client.list_collections()
print("Collections:", collections)

# Get a specific collection
collection = client.get_collection("documents")

# Check collection info (e.g. metadata)
print("Collection info:", collection.get())

# Get collection metadata if available
print("Collection metadata:", collection.metadata)

'''
& C:/Users/dell/Desktop/projects/health-bot/.venv/Scripts/python.exe c:/Users/dell/Desktop/projects/health-bot/check_config.py
-bot/check_config.py                                                            Collections: [Collection(name=documents)]
Collection info: {'ids': ['doc_0', 'doc_1', 'doc_2', 'doc_3', 'doc_4'], 'embeddings': None, 'documents': [...], 'uris': None, 'included': ['metadatas', 'documents'], 'data': None, 'metadatas': [None, None, None, None, None]}                                                   Collection metadata: None

'''

# Results
# {'ids': [['doc_7', 'doc_11']], 'embeddings': None, 'documents': [['Cardio vs. Strength Training: What’s Best for You?. Both cardio and strength training have benefits. Cardio improves heart health and burns calories, while strength training builds muscle and boosts metabolism. A balanced routine includes both types of exercise.', 'HIIT Workouts to Burn Fat Fast. High-Intensity Interval Training (HIIT) alternates short bursts of intense activity like sprinting or burpees with low-intensity recovery periods. A typical session lasts 20–30 minutes. HIIT raises your metabolism for hours after exercise.']], 'uris': None, 'included': ['metadatas', 'documents', 'distances'], 'data': None, 'metadatas': [[None, None]], 'distances': [[0.8457728624343872, 0.8472914695739746]]}