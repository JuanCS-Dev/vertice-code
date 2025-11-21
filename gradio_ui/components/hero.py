"""Hero section component - Emotional entry point."""
import gradio as gr


def create_hero_section():
    """
    Create hero section with emotional impact.
    
    Design goals:
    - Immediate "wow" factor
    - Clear value proposition
    - Inviting call-to-action
    """
    with gr.Row(elem_classes=["hero-section"]):
        gr.Markdown(
            """
            <div class="hero-title">🚀 QWEN-DEV-CLI</div>
            <div class="hero-subtitle">Your AI-Powered Development Partner</div>
            <p style="color: #64748b; font-size: 1rem;">
                Multi-language LSP • Smart Refactoring • Context-Aware Suggestions
            </p>
            """,
            elem_classes=["hero-content"]
        )
