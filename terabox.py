import aiohttp
import re
import json
from urllib.parse import urlparse, parse_qs

class TeraboxDownloader:
    def __init__(self):
        self.domains = [
            "terabox.com", "teraboxapp.com", "terasharelink.com",
            "1024tera.com", "4funbox.com", "mirrobox.com",
            "nephobox.com", "freeterabox.com", "1024terabox.com"
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    def is_valid_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            return any(domain in parsed.netloc for domain in self.domains)
        except:
            return False

    def extract_surl(self, url: str) -> str:
        if "/s/" in url:
            match = re.search(r'/s/([a-zA-Z0-9_-]+)', url)
            if match:
                return match.group(1)
        parsed = parse_qs(urlparse(url).query)
        return parsed.get('surl', [None])[0]

    async def get_file_info(self, url: str) -> dict:
        if not self.is_valid_url(url):
            return {"error": "Invalid Terabox URL"}

        surl = self.extract_surl(url)
        if not surl:
            return {"error": "Could not extract share ID"}

        try:
            # Method 1: Direct API
            api_url = f"https://www.terabox.com/api/shorturlinfo?shorturl={surl}&root=1"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=self.headers, timeout=30) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("errno") == 0:
                            return self._parse_response(data)
                
                # Method 2: Alternative API endpoint
                alt_api = f"https://www.1024tera.com/api/shorturlinfo?shorturl={surl}&root=1"
                async with session.get(alt_api, headers=self.headers, timeout=30) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("errno") == 0:
                            return self._parse_response(data)

                # Method 3: Scrape webpage
                return await self._scrape_method(session, url, surl)

        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}

    async def _scrape_method(self, session, url: str, surl: str) -> dict:
        try:
            async with session.get(url, headers=self.headers, timeout=30, allow_redirects=True) as resp:
                html = await resp.text()
                
                # Find jsToken
                js_token_match = re.search(r'fn%28%22([^%]+)%22%29', html)
                if not js_token_match:
                    js_token_match = re.search(r'jsToken.*?([a-fA-F0-9]{128,})', html)
                
                # Find file data in page
                data_match = re.search(r'locals\.shareData\s*=\s*(\{.*?\});', html, re.DOTALL)
                if data_match:
                    try:
                        share_data = json.loads(data_match.group(1))
                        file_list = share_data.get("file_list", {}).get("list", [])
                        if file_list:
                            return self._parse_file_list(file_list)
                    except:
                        pass

                # Alternative pattern
                pattern = r'"server_filename":"([^"]+)".*?"size":(\d+).*?"dlink":"([^"]+)"'
                matches = re.findall(pattern, html)
                if matches:
                    name, size, dlink = matches[0]
                    return {
                        "filename": name,
                        "size": int(size),
                        "size_str": self._format_size(int(size)),
                        "download_link": dlink.replace("\\", "")
                    }

                return {"error": "File info not found in page"}

        except Exception as e:
            return {"error": f"Scrape failed: {str(e)}"}

    def _parse_response(self, data: dict) -> dict:
        try:
            file_list = data.get("list", [])
            if not file_list:
                return {"error": "Empty file list"}
            
            file_info = file_list[0]
            return {
                "filename": file_info.get("server_filename", "Unknown"),
                "size": file_info.get("size", 0),
                "size_str": self._format_size(file_info.get("size", 0)),
                "download_link": file_info.get("dlink", ""),
                "thumb": file_info.get("thumbs", {}).get("url3", ""),
                "fs_id": file_info.get("fs_id", "")
            }
        except Exception as e:
            return {"error": f"Parse error: {str(e)}"}

    def _parse_file_list(self, file_list: list) -> dict:
        if not file_list:
            return {"error": "Empty file list"}
        
        file_info = file_list[0]
        return {
            "filename": file_info.get("server_filename", "Unknown"),
            "size": file_info.get("size", 0),
            "size_str": self._format_size(file_info.get("size", 0)),
            "download_link": file_info.get("dlink", ""),
            "thumb": file_info.get("thumbs", {}).get("url3", "")
        }

    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

    async def get_download_link(self, url: str) -> dict:
        info = await self.get_file_info(url)
        if "error" in info:
            return info
        
        if not info.get("download_link"):
            return {"error": "Download link not available"}
        
        # Get fast download link
        dlink = info["download_link"]
        
        headers = {
            **self.headers,
            "Referer": "https://www.terabox.com/"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(dlink, headers=headers, allow_redirects=True, timeout=30) as resp:
                    final_url = str(resp.url)
                    info["fast_link"] = final_url
        except:
            info["fast_link"] = dlink
        
        return info
