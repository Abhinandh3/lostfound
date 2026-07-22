import os
import json

# Lazy imports for ML libraries to avoid loading on every request
_clip_model = None
_clip_processor = None
_faiss_index = None
_embedding_map = {}  # Maps index ID to (case_id, image_id)

MODEL_NAME = "openai/clip-vit-base-patch32"
EMBEDDING_DIM = 512
FAISS_INDEX_PATH = "faiss_index.index"
EMBEDDING_MAP_PATH = "embedding_map.json"


def _get_torch():
    """Lazy load torch."""
    import torch
    return torch


def _get_np():
    """Lazy load numpy."""
    import numpy as np
    return np


def _get_clip():
    """Lazy load CLIP model and processor."""
    global _clip_model, _clip_processor
    if _clip_model is None:
        from transformers import CLIPProcessor, CLIPModel
        print(f"Loading CLIP model: {MODEL_NAME}")
        _clip_model = CLIPModel.from_pretrained(MODEL_NAME)
        _clip_processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    return _clip_model, _clip_processor


def _get_faiss():
    """Lazy load faiss."""
    import faiss
    return faiss


def get_clip_model():
    """Load CLIP model if not already loaded."""
    return _get_clip()


def get_faiss_index():
    """Load FAISS index if exists, otherwise create new one."""
    global _faiss_index
    faiss = _get_faiss()
    if _faiss_index is None:
        if os.path.exists(FAISS_INDEX_PATH):
            print(f"Loading FAISS index from {FAISS_INDEX_PATH}")
            _faiss_index = faiss.read_index(FAISS_INDEX_PATH)
        else:
            print("Creating new FAISS index")
            _faiss_index = faiss.IndexFlatL2(EMBEDDING_DIM)
    return _faiss_index


def load_embedding_map():
    """Load embedding map from disk."""
    global _embedding_map
    if os.path.exists(EMBEDDING_MAP_PATH):
        with open(EMBEDDING_MAP_PATH, 'r') as f:
            _embedding_map = json.load(f)
    return _embedding_map


def save_embedding_map():
    """Save embedding map to disk."""
    with open(EMBEDDING_MAP_PATH, 'w') as f:
        json.dump(_embedding_map, f)


def save_faiss_index():
    """Save FAISS index to disk."""
    faiss = _get_faiss()
    faiss.write_index(get_faiss_index(), FAISS_INDEX_PATH)


def generate_embedding(image_path):
    """Generate CLIP embedding for an image."""
    from PIL import Image
    
    model, processor = get_clip_model()
    torch = _get_torch()
    np = _get_np()
    
    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"Error loading image: {e}")
        return None
    
    inputs = processor(images=image, return_tensors="pt", padding=True)
    
    with torch.no_grad():
        outputs = model.get_image_features(**inputs)
    
    # Normalize the embedding
    embedding = outputs.numpy().flatten()
    embedding = embedding / np.linalg.norm(embedding)
    
    return embedding.tolist()


def add_to_index(image_path, case_id, image_id):
    """Add an image embedding to the FAISS index."""
    np = _get_np()
    
    embedding = generate_embedding(image_path)
    
    if embedding is None:
        return False
    
    index = get_faiss_index()
    embedding_array = np.array([embedding], dtype=np.float32)
    
    # Add to FAISS index
    index.add(embedding_array)
    
    # Update embedding map
    idx = len(_embedding_map)
    _embedding_map[str(idx)] = {"case_id": case_id, "image_id": image_id}
    
    # Save index and map
    save_faiss_index()
    save_embedding_map()
    
    return True


def search_similar_images(query_image_path, top_k=10):
    """Search for similar images using FAISS."""
    np = _get_np()
    
    query_embedding = generate_embedding(query_image_path)
    
    if query_embedding is None:
        return []
    
    index = get_faiss_index()
    query_array = np.array([query_embedding], dtype=np.float32)
    
    # Search in FAISS index
    distances, indices = index.search(query_array, min(top_k, len(_embedding_map)))
    
    results = []
    for i, idx in enumerate(indices[0]):
        if idx < 0 or str(idx) not in _embedding_map:
            continue
        
        distance = distances[0][i]
        # Convert L2 distance to similarity percentage
        # Lower distance = higher similarity
        similarity = max(0, 100 - (distance * 10))
        
        mapping = _embedding_map[str(idx)]
        results.append({
            "case_id": mapping["case_id"],
            "image_id": mapping["image_id"],
            "similarity": round(similarity, 2),
            "distance": round(distance, 4)
        })
    
    return results


def rebuild_index_from_database(cases_with_images):
    """Rebuild FAISS index from database records.
    
    Args:
        cases_with_images: List of tuples (case_id, image_id, image_path)
    """
    global _faiss_index, _embedding_map
    faiss = _get_faiss()
    np = _get_np()
    
    # Reset index and map
    _faiss_index = faiss.IndexFlatL2(EMBEDDING_DIM)
    _embedding_map = {}
    
    embeddings = []
    
    for case_id, image_id, image_path in cases_with_images:
        if os.path.exists(image_path):
            embedding = generate_embedding(image_path)
            if embedding:
                embeddings.append(np.array(embedding, dtype=np.float32))
                idx = len(_embedding_map)
                _embedding_map[str(idx)] = {"case_id": case_id, "image_id": image_id}
    
    if embeddings:
        embeddings_array = np.vstack(embeddings)
        _faiss_index.add(embeddings_array)
        save_faiss_index()
        save_embedding_map()
        print(f"Rebuilt index with {len(embeddings)} embeddings")
    else:
        print("No valid embeddings to rebuild index")
