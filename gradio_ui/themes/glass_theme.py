"""
Glassmorphism Theme for QWEN-DEV-CLI
Emotional design with depth and transparency.
"""
import gradio as gr


def create_glass_theme() -> gr.themes.Base:
    """
    Create custom glassmorphism theme.
    
    Design principles:
    - Dark background (OLED-optimized)
    - Frosted glass cards
    - Subtle gradients
    - Soft shadows
    - Smooth transitions
    """
    
    # Start with Glass base theme
    theme = gr.themes.Glass(
        primary_hue="blue",
        secondary_hue="cyan",
        neutral_hue="slate",
        font=gr.themes.GoogleFont("Inter"),
    )
    
    # Customize theme with CSS variables
    # Note: Gradio 5 uses CSS directly, minimal Python customization
    
    return theme
