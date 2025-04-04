import os
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import Config

class PDFService:
    def __init__(self):
        self.upload_folder = Config.UPLOAD_FOLDER
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def save_pdf(self, file, filename):
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
        
        file_path = os.path.join(self.upload_folder, filename)
        file.save(file_path)
        return file_path
    
    def extract_text(self, file_path):
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def chunk_text(self, text, chunk_size=1000, chunk_overlap=200):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        chunks = text_splitter.split_text(text)
        return chunks
    
    def extract_and_chunk(self, file_path):
        text = self.extract_text(file_path)
        if text:
            return self.chunk_text(text)
        return []