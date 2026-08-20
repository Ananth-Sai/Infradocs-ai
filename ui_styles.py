import re
import os
import html

# --- Custom CSS Design System ---
CUSTOM_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

<style>
    /* Complete elimination of top toolbar, deploy button, and hamburger menu */
    header[data-testid="stHeader"],
    .stAppHeader,
    [data-testid="stHeader"],
    #MainMenu,
    footer,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    .stDeployButton {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0px !important;
        min-height: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
        pointer-events: none !important;
    }
    
    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Content Canvas: Deep Obsidian Dark */
    .stApp, [data-testid="stAppViewContainer"], .main {
        background-color: #080c15 !important;
        color: #f1f5f9 !important;
    }
    
    /* Sidebar: Rich Slate Navy with Clear Dividing Border */
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {
        background-color: #111827 !important;
        border-right: 1px solid #1f2937 !important;
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.4) !important;
    }
    
    /* Force entire layout and title to snap cleanly to the top */
    .block-container,
    [data-testid="block-container"],
    [data-testid="stMainBlockContainer"],
    .stMainBlockContainer,
    .main .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        max-width: 96% !important;
    }
    
    /* Header Area */
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        margin-top: 0rem !important;
        padding-top: 0rem !important;
    }
    
    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    
    /* Input Styling */
    .stTextInput > div > div > input {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        font-size: 0.95rem;
        transition: all 0.2s ease-in-out;
    }
    .stTextInput > div > div > input:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.25) !important;
    }
    
    /* Answer Card */
    .glass-answer-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-left: 4px solid #38bdf8;
        border-radius: 12px;
        padding: 22px 26px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        margin-top: 10px;
        margin-bottom: 20px;
        line-height: 1.65;
        font-size: 1rem;
        color: #f8fafc;
    }
    
    /* Status Badges */
    .badge-verified {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.35);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    .badge-refusal {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.35);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    
    /* Metrics Strip */
    .metrics-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 14px;
    }
    .metric-pill {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 4px 10px;
        font-size: 0.78rem;
        color: #94a3b8;
        font-family: 'Fira Code', monospace;
    }
    .metric-pill span {
        color: #38bdf8;
        font-weight: 600;
    }
    
    /* Citation Badges */
    .citation-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: #0f172a;
        color: #38bdf8;
        border: 1px solid #0284c7;
        padding: 3px 9px;
        margin: 2px 4px;
        border-radius: 6px;
        font-size: 0.82rem;
        font-family: 'Fira Code', monospace;
        font-weight: 500;
        text-decoration: none;
    }
    
    /* Chunk Relevance & Strategy Badges */
    .relevance-high {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
    }
    .relevance-mid {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.4);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
    }
    .relevance-low {
        background: rgba(148, 163, 184, 0.15);
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.3);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.72rem;
    }
    .strategy-tag {
        background: rgba(168, 85, 247, 0.15);
        color: #c084fc;
        border: 1px solid rgba(168, 85, 247, 0.35);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-family: 'Fira Code', monospace;
    }
</style>
"""


def format_citation_pills(text: str) -> str:
    """Format [source: filename.md] citations into styled badge pills."""
    def replace_source(match):
        source = match.group(1).strip()
        icon = "📄"
        if "deployment" in source.lower():
            icon = "📘"
        elif "platform" in source.lower():
            icon = "⚙️"
        elif "troubleshoot" in source.lower():
            icon = "❓"
        return f'<span class="citation-badge">{icon} {html.escape(source)}</span>'

    return re.sub(r"\[source:\s*([^\]]+)\]", replace_source, text)


def get_doc_content(filename: str) -> str:
    """Read and format document content from docs/ for the sidebar explorer."""
    from ingest import load_text
    path = os.path.join("docs", filename)
    if os.path.exists(path):
        try:
            return load_text(path)
        except Exception as e:
            return f"Error previewing file: {e}"
    return "Document content unavailable."



def get_relevance_badge(distance: float) -> str:
    """Generate color-coded relevance badge with distance and similarity percentage."""
    similarity_pct = max(0.0, min(100.0, (1.0 - distance) * 100))
    if distance < 0.55:
        return f'<span class="relevance-high">🟢 High Match ({similarity_pct:.1f}% sim | dist: {distance:.3f})</span>'
    elif distance < 0.78:
        return f'<span class="relevance-mid">🟡 Moderate Match ({similarity_pct:.1f}% sim | dist: {distance:.3f})</span>'
    return f'<span class="relevance-low">⚪ Context Match ({similarity_pct:.1f}% sim | dist: {distance:.3f})</span>'
