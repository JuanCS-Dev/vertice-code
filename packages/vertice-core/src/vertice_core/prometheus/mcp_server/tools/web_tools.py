"""
Web Tools for MCP Server
Safe web content retrieval and search tools

This module provides 2 essential web tools with
SSRF protection, rate limiting, and content processing.
"""

import logging
import ipaddress
import urllib.parse
from typing import List, Optional, Dict
import httpx

from .validated import create_validated_tool

logger = logging.getLogger(__name__)


# SSRF Protection (adapted from parity/web_tools.py)
BLOCKED_IP_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),  # Loopback
    ipaddress.ip_network("10.0.0.0/8"),  # RFC 1918 Class A
    ipaddress.ip_network("172.16.0.0/12"),  # RFC 1918 Class B
    ipaddress.ip_network("192.168.0.0/16"),  # RFC 1918 Class C
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local (AWS metadata)
    ipaddress.ip_network("::1/128"),  # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),  # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
]

BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",  # GCP metadata
    "metadata",  # Generic cloud metadata
    "169.254.169.254",  # AWS/GCP/Azure metadata IP
}


def is_ssrf_safe(url: str) -> tuple[bool, Optional[str]]:
    """Check if URL is safe from SSRF attacks."""
    try:
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return False, "Invalid URL: no hostname"

        # Check blocked hostnames (case-insensitive)
        if hostname.lower() in BLOCKED_HOSTNAMES:
            return False, f"SSRF blocked: hostname '{hostname}' is not allowed"

        # Check if hostname is an IP address directly
        try:
            ip = ipaddress.ip_address(hostname)
            for blocked_range in BLOCKED_IP_RANGES:
                if ip in blocked_range:
                    return False, f"SSRF blocked: IP {ip} is in private/internal range"
            return True, None
        except ValueError:
            pass  # Not an IP, continue with DNS resolution

        # DNS resolution check (simplified)
        try:
            import socket

            resolved_ip = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(resolved_ip)
            for blocked_range in BLOCKED_IP_RANGES:
                if ip in blocked_range:
                    return False, f"SSRF blocked: {hostname} resolves to private IP {ip}"
        except Exception as e:
            pass  # DNS resolution failed, allow (might be a valid hostname)

        return True, None

    except Exception as e:
        return False, f"URL validation failed: {str(e)}"


# Simple rate limiter
class RateLimiter:
    """Simple rate limiter."""

    def __init__(self, max_requests: int = 30, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[float] = []

    def is_allowed(self) -> tuple[bool, Optional[str]]:
        """Check if request is allowed."""
        import time

        now = time.time()

        # Clean old requests
        self.requests = [t for t in self.requests if now - t < self.window_seconds]

        if len(self.requests) >= self.max_requests:
            return (
                False,
                f"Rate limit exceeded: {self.max_requests} requests per {self.window_seconds}s",
            )

        self.requests.append(now)
        return True, None


_fetch_rate_limiter = RateLimiter(max_requests=30, window_seconds=60.0)
_search_rate_limiter = RateLimiter(max_requests=10, window_seconds=60.0)


# Tool 1: Fetch URL
async def fetch_url(url: str, max_length: int = 10000, timeout: int = 30) -> dict:
    """Fetch URL content and convert to readable text."""
    # Validate URL
    if not url:
        return {"success": False, "error": "URL is required"}

    if not url.startswith(("http://", "https://")):
        return {"success": False, "error": "URL must start with http:// or https://"}

    # SSRF protection
    is_safe, ssrf_error = is_ssrf_safe(url)
    if not is_safe:
        logger.warning(f"SSRF blocked request to {url}: {ssrf_error}")
        return {"success": False, "error": ssrf_error}

    # Rate limiting
    allowed, rate_error = _fetch_rate_limiter.is_allowed()
    if not allowed:
        logger.warning(f"Rate limit hit for fetch_url: {rate_error}")
        return {"success": False, "error": rate_error}

    # Validate max_length
    if not isinstance(max_length, int) or max_length < 100:
        max_length = 10000
    max_length = min(max_length, 50000)  # Hard limit

    # Upgrade HTTP to HTTPS
    if url.startswith("http://"):
        url = "https://" + url[7:]
        logger.debug(f"Upgraded URL to HTTPS: {url}")

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "MCP-Server/1.0 (Web content retrieval tool)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
        ) as client:
            response = await client.get(url)

            if response.status_code >= 400:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.reason_phrase}",
                }

            # Get content type
            content_type = response.headers.get("content-type", "").lower()

            # Extract text content
            if "text/html" in content_type:
                # Try to extract readable text from HTML
                try:
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(response.text, "html.parser")

                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()

                    # Get text
                    text = soup.get_text(separator="\n", strip=True)

                    # Clean up whitespace
                    lines = [line.strip() for line in text.split("\n") if line.strip()]
                    text = "\n".join(lines)

                except ImportError:
                    text = response.text  # Fallback to raw HTML
            else:
                text = response.text

            # Truncate if needed
            if len(text) > max_length:
                text = text[:max_length] + "\n\n[CONTENT TRUNCATED]"

            return {
                "success": True,
                "content": text,
                "url": str(response.url),  # Final URL after redirects
                "status_code": response.status_code,
                "content_type": content_type,
                "content_length": len(response.content),
                "truncated": len(text) > max_length,
            }

    except httpx.TimeoutException:
        return {"success": False, "error": f"Request timed out after {timeout}s"}
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return {"success": False, "error": str(e)}


# Tool 2: Search Web
async def search_web(
    query: str,
    num_results: int = 5,
    allowed_domains: Optional[List[str]] = None,
    blocked_domains: Optional[List[str]] = None,
) -> dict:
    """Search the web using DuckDuckGo and return results."""
    # Validate query
    if not query:
        return {"success": False, "error": "Query is required"}

    if len(query) < 2:
        return {"success": False, "error": "Query too short (minimum 2 characters)"}

    # Rate limiting
    allowed, rate_error = _search_rate_limiter.is_allowed()
    if not allowed:
        logger.warning(f"Rate limit hit for search_web: {rate_error}")
        return {"success": False, "error": rate_error}

    # Validate num_results
    if not isinstance(num_results, int) or num_results < 1:
        num_results = 5
    num_results = min(num_results, 20)  # Hard limit

    # Validate domain lists
    if allowed_domains is None:
        allowed_domains = []
    if blocked_domains is None:
        blocked_domains = []

    try:
        # Use DuckDuckGo HTML search (no API key needed)
        encoded_query = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        async with httpx.AsyncClient(
            timeout=10, headers={"User-Agent": "MCP-Server/1.0 (Web search tool)"}
        ) as client:
            response = await client.get(url)

            if response.status_code != 200:
                return {"success": False, "error": f"Search failed: HTTP {response.status_code}"}

            html = response.text

            # Parse DuckDuckGo results (simplified)
            results = _parse_ddg_results(html, num_results * 2)  # Get extra for filtering

            # Apply domain filters
            if allowed_domains:
                results = [
                    r for r in results if any(domain in r["url"] for domain in allowed_domains)
                ]

            if blocked_domains:
                results = [
                    r for r in results if not any(domain in r["url"] for domain in blocked_domains)
                ]

            # Limit results
            results = results[:num_results]

            # Format sources section
            sources = []
            for i, result in enumerate(results, 1):
                sources.append(f"[{i}] {result['title']} - {result['url']}")

            sources_markdown = "\n".join(sources) if sources else ""

            return {
                "success": True,
                "query": query,
                "results": results,
                "sources": sources,
                "sources_markdown": sources_markdown,
                "count": len(results),
            }

    except Exception as e:
        logger.error(f"Web search failed for query '{query}': {e}")
        return {"success": False, "error": str(e)}


def _parse_ddg_results(html: str, max_results: int) -> List[Dict[str, str]]:
    """Parse DuckDuckGo HTML results (simplified version)."""
    results = []

    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        # Find result containers
        result_divs = soup.find_all("div", class_="result")[:max_results]

        for div in result_divs:
            try:
                # Extract title and URL
                title_elem = div.find("a", class_="result__a")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url = title_elem.get("href", "")

                # Extract snippet
                snippet_elem = div.find("a", class_="result__snippet")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                if title and url:
                    results.append({"title": title, "url": url, "snippet": snippet})

            except Exception as e:
                continue  # Skip malformed results

    except ImportError:
        logger.warning("BeautifulSoup not available, cannot parse search results")
        return []

    return results


# Create and register all web tools
web_tools = [
    create_validated_tool(
        name="fetch_url",
        description="Fetch URL content and convert to readable text with SSRF protection",
        category="web",
        parameters={
            "url": {"type": "string", "description": "URL to fetch content from", "required": True},
            "max_length": {
                "type": "integer",
                "description": "Maximum content length to return",
                "default": 10000,
                "minimum": 100,
                "maximum": 50000,
            },
            "timeout": {
                "type": "integer",
                "description": "Request timeout in seconds",
                "default": 30,
                "minimum": 5,
                "maximum": 120,
            },
        },
        required_params=["url"],
        execute_func=fetch_url,
    ),
    create_validated_tool(
        name="search_web",
        description="Search the web using DuckDuckGo and return results with citations",
        category="web",
        parameters={
            "query": {"type": "string", "description": "Search query", "required": True},
            "num_results": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 5,
                "minimum": 1,
                "maximum": 20,
            },
            "allowed_domains": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Only include results from these domains",
            },
            "blocked_domains": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Exclude results from these domains",
            },
        },
        required_params=["query"],
        execute_func=search_web,
    ),
]

# Register all tools with the global registry
from .registry import register_tool

for tool in web_tools:
    register_tool(tool)
