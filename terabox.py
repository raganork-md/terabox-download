import re
import os
import time
import asyncio
import aiohttp
import aiofiles
from urllib.parse import urlparse, parse_qs

class TeraboxDownloader:
    def __init__(self):
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
        
        # API endpoints for different methods
        self.api_endpoints = [
            "https://teraboxvideodownloader.nepcoderdevs.workers.dev/?url=",
            "https://terabox.hnn.workers.dev/api/get-info?data=",
            "https://tera.instavideosave.com/?url=",
            "https://teraabox.vercel.app/api?url=",
            "https://terabox-dl.vercel.app/api?url=",
        ]
    
    async def create_session(self):
        """Create aiohttp session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=300)
            connector = aiohttp.TCPConnector(limit=10, force_close=True)
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout,
                connector=connector
            )
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def extract_surl(self, url):
        """Extract surl from Terabox URL"""
        patterns = [
            r"/s/([a-zA-Z0-9_-]+)",
            r"surl=([a-zA-Z0-9_-]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def get_file_info(self, url):
        """Get file information from Terabox URL"""
        session = await self.create_session()
        
        # Try each API endpoint
        for api in self.api_endpoints:
            try:
                api_url = f"{api}{url}"
                
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse response based on API format
                        file_info = self.parse_api_response(data)
                        if file_info:
                            return file_info
                            
            except Exception as e:
                continue
        
        # If all APIs fail, try direct scraping
        return await self.scrape_file_info(url)
    
    def parse_api_response(self, data):
        """Parse API response to extract file info"""
        try:
            # Different API response formats
            if isinstance(data, dict):
                # Format 1: Direct response
                if "file_name" in data or "filename" in data:
                    return {
                        "file_name": data.get("file_name") or data.get("filename") or data.get("name", "unknown"),
                        "file_size": int(data.get("file_size") or data.get("size") or data.get("sizebytes", 0)),
                        "download_url": data.get("download_url") or data.get("downloadLink") or data.get("link", ""),
                    }
                
                # Format 2: Nested in 'data' key
                if "data" in data:
                    inner = data["data"]
                    if isinstance(inner, dict):
                        return {
                            "file_name": inner.get("file_name") or inner.get("filename", "unknown"),
                            "file_size": int(inner.get("file_size") or inner.get("size", 0)),
                            "download_url": inner.get("download_url") or inner.get("downloadLink", ""),
                        }
                    elif isinstance(inner, list) and len(inner) > 0:
                        first = inner[0]
                        return {
                            "file_name": first.get("file_name") or first.get("filename", "unknown"),
                            "file_size": int(first.get("file_size") or first.get("size", 0)),
                            "download_url": first.get("download_url") or first.get("downloadLink", ""),
                        }
                
                # Format 3: Response in 'response' key
                if "response" in data:
                    resp = data["response"]
                    if isinstance(resp, list) and len(resp) > 0:
                        first = resp[0]
                        return {
                            "file_name": first.get("file_name") or first.get("title", "unknown"),
                            "file_size": int(first.get("size", 0)),
                            "download_url": first.get("resolutions", {}).get("HD Video") or first.get("downloadLink", ""),
                        }
                
                # Format 4: Direct with different keys
                if "downloadLink" in data or "link" in data:
                    return {
                        "file_name": data.get("title") or data.get("name", "unknown"),
                        "file_size": int(data.get("size", 0)),
                        "download_url": data.get("downloadLink") or data.get("link", ""),
                    }
                    
        except Exception as e:
            pass
        
        return None
    
    async def scrape_file_info(self, url):
        """Scrape file info directly from Terabox page"""
        session = await self.create_session()
        
        try:
            async with session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                
                # Extract file name
                name_match = re.search(r'"server_filename":"([^"]+)"', html)
                file_name = name_match.group(1) if name_match else "unknown_file"
                
                # Extract file size
                size_match = re.search(r'"size":(\d+)', html)
                file_size = int(size_match.group(1)) if size_match else 0
                
                # Extract download link
                dlink_match = re.search(r'"dlink":"([^"]+)"', html)
                download_url = ""
                if dlink_match:
                    download_url = dlink_match.group(1).replace("\\", "")
                
                if download_url:
                    return {
                        "file_name": file_name,
                        "file_size": file_size,
                        "download_url": download_url,
                    }
                    
        except Exception as e:
            pass
        
        return None
    
    async def download_file(self, url, file_name, status_msg=None, start_time=None):
        """Download file from URL"""
        session = await self.create_session()
        
        # Clean filename
        file_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)
        file_path = f"downloads/{file_name}"
        
        # Create downloads directory
        os.makedirs("downloads", exist_ok=True)
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 1024 * 1024  # 1MB chunks
                
                async with aiofiles.open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        await f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress
                        if status_msg and total_size > 0:
                            try:
                                percentage = downloaded * 100 / total_size
                                filled = int(percentage / 5)
                                bar = "█" * filled + "░" * (20 - filled)
                                
                                elapsed = time.time() - start_time
                                speed = downloaded / elapsed if elapsed > 0 else 0
                                eta = (total_size - downloaded) / speed if speed > 0 else 0
                                
                                size_names = ["B", "KB", "MB", "GB"]
                                
                                def fmt_size(b):
                                    i = 0
                                    while b >= 1024 and i < len(size_names) - 1:
                                        b /= 1024
                                        i += 1
                                    return f"{b:.2f} {size_names[i]}"
                                
                                text = f"""
⬇️ **Downloading...**

📁 **File:** `{file_name}`
📊 **Progress:** [{bar}] {percentage:.1f}%
📦 **Size:** {fmt_size(downloaded)} / {fmt_size(total_size)}
⚡ **Speed:** {fmt_size(speed)}/s
⏱ **ETA:** {int(eta)}s
"""
                                await status_msg.edit_text(text)
                            except Exception:
                                pass
                
                return file_path
                
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            return None
    
    async def __aenter__(self):
        await self.create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()
