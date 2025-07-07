import json
import os
from datetime import datetime

import requests


class CloudStorage:
    """Simple cloud storage for PDF receipts using free services"""
    
    def __init__(self):
        self.config_file = "cloud_storage_config.json"
        self.load_config()
    
    def load_config(self):
        """Load cloud storage configuration"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                self.create_default_config()
        else:
            self.create_default_config()
    
    def create_default_config(self):
        """Create default configuration"""
        self.config = {
            "enabled": False,
            "service": "local",  # local, imgur, or custom
            "api_key": "",
            "upload_url": "",
            "download_base_url": ""
        }
        self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def upload_pdf(self, pdf_path):
        """Upload PDF to cloud storage and return public URL"""
        if not self.config["enabled"]:
            return None, "Cloud storage is disabled"
        
        try:
            if self.config["service"] == "imgur":
                return self._upload_to_imgur(pdf_path)
            elif self.config["service"] == "custom":
                return self._upload_to_custom(pdf_path)
            else:
                return None, "No cloud storage service configured"
        except Exception as e:
            return None, f"Upload failed: {str(e)}"
    
    def _upload_to_imgur(self, pdf_path):
        """Upload to Imgur (free tier)"""
        try:
            # Note: Imgur doesn't support PDF uploads in free tier
            # This is a placeholder for demonstration
            return None, "Imgur free tier doesn't support PDF uploads"
        except Exception as e:
            return None, f"Imgur upload failed: {str(e)}"
    
    def _upload_to_custom(self, pdf_path):
        """Upload to custom service"""
        try:
            if not self.config["upload_url"]:
                return None, "Custom upload URL not configured"
            
            with open(pdf_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(self.config["upload_url"], files=files)
            
            if response.status_code == 200:
                result = response.json()
                file_url = result.get('url') or result.get('link')
                if file_url:
                    return file_url, "Upload successful"
                else:
                    return None, "Upload response doesn't contain file URL"
            else:
                return None, f"Upload failed with status {response.status_code}"
        except Exception as e:
            return None, f"Custom upload failed: {str(e)}"

class LocalFileServer:
    """Simple local file server for development/testing"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.files_dir = os.path.join(os.getcwd(), 'public_files')
        os.makedirs(self.files_dir, exist_ok=True)
    
    def serve_file(self, file_path):
        """Create a local file server for the PDF"""
        try:
            # Copy file to public directory
            filename = os.path.basename(file_path)
            public_path = os.path.join(self.files_dir, filename)
            
            with open(file_path, 'rb') as src, open(public_path, 'wb') as dst:
                dst.write(src.read())
            
            # Return local URL (for development only)
            return f"{self.base_url}/files/{filename}", "File served locally"
        except Exception as e:
            return None, f"Local serving failed: {str(e)}"

def get_pdf_url(pdf_path):
    """Get a publicly accessible URL for the PDF"""
    cloud_storage = CloudStorage()
    
    # Try cloud storage first
    if cloud_storage.config["enabled"]:
        url, message = cloud_storage.upload_pdf(pdf_path)
        if url:
            return url, message
    
    # Fallback: return local path
    return pdf_path, "PDF saved locally (no cloud storage configured)" 