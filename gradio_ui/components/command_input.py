"""Command input component with suggestions."""
import gradio as gr
from typing import Tuple


def create_command_interface() -> Tuple[gr.Textbox, gr.HTML]:
    """
    Create command input with smart suggestions.
    
    Returns:
        Tuple of (input_box, suggestions_html)
    """
    
    # Command input
    command_input = gr.Textbox(
        label="💬 What would you like to do?",
        placeholder="read main.py, refactor legacy code, fix all TODOs...",
        lines=2,
        elem_classes=["command-input"],
        show_label=True
    )
    
    # Smart suggestions
    suggestions = gr.HTML(
        """
        <div style="margin-top: 16px;">
            <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 8px;">💡 Quick Suggestions:</p>
            <div class="suggestion-chip">📖 Read main.py</div>
            <div class="suggestion-chip">🔧 Refactor legacy code</div>
            <div class="suggestion-chip">✅ Fix all TODOs</div>
            <div class="suggestion-chip">🔍 Search for imports</div>
        </div>
        """,
        elem_classes=["suggestions-container"]
    )
    
    return command_input, suggestions
