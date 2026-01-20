import os
import sys
from typing import List

from mcp.server.fastmcp import FastMCP
import uvicorn

# LangChain Imports
from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    Docx2txtLoader,
    PyMuPDFLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# --- Configuration ---
DOCS_DIR = "./docs"
DB_DIR = "./chroma_db"

# Global variable to hold the database connection
vector_store = None

# --- Database Initialization Logic ---

def initialize_vector_db():
    """
    Checks if the Vector DB exists. If not, reads files and builds it.
    """
    global vector_store
    
    # Check if DB directory exists and is not empty
    if not os.path.exists(DB_DIR) or not os.listdir(DB_DIR):
        print("⚡ Building Vector Database from documents... (Using PyMuPDF)")
        
        # 1. Define Loaders for different file types
        loaders = [
            DirectoryLoader(DOCS_DIR, glob="**/*.txt", loader_cls=TextLoader),
            DirectoryLoader(DOCS_DIR, glob="**/*.docx", loader_cls=Docx2txtLoader),
            DirectoryLoader(DOCS_DIR, glob="**/*.pdf", loader_cls=PyMuPDFLoader)
        ]
        
        documents: List[Document] = []
        for loader in loaders:
            try:
                print(f"   - Loading files with {loader.loader_cls.__name__}...")
                new_docs = loader.load()
                documents.extend(new_docs)
            except Exception as e:
                print(f"⚠️ Warning: Issue loading files: {e}")

        if not documents:
            print("⚠️ No documents found in /docs. Policy Search will be empty.")
            return

        print(f"   - Loaded {len(documents)} source pages/files.")

        # 2. Split Text into Chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        print(f"   - Split into {len(chunks)} chunks.")
        
        # 3. Create Vector Store (ChromaDB + OpenAI Embeddings)
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
            persist_directory=DB_DIR
        )
        print(f"✅ Database built successfully in {DB_DIR}")
        
    else:
        print("⚡ Loading existing Vector Database from disk...")
        vector_store = Chroma(
            persist_directory=DB_DIR,
            embedding_function=OpenAIEmbeddings(model="text-embedding-3-small")
        )

# --- MCP Server Setup ---

mcp = FastMCP("Policy Service")

@mcp.tool()
def search_hr_policies(query: str) -> str:
    """
    Searches the HR Policy Documents (PDFs/Word/Txt) for specific rules or information.
    """
    if not vector_store:
        return "Error: Policy Database is not initialized. Please check server logs."

    print(f"🔍 Searching policies for: '{query}'")
    sys.stdout.flush() # Ensure it prints immediately


    # Search for the 5 most relevant chunks
    results = vector_store.similarity_search(query, k=10)
    
    if not results:
        return "No relevant policy information found in the documents."

    # Format the results for the AI
    context_parts = []
    for i, doc in enumerate(results):
        source = doc.metadata.get("source", "Unknown file")
        content = doc.page_content.replace("\n", " ")
        context_parts.append(f"Source {i+1} ({source}):\n{content}")

    final_response = "\n\n---\n\n".join(context_parts)
    print(f"✅ Found {len(results)} results. Returning content length: {len(final_response)}")
    sys.stdout.flush()
    return final_response

if __name__ == "__main__":
    # Initialize Vector DB BEFORE starting server
    print("🚀 Starting Policy Service initialization...")
    sys.stdout.flush()
    try:
        initialize_vector_db()
        print("✅ Vector DB initialized successfully")
    except Exception as e:
        print(f"🔥 CRITICAL ERROR initializing Policy DB: {e}")
    sys.stdout.flush()
    
    print("🌐 Starting Uvicorn server on port 8002...")
    sys.stdout.flush()
    # Runs on Port 8002 - Same pattern as leave/loan services
    uvicorn.run(mcp.sse_app(), host="0.0.0.0", port=8002)