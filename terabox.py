import aiohttp
import re
import json

class TeraboxDownloader:
    def __init__(self):
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        self.domains = [
            "terabox.com", "teraboxapp.com", "1024tera.com", 
            "freeterabox.com", "mirrobox.com", "nephobox.com",
            "4funbox.com", "terabox.app", "tera.instavideosave.com"
        ]

    def is_valid_url(self, url: str) -> bool:
        return any(domain in url.lower() for domain in self.domains)

    def extract_surl(self, url: str) -> str:
        patterns = [
            r'/s/1([a-zA-Z0-9_-]+)',
            r'/s/([a-zA-Z0-9_-]+)',
            r'surl=1?([a-zA-Z0-9_-]+)',
            r'/sharing/link\?surl=1?([a-zA-Z0-9_-]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    async def get_session(self):
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_info(self, url: str) -> dict:
        try:
            session = await self.get_session()
            
            # Method 1: Direct page scraping
            result = await self._scrape_direct(session, url)
            if result and "error" not in result:
                return result

            # Method 2: Mobile page
            result = await self._scrape_mobile(session, url)
            if result and "error" not in result:
                return result

            # Method 3: API endpoint
            result = await self._try_api(session, url)
            if result and "error" not in result:
                return result

            return {"error": "❌ File info കിട്ടിയില്ല! Link ശരിയാണോ check ചെയ്യുക."}

        except aiohttp.ClientError as e:
            return {"error": f"🌐 Network error: {str(e)}"}
        except Exception as e:
            return {"error": f"⚠️ Error: {str(e)}"}

    async def _scrape_direct(self, session, url: str) -> dict:
        try:
            async with session.get(url, headers=self.headers, allow_redirects=True) as resp:
                if resp.status != 200:
                    return None
                html = await resp.text()
                return self._parse_html(html)
        except:
            return None

    async def _scrape_mobile(self, session, url: str) -> dict:
        try:
            mobile_headers = self.headers.copy()
            mobile_headers["User-Agent"] = "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36"
            
            async with session.get(url, headers=mobile_headers, allow_redirects=True) as resp:
                if resp.status != 200:
                    return None
                html = await resp.text()
                return self._parse_html(html)
        except:
            return None

    async def _try_api(self, session, url: str) -> dict:
        try:
            surl = self.extract_surl(url)
            if not surl:
                return None

            api_url = f"https://www.terabox.com/api/shorturlinfo?shorturl={surl}"
            async with session.get(api_url, headers=self.headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("errno") == 0:
                        file_list = data.get("list", [])
                        if file_list:
                            f = file_list[0]
                            return {
                                "filename": f.get("server_filename", "file"),
                                "size": self.format_size(int(f.get("size", 0))),
                                "download_link": f.get("dlink", ""),
                                "thumb": f.get("thumbs", {}).get("url3", "")
                            }
        except:
            return None

    def _parse_html(self, html: str) -> dict:
        try:
            # Pattern 1: window.__INITIAL_STATE__
            match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.+?\});', html, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                file_info = data.get("file", {}).get("list", [{}])[0]
                if file_info:
                    return {
                        "filename": file_info.get("server_filename", "file"),
                        "size": self.format_size(int(file_info.get("size", 0))),
                        "download_link": file_info.get("dlink", ""),
                        "thumb": file_info.get("thumbs", {}).get("url3", "")
                    }

            # Pattern 2: Direct JSON in page
            patterns = [
                r'"server_filename"\s*:\s*"([^"]+)"',
                r'"filename"\s*:\s*"([^"]+)"',
                r'"file_name"\s*:\s*"([^"]+)"'
            ]
            filename = None
            for p in patterns:
                m = re.search(p, html)
                if m:
                    filename = m.group(1)
                    break

            size_match = re.search(r'"size"\s*:\s*["\']?(\d+)["\']?', html)
            dlink_match = re.search(r'"dlink"\s*:\s*"(https?:[^"]+)"', html)

            if filename and dlink_match:
                return {
                    "filename": filename,
                    "size": self.format_size(int(size_match.group(1))) if size_match else "Unknown",
                    "download_link": dlink_match.group(1).replace("\\", ""),
                    "thumb": ""
                }

            return None
        except:
            return None

    def format_size(self, size: int) -> str:
        if size <= 0:
            return "Unknown"
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        for unit in units:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"
