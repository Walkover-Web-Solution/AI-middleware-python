#!/usr/bin/env python3
"""
PgVector Setup Script
This script sets up the pgvector extension and creates the necessary tables for RAG functionality.
Run this script once to initialize PgVector support in your PostgreSQL database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from models.postgres.pg_connection import engine, Base
from models.postgres.pg_models import RagDocument, RagChunk

def setup_pgvector():
    """Set up PgVector extension and create RAG tables"""
    try:
        with engine.connect() as conn:
            # Enable pgvector extension
            print("Enabling pgvector extension...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            print("✓ PgVector extension enabled successfully")
            
            # Create all tables
            print("Creating RAG tables...")
            Base.metadata.create_all(engine)
            print("✓ RAG tables created successfully")
            
            # Create indexes for better performance
            print("Creating performance indexes...")
            
            # Index for similarity search on embeddings (single table)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rag_vector_store_embedding_cosine 
                ON rag_vector_store USING ivfflat (embedding vector_cosine_ops) 
                WITH (lists = 100);
            """))
            
            # Index for filtering by namespace and doc_id
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rag_vector_store_namespace_doc 
                ON rag_vector_store (namespace, doc_id);
            """))
            
            # Index for org queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_rag_vector_store_org_id 
                ON rag_vector_store (org_id);
            """))
            
            conn.commit()
            print("✓ Performance indexes created successfully")
            
        print("\n🎉 PgVector setup completed successfully!")
        print("\nYou can now use the following API endpoints:")
        print("- POST /rag/pgvector - Create vectors and store documents")
        print("- POST /rag/pgvector/query - Query documents using similarity search")
        print("- GET /rag/pgvector/docs - Get all documents")
        print("- DELETE /rag/pgvector/docs - Delete documents")
        
    except Exception as error:
        print(f"❌ Error setting up PgVector: {error}")
        raise

def check_pgvector_status():
    """Check if PgVector is properly set up"""
    try:
        with engine.connect() as conn:
            # Check if pgvector extension exists
            result = conn.execute(text("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                );
            """)).fetchone()
            
            if result[0]:
                print("✓ PgVector extension is installed")
            else:
                print("❌ PgVector extension is not installed")
                return False
            
            # Check if tables exist
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'rag_documents'
                );
            """)).fetchone()
            
            if result[0]:
                print("✓ RAG tables exist")
            else:
                print("❌ RAG tables do not exist")
                return False
                
            print("✅ PgVector is properly set up and ready to use!")
            return True
            
    except Exception as error:
        print(f"❌ Error checking PgVector status: {error}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PgVector Setup Script")
    parser.add_argument("--check", action="store_true", help="Check PgVector status")
    parser.add_argument("--setup", action="store_true", help="Set up PgVector")
    
    args = parser.parse_args()
    
    if args.check:
        check_pgvector_status()
    elif args.setup:
        setup_pgvector()
    else:
        print("Usage:")
        print("  python setup_pgvector.py --setup   # Set up PgVector")
        print("  python setup_pgvector.py --check   # Check PgVector status")
