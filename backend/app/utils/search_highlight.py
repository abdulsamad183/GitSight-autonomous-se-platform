import html
import re


def sanitize_headline(text: str) -> str:
    """Allow only highlight tags from PostgreSQL ts_headline."""
    if not text:
        return ""
    result = text.replace("<b>", "<mark>").replace("</b>", "</mark>")
    # Escape everything then restore mark tags
    result = html.escape(result)
    result = result.replace("&lt;mark&gt;", "<mark>").replace("&lt;/mark&gt;", "</mark>")
    return result


def build_content_snippet(content: str, query: str, max_len: int = 400) -> str:
    if not content:
        return ""
    lowered = content.lower()
    query_lower = query.lower().strip()
    pos = lowered.find(query_lower) if query_lower else -1
    if pos == -1:
        for term in query.split():
            pos = lowered.find(term.lower())
            if pos != -1:
                break
    if pos == -1:
        snippet = content[:max_len]
    else:
        start = max(0, pos - max_len // 3)
        end = min(len(content), start + max_len)
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
    return highlight_terms(snippet, query)


def highlight_terms(text: str, query: str) -> str:
    if not query.strip():
        return html.escape(text)
    result = html.escape(text)
    for term in sorted(set(query.split()), key=len, reverse=True):
        if len(term) < 2:
            continue
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        result = pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", result)
    return result
