"""
MongoDB database module for persisting shortlisting results.
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from typing import Dict, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MongoDB:
    """MongoDB connection and operations for Smart Shortlisting Engine."""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.shortlistings_collection = None
        self.connect()
    
    def connect(self) -> bool:
        """
        Connect to MongoDB using credentials from environment variables.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Get credentials from environment
            username = os.getenv("MONGODB_USERNAME")
            password = os.getenv("MONGODB_PASSWORD")
            cluster = os.getenv("MONGODB_CLUSTER", "cluster0.aofhzxk.mongodb.net")
            
            if not username or not password:
                print("Warning: MongoDB credentials not found in environment variables")
                return False
            
            # Construct connection string
            connection_string = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"
            
            # Connect to MongoDB
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database
            db_name = os.getenv("MONGODB_DATABASE", "smart_shortlisting")
            self.db = self.client[db_name]
            
            # Get collections
            self.shortlistings_collection = self.db["shortlistings"]
            
            print(f"Connected to MongoDB: {db_name}")
            return True
            
        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            return False
    
    def save_shortlisting_result(
        self,
        jd_path: str,
        output: Dict,
        resume_count: int
    ) -> Optional[str]:
        """
        Save shortlisting result to MongoDB.
        
        Args:
            jd_path: Path to JD PDF
            output: Complete output dictionary from pipeline
            resume_count: Number of resumes processed
            
        Returns:
            Inserted document ID, or None if failed
        """
        if not self.shortlistings_collection:
            print("MongoDB not connected, skipping save")
            return None
        
        try:
            document = {
                "jd_path": jd_path,
                "jd_role": output["jd_summary"]["role_title"],
                "jd_experience_level": output["jd_summary"]["experience_level"],
                "required_skills": output["jd_summary"]["required_skills"],
                "nice_to_have_skills": output["jd_summary"]["nice_to_have_skills"],
                "total_candidates": output["metadata"]["total_candidates"],
                "rankings": output["rankings"],
                "top_3_explanations": output["top_3_explanations"],
                "resume_count": resume_count,
                "created_at": datetime.now(),
                "metadata": output["metadata"]
            }
            
            result = self.shortlistings_collection.insert_one(document)
            print(f"Saved shortlisting result with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except PyMongoError as e:
            print(f"Error saving to MongoDB: {e}")
            return None
    
    def get_shortlisting_by_id(self, shortlisting_id: str) -> Optional[Dict]:
        """
        Retrieve a shortlisting result by ID.
        
        Args:
            shortlisting_id: MongoDB document ID
            
        Returns:
            Document dictionary, or None if not found
        """
        if not self.shortlistings_collection:
            return None
        
        try:
            from bson.objectid import ObjectId
            document = self.shortlistings_collection.find_one({"_id": ObjectId(shortlisting_id)})
            
            if document:
                # Convert ObjectId to string for JSON serialization
                document["_id"] = str(document["_id"])
                return document
            
            return None
            
        except PyMongoError as e:
            print(f"Error retrieving from MongoDB: {e}")
            return None
    
    def get_all_shortlistings(self, limit: int = 10) -> List[Dict]:
        """
        Retrieve all shortlisting results, sorted by creation date.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of document dictionaries
        """
        if not self.shortlistings_collection:
            return []
        
        try:
            cursor = self.shortlistings_collection.find().sort("created_at", -1).limit(limit)
            results = []
            
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                results.append(doc)
            
            return results
            
        except PyMongoError as e:
            print(f"Error retrieving from MongoDB: {e}")
            return []
    
    def get_shortlistings_by_role(self, role: str) -> List[Dict]:
        """
        Retrieve shortlisting results for a specific role.
        
        Args:
            role: Job role title to search for
            
        Returns:
            List of document dictionaries
        """
        if not self.shortlistings_collection:
            return []
        
        try:
            cursor = self.shortlistings_collection.find(
                {"jd_role": {"$regex": role, "$options": "i"}}
            ).sort("created_at", -1)
            
            results = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                results.append(doc)
            
            return results
            
        except PyMongoError as e:
            print(f"Error retrieving from MongoDB: {e}")
            return []
    
    def delete_shortlisting(self, shortlisting_id: str) -> bool:
        """
        Delete a shortlisting result by ID.
        
        Args:
            shortlisting_id: MongoDB document ID
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.shortlistings_collection:
            return False
        
        try:
            from bson.objectid import ObjectId
            result = self.shortlistings_collection.delete_one({"_id": ObjectId(shortlisting_id)})
            return result.deleted_count > 0
            
        except PyMongoError as e:
            print(f"Error deleting from MongoDB: {e}")
            return False
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")
