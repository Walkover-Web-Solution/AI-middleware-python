import PyPDF2
import pdfplumber
import os

def process_pdfs(pdf_directory,pdfs):
    """Process all PDFs in the directory"""
    
    pdf_files = pdfs
    
    all_chunks = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_directory, pdf_file)
        if os.path.exists(pdf_path):
            chunks = extract_text_from_pdf(pdf_path)  # Limit pages for demo
            all_chunks.extend(chunks)
    
    return all_chunks

def extract_text_from_pdf(pdf_path, max_pages=100):
    """Extract text from PDF file with chunking"""
    chunks = []
    
    try:
        # Try with pdfplumber first (better text extraction)
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = min(len(pdf.pages), max_pages)
            print(f"  Extracting text from {total_pages} pages...")
            
            for page_num in range(total_pages):
                try:
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    
                    if text and len(text.strip()) > 50:  # Only process pages with substantial text
                        # Split into chunks of ~500 characters
                        sentences = text.split('.')
                        current_chunk = ""
                        
                        for sentence in sentences:
                            if len(current_chunk + sentence) < 500:
                                current_chunk += sentence + "."
                            else:
                                if current_chunk.strip():
                                    chunks.append({
                                        'content': current_chunk.strip(),
                                        'source': os.path.basename(pdf_path),
                                        'page_number': page_num + 1,
                                        'chunk_index': len(chunks)
                                    })
                                current_chunk = sentence + "."
                        
                        # Add the last chunk if it has content
                        if current_chunk.strip():
                            chunks.append({
                                'content': current_chunk.strip(),
                                'source': os.path.basename(pdf_path),
                                'page_number': page_num + 1,
                                'chunk_index': len(chunks)
                            })
                            
                except Exception as e:
                    print(f"  Warning: Could not extract from page {page_num + 1}: {e}")
                    continue
    except Exception as e:
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = min(len(pdf_reader.pages), max_pages)
                
                for page_num in range(total_pages):
                    try:
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        
                        if text and len(text.strip()) > 50:
                            # Simple chunking for PyPDF2
                            words = text.split()
                            chunk_size = 100  # words per chunk
                            
                            for i in range(0, len(words), chunk_size):
                                chunk_words = words[i:i + chunk_size]
                                chunk_text = ' '.join(chunk_words)
                                
                                if len(chunk_text.strip()) > 50:
                                    chunks.append({
                                        'content': chunk_text.strip(),
                                        'source': os.path.basename(pdf_path),
                                        'page_number': page_num + 1,
                                        'chunk_index': len(chunks)
                                    })
                                    
                    except Exception as e:
                        print(f"  Warning: Could not extract from page {page_num + 1}: {e}")
                        continue
                        
        except Exception as e:
            return []
    
    print(f"  Extracted {len(chunks)} chunks from {os.path.basename(pdf_path)}")
    return chunks