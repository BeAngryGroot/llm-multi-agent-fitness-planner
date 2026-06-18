import os
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pymongo import MongoClient
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langsmith import traceable

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("nutrition_search")

nutrition_search = APIRouter()

# Global variables for caching
embeddings_model = None
vector_store_full = None
vector_store_sample = None


class NutritionQuery(BaseModel):
    """Query parameters for nutrition search"""
    query: str = Field(description="Search query")
    dietary_restrictions: List[str] = Field(default_factory=list)
    macro_goals: Dict[str, float] = Field(default_factory=dict)
    limit: int = Field(default=20)
    similarity_threshold: float = Field(default=0.5)
    use_full_database: bool = Field(default=False)


class NutritionResult(BaseModel):
    """Single nutrition search result"""
    fdc_id: str
    description: str
    brand_owner: Optional[str] = None
    brand_name: Optional[str] = None
    food_category: Optional[str] = None
    nutrition_per_100g: Dict[str, float]
    primary_macro_category: str
    is_high_protein: bool
    similarity_score: float


class NutritionSearchResponse(BaseModel):
    """Nutrition search response"""
    query: str
    results: List[NutritionResult]
    total_results: int
    search_time_ms: float


# Helper function for MongoDB connection
def get_mongo_client():
    """Get MongoDB client connection"""
    mongo_user = os.getenv("MONGO_USER")
    mongo_password = os.getenv("MONGO_PASSWORD")

    mongo_port = os.getenv("MONGO_PORT", "27017")
    
    try:
        # Docker internal connection
        mongo_uri = f"mongodb://{mongo_user}:{mongo_password}@mongodb_ai_fitness_planner:27017/admin"
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        return client
    except:
        # Fallback to localhost
        mongo_uri = f"mongodb://{mongo_user}:{mongo_password}@localhost:{mongo_port}/admin"
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        return client


def get_embeddings_model():
    """Initialize HuggingFace embeddings model"""
    global embeddings_model
    if embeddings_model is None:
        embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    return embeddings_model


def get_vector_store(use_full_database: bool = False):
    """Get the appropriate FAISS vector store based on database selection"""
    global vector_store_full, vector_store_sample

    if use_full_database:
        if vector_store_full is None:
            # Try to load full database vector store
            vector_store_path = "./nutrition_faiss_index_full"
            if os.path.exists(vector_store_path):
                embeddings = get_embeddings_model()
                vector_store_full = FAISS.load_local(
                    vector_store_path, embeddings, allow_dangerous_deserialization=True
                )
                logger.info("Loaded full database vector store")
            else:
                logger.warning("Full database vector store not found, using sample")
                return get_vector_store(use_full_database=False)
        return vector_store_full
    else:
        if vector_store_sample is None:
            # Try to load sample database vector store
            vector_store_path = "./nutrition_faiss_index_sample"
            if os.path.exists(vector_store_path):
                embeddings = get_embeddings_model()
                vector_store_sample = FAISS.load_local(
                    vector_store_path, embeddings, allow_dangerous_deserialization=True
                )
                logger.info("Loaded sample database vector store")
            else:
                logger.error("Sample database vector store not found")
                raise FileNotFoundError("Vector store not found. Run setup_database.py first.")
        return vector_store_sample


@nutrition_search.post("/create_vector_index_sample/")
async def create_vector_index_sample():
    """Create vector index for sample nutrition database"""
    try:
        import time
        start_time = time.time()

        # Get MongoDB client
        client = get_mongo_client()
        db = client[os.getenv("MONGO_DB_NAME", "usda_nutrition")]
        collection = db["branded_foods_sample"]

        # Get embeddings model
        embeddings = get_embeddings_model()

        # Prepare documents for vector store
        documents = []
        metadatas = []

        # Get all documents from collection
        cursor = collection.find({"nutrition_enhanced": {"$exists": True}})
        
        for doc in cursor:
            # Create a text representation of the food
            food_text = f"{doc.get('description', '')} {doc.get('brandOwner', '')} {doc.get('foodCategory', '')}"
            documents.append(food_text)
            
            # Add metadata
            metadata = {
                "fdc_id": doc.get('fdcId'),
                "description": doc.get('description'),
                "brand_owner": doc.get('brandOwner'),
                "brand_name": doc.get('brandName'),
                "food_category": doc.get('foodCategory'),
                "nutrition_per_100g": doc.get('nutrition_enhanced', {}).get('per_100g', {}),
                "primary_macro_category": doc.get('nutrition_enhanced', {}).get('macro_breakdown', {}).get('primary_macro_category', 'unknown'),
                "is_high_protein": doc.get('nutrition_enhanced', {}).get('macro_breakdown', {}).get('is_high_protein', False),
            }
            metadatas.append(metadata)

        # Create FAISS vector store
        vector_store = FAISS.from_texts(documents, embeddings, metadatas=metadatas)

        # Save vector store
        vector_store.save_local("./nutrition_faiss_index_sample")

        end_time = time.time()
        logger.info(f"Created sample vector index in {end_time - start_time:.2f} seconds")

        return {
            "message": "Sample vector index created successfully",
            "documents_processed": len(documents),
            "time_taken": f"{end_time - start_time:.2f} seconds"
        }

    except Exception as e:
        logger.error(f"Error creating vector index: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create vector index: {str(e)}")


@nutrition_search.post("/search", response_model=NutritionSearchResponse)
async def search_nutrition_semantic(query: NutritionQuery):
    """Search nutrition database using semantic search"""
    try:
        import time
        start_time = time.time()

        # Get vector store
        vector_store = get_vector_store(use_full_database=query.use_full_database)

        # Perform similarity search
        results = vector_store.similarity_search_with_score(
            query.query,
            k=query.limit,
        )

        # Filter results based on similarity threshold
        filtered_results = []
        for doc, score in results:
            if score >= query.similarity_threshold:
                # Convert FAISS Document to NutritionResult
                metadata = doc.metadata
                result = NutritionResult(
                    fdc_id=metadata.get('fdc_id'),
                    description=metadata.get('description'),
                    brand_owner=metadata.get('brand_owner'),
                    brand_name=metadata.get('brand_name'),
                    food_category=metadata.get('food_category'),
                    nutrition_per_100g=metadata.get('nutrition_per_100g', {}),
                    primary_macro_category=metadata.get('primary_macro_category'),
                    is_high_protein=metadata.get('is_high_protein'),
                    similarity_score=score,
                )
                filtered_results.append(result)

        end_time = time.time()
        search_time_ms = (end_time - start_time) * 1000

        # Log search details
        logger.info(f"Nutrition search completed in {search_time_ms:.2f}ms")
        logger.info(f"Query: {query.query}, Results: {len(filtered_results)}")

        return NutritionSearchResponse(
            query=query.query,
            results=filtered_results,
            total_results=len(filtered_results),
            search_time_ms=search_time_ms,
        )

    except Exception as e:
        logger.error(f"Error in nutrition search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@nutrition_search.get("/categories")
async def get_food_categories():
    """Get all unique food categories"""
    try:
        client = get_mongo_client()
        db = client[os.getenv("MONGO_DB_NAME", "usda_nutrition")]
        collection = db["branded_foods_sample"]

        # Get distinct food categories
        categories = collection.distinct("foodCategory")
        client.close()

        return {
            "categories": categories,
            "count": len(categories)
        }

    except Exception as e:
        logger.error(f"Error getting food categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@nutrition_search.get("/stats")
async def get_nutrition_stats():
    """Get nutrition database statistics"""
    try:
        client = get_mongo_client()
        db = client[os.getenv("MONGO_DB_NAME", "usda_nutrition")]

        # Get counts from both collections
        sample_count = db["branded_foods_sample"].count_documents({})
        full_count = db["branded_foods"].count_documents({})

        client.close()

        return {
            "sample_database_count": sample_count,
            "full_database_count": full_count,
            "total_foods": sample_count + full_count
        }

    except Exception as e:
        logger.error(f"Error getting nutrition stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")