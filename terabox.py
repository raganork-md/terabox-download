import aiohttp
import re
import json

class TeraboxDownloader:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.terabox.com/"
        }

    def is_valid_url(self, url: str) -> bool:
        domains = ["terabox", "1024tera", "freeterabox", "mirrobox", "nephobox", "4funbox", "teraboxapp"]
        return any(d in url.lower() for d in domains)

    async def get_info(self, url: str) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=30, allow_redirects=True) as r:
                    html = await r.text()
                    
                    # Extract jsToken
                    js_token = re.search(r'fn%28%22(.+?)%22%29', html)
                    if not js_token:
                        js_token = re.search(r'fn\("(.+?)"\)', html)
                    
                    # Extract file data from page
                    data_match = re.search(r'locals\.fileInfo\s*=\s*(\{.+?\});', html, re.DOTALL)
                    if not data_match:
                        data_match = re.search(r'"file_info":\s*(\{.+?\})', html)
                    
                    if data_match:
                        file_data = json.loads(data_match.group(1))
                        return {
                            "filename": file_data.get("file_name") or file_data.get("server_filename"),
                            "size": self.format_size(int(file_data.get("size", 0))),
                            "download_link": file_data.get("dlink"),
                            "thumb": file_data.get("thumbs", {}).get("url3", "")
                        }

                    # Alternate: find dlink directly
                    dlink = re.search(r'"dlink":"(https[^"]+)"', html)
                    fname = re.search(r'"server_filename":"([^"]+)"', html)
                    fsize = re.search(r'"size":(\d+)', html)
                    
                    if dlink:
                        return {
                            "filename": fname.group(1) if fname else "terabox_file",
                            "size": self.format_size(int(fsize.group(1))) if fsize else "Unknown",
                            "download_link": dlink.group(1).replace("\\", ""),
                            "thumb": ""
                        }

            return {"error": "File info not found - Terabox blocked"}
        except Exception as e:
            return {"error": str(e)}

    def format_size(self, size: int) -> str:
        for u in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {u}"
            size /= 1024
        return f"{size:.2f} TB"
