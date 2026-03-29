import requests
import streamlit as st
from typing import List, Dict

class APIClient:
    """Client for communicating with backend API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def upload_pdfs(self, file_list: List) -> Dict:
        """Upload PDF files to backend"""
        try:
            files = [('files', (file.name, file.getbuffer(), 'application/pdf')) 
                    for file in file_list]
            
            response = requests.post(
                f"{self.base_url}/api/pdf/upload",
                files=files,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Upload failed: {str(e)}")
            return {"error": str(e)}
    
    def list_pdfs(self) -> Dict:
        """Get list of uploaded PDFs"""
        try:
            response = requests.get(
                f"{self.base_url}/api/pdf/list",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Failed to fetch PDFs: {str(e)}")
            return {"pdfs": []}
    
    def extract_text(self, file_id: str) -> Dict:
        """Extract text from PDF"""
        try:
            response = requests.post(
                f"{self.base_url}/api/analyze/extract-text/{file_id}",
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Text extraction failed: {str(e)}")
            return {"error": str(e)}
    
    def clean_text(self, file_id: str) -> Dict:
        """Clean and preprocess text"""
        try:
            response = requests.post(
                f"{self.base_url}/api/analyze/clean-text/{file_id}",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Text cleaning failed: {str(e)}")
            return {"error": str(e)}
    
    def calculate_similarity(self, file_ids: List[str]) -> Dict:
        """Calculate similarity between documents"""
        try:
            response = requests.post(
                f"{self.base_url}/api/analyze/similarity",
                json={"file_ids": file_ids},
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Similarity calculation failed: {str(e)}")
            return {"error": str(e)}
    
    def generate_heatmap(self, file_ids: List[str]) -> Dict:
        """Generate redundancy heatmap"""
        try:
            response = requests.post(
                f"{self.base_url}/api/analyze/redundancy-heatmap",
                json={"file_ids": file_ids},
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Heatmap generation failed: {str(e)}")
            return {"error": str(e)}
    
    def generate_clean_pdf(self, file_ids: List[str]) -> Dict:
        """Generate clean PDF with deduplicated content"""
        try:
            response = requests.post(
                f"{self.base_url}/api/download/clean-pdf",
                json={"file_ids": file_ids},
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Failed to generate clean PDF: {str(e)}")
            return {"error": str(e)}