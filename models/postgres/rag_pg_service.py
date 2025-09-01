from models.postgres.pg_connection import Session, engine, Base
from models.postgres.pg_models import Document
from src.services.embeddingService import embedding_model
from sqlalchemy import text, Index
from sqlalchemy.exc import SQLAlchemyError
import numpy as np
import uuid
import time
from langchain_openai import OpenAIEmbeddings
from config import Config
apikey = Config.OPENAI_API_KEY

class pg_function:
    def __init__(self) -> None:
        """Initialize with SQLAlchemy session"""
        self.session = Session()
        self.engine = engine

        try:
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
            print("pgvector extension enabled successfully!")
        except SQLAlchemyError as e:
            print(f"Warning: Could not enable pgvector extension: {e}")
            print("Make sure pgvector is installed on your PostgreSQL server")

    def __del__(self):
        """Clean up session on destruction"""
        if hasattr(self, 'session'):
            self.session.close()

    def delete_table(self):
        """Delete table - documents using SQLAlchemy"""
        try:
            Document.__table__.drop(self.engine, checkfirst=True)
            print("Table 'documents' deleted successfully!")
        except SQLAlchemyError as e:
            print(f"Error deleting table: {e}")
            raise

    def create_table(self, size=None):
        """Create table documents using SQLAlchemy"""
        try:
            Base.metadata.create_all(self.engine)
            print("\n    Table created successfully!!!")
        except SQLAlchemyError as e:
            print(f"Error creating table: {e}")
            raise

    def create_normal_index(self):
        """Create normal index on org_id using SQLAlchemy"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_documents_org_id ON documents(org_id);"))
                conn.commit()
            print("\n    Indexing done on org_id")
        except SQLAlchemyError as e:
            print(f"Error creating index: {e}")
            raise

    def create_vector_index(self, type="ivfflat"):
        """Create vector index with ivfflat indexing as default"""
        try:
            with self.engine.connect() as conn:
                if type == "hnsw":
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_documents_embedding_hnsw ON documents 
                        USING hnsw (embedding vector_cosine_ops) 
                        WITH (m = 16, ef_construction = 64);
                    """))
                elif type == "ivfflat":
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_documents_embedding_ivfflat ON documents 
                        USING ivfflat (embedding vector_cosine_ops) 
                        WITH (lists = 100);
                    """))
                conn.commit()
            print("     Vector indexing done !!!")
        except SQLAlchemyError as e:
            print(f"Error creating vector index: {e}")
            raise

    def store_in_db(self, pdf_chunks, embeddings):
        """Store documents in database using SQLAlchemy ORM"""
        try:
            documents = []
            for chunk, embedding in zip(pdf_chunks, embeddings):
                
                # Convert numpy array to list if needed
                if isinstance(embedding, np.ndarray):
                    embedding_list = embedding[0].tolist()
                else:
                    embedding_list = embedding[0]
                
                document = Document(
                    content=chunk['content'],
                    org_id=chunk['org_id'],
                    chunk_index=chunk['chunk_index'],
                    embedding=embedding_list
                )
                documents.append(document)
            
            # Bulk insert for better performance
            self.session.bulk_save_objects(documents)
            self.session.commit()
            print("     Stored the data successfully!!!")
            
        except SQLAlchemyError as e:
            self.session.rollback()
            print(f"Error storing documents: {e}")
            raise

    def search_in_db(self, namespace, query, doc_id, limit=3):
        """Search in database using SQLAlchemy with vector similarity"""
        try:
            # Convert query into a vector
            start_time = time.time()

            #embed query
            query_vector = OpenAIEmbeddings(api_key=apikey).embed_query(query)
            search_duration = time.time()-start_time
            print(f"Query embedding completed in {search_duration:.3f}s")

            # Convert numpy array to list if needed
            if isinstance(query_vector, np.ndarray):
                query_vector_list = query_vector.tolist()
            else:
                query_vector_list = query_vector

            # Use raw SQL for vector operations
            query = text("""
                SELECT 
                    id, content, org_id, chunk_index,
                    1 - (embedding <=> CAST(:query_vector AS vector)) AS similarity
                FROM documents
                WHERE org_id = :namespace
                ORDER BY embedding <=> CAST(:query_vector AS vector)
                LIMIT :limit
            """)
            
            start_time = time.time()

            #execute search in db            
            result = self.session.execute(query, {
                'query_vector': str(query_vector_list),
                'namespace': namespace,
                'limit': limit
            })
            search_duration = time.time()-start_time
            print(f"PostgreSQL search completed in {search_duration:.3f}s")
            
            results = result.fetchall()
            return results
            
        except SQLAlchemyError as e:
            print(f"Error searching documents: {e}")
            return []