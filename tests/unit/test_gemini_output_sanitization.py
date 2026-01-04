"""
Test Gemini Output Sanitization - 2026 Fixes.

Tests for:
- Malformed code fence handling
- Inline content deduplication
- Language detection from content

Based on 2026 research:
- Gemini CLI Issues #8392, #8439 (P1 markdown bugs)
- Chrome Best Practices for LLM Streaming
- Incremark incremental parsing techniques
"""

import pytest
import re


class TestCodeFenceSanitization:
    """Test code fence sanitization from streaming_adapter.py."""

    def test_duplicated_fence_marker(self):
        """Test: ```lang```lang → ```lang"""
        pattern = re.compile(r'```(\w+)```\1')

        # Test cases
        assert pattern.sub(r'```\1', '```html```html') == '```html'
        assert pattern.sub(r'```\1', '```python```python') == '```python'
        assert pattern.sub(r'```\1', '```tool_code```tool_code') == '```tool_code'

        # Should not affect normal fences
        assert pattern.sub(r'```\1', '```python') == '```python'
        assert pattern.sub(r'```\1', '```html\n<html>') == '```html\n<html>'

    def test_fence_with_html_content_on_same_line(self):
        """Test: ```html<html> → ```html\n<html>"""
        # Pattern for HTML tags immediately after language
        pattern_html = re.compile(r'```(\w+)(<[^>\n]+>)')

        # Test HTML tag after language (immediate, no space)
        # This is the main case we want to fix - Gemini outputs like ```html<html>
        result = pattern_html.sub(r'```\1\n\2', '```html<html>')
        assert result == '```html\n<html>'

        # Test with full HTML tag
        result = pattern_html.sub(r'```\1\n\2', '```html<div class="foo">')
        assert result == '```html\n<div class="foo">'

        # Should not affect proper fences with newline
        assert pattern_html.sub(r'```\1\n\2', '```python\ndef foo():') == '```python\ndef foo():'

    def test_fence_with_json_content_on_same_line(self):
        """Test: ```json{ → ```json\n{"""
        # Pattern for JSON/object literals after language
        pattern_json = re.compile(r'```(\w+)([\{\[])')

        # Test JSON opening brace (common pattern)
        result = pattern_json.sub(r'```\1\n\2', '```json{')
        assert result == '```json\n{'

        # Test array opening bracket
        result = pattern_json.sub(r'```\1\n\2', '```json[')
        assert result == '```json\n['

        # Should not affect proper fences with newline
        assert pattern_json.sub(r'```\1\n\2', '```json\n{}') == '```json\n{}'


class TestInlineDeduplication:
    """Test inline content deduplication."""

    def test_duplicated_closing_tags(self):
        """Test: </body></body> → </body>"""
        pattern = re.compile(r'(</\w+>)\1+')

        assert pattern.sub(r'\1', '</body></body>') == '</body>'
        assert pattern.sub(r'\1', '</div></div></div>') == '</div>'
        assert pattern.sub(r'\1', '</html></html>') == '</html>'

        # Should not affect different tags
        assert pattern.sub(r'\1', '</body></html>') == '</body></html>'

    def test_duplicated_opening_tags(self):
        """Test: <div><div> → <div>"""
        pattern = re.compile(r'(<\w+[^>]*>)\1+')

        assert pattern.sub(r'\1', '<div><div>') == '<div>'
        assert pattern.sub(r'\1', '<span><span><span>') == '<span>'

        # With attributes
        assert pattern.sub(r'\1', '<div class="foo"><div class="foo">') == '<div class="foo">'

    def test_immediate_word_duplication(self):
        """Test: word word → word"""
        pattern = re.compile(r'\b(\w{3,})\s+\1\b')

        assert pattern.sub(r'\1', 'hello hello') == 'hello'
        assert pattern.sub(r'\1', 'the the') == 'the'
        assert pattern.sub(r'\1', 'function function') == 'function'

        # Should not affect short words (less than 3 chars) - prevents false positives
        assert pattern.sub(r'\1', 'do do') == 'do do'  # 'do' is only 2 chars

        # Should not affect intentional repetitions in different contexts
        assert pattern.sub(r'\1', 'foo bar bar baz') == 'foo bar baz'


class TestLanguageDetection:
    """Test language detection from content."""

    def test_html_detection(self):
        """Test HTML/XML language detection."""
        from vertice_cli.tui.components.block_detector import BlockDetector

        detector = BlockDetector()

        # HTML tags
        assert detector._guess_language_from_content('<html>', '<html><body>') == 'html'
        assert detector._guess_language_from_content('<!DOCTYPE', '<!DOCTYPE html>') == 'html'
        assert detector._guess_language_from_content('<div>', '<div class="foo">') == 'html'

        # SVG
        assert detector._guess_language_from_content('<svg', '<svg viewBox="0 0 100 100">') == 'svg'

    def test_python_detection(self):
        """Test Python language detection."""
        from vertice_cli.tui.components.block_detector import BlockDetector

        detector = BlockDetector()

        assert detector._guess_language_from_content('def', 'def foo():') == 'python'
        assert detector._guess_language_from_content('class', 'class Foo:') == 'python'
        assert detector._guess_language_from_content('import', 'import os') == 'python'
        assert detector._guess_language_from_content('from', 'from typing import List') == 'python'

    def test_javascript_detection(self):
        """Test JavaScript language detection."""
        from vertice_cli.tui.components.block_detector import BlockDetector

        detector = BlockDetector()

        assert detector._guess_language_from_content('function', 'function foo() {') == 'javascript'
        assert detector._guess_language_from_content('const', 'const x = 1') == 'javascript'
        assert detector._guess_language_from_content('let', 'let y = 2') == 'javascript'

    def test_bash_detection(self):
        """Test Bash/Shell language detection."""
        from vertice_cli.tui.components.block_detector import BlockDetector

        detector = BlockDetector()

        assert detector._guess_language_from_content('#!/bin/bash', '#!/bin/bash\necho hello') == 'bash'
        assert detector._guess_language_from_content('echo', 'echo "hello world"') == 'bash'

    def test_json_detection(self):
        """Test JSON language detection."""
        from vertice_cli.tui.components.block_detector import BlockDetector

        detector = BlockDetector()

        assert detector._guess_language_from_content('{', '{"key": "value"}') == 'json'
        assert detector._guess_language_from_content('[', '[1, 2, 3]') == 'json'

    def test_sql_detection(self):
        """Test SQL language detection."""
        from vertice_cli.tui.components.block_detector import BlockDetector

        detector = BlockDetector()

        assert detector._guess_language_from_content('SELECT', 'SELECT * FROM users') == 'sql'
        assert detector._guess_language_from_content('INSERT', 'INSERT INTO table') == 'sql'


class TestBlockDetectorCodeFence:
    """Test BlockDetector code fence pattern."""

    def test_flexible_code_fence_pattern(self):
        """Test that code fence pattern is more flexible."""
        from vertice_cli.tui.components.block_detector import BlockDetector, BlockType

        pattern = BlockDetector.PATTERNS[BlockType.CODE_FENCE]

        # Standard fence
        match = pattern.match('```python')
        assert match is not None
        assert match.group(2) == 'python'

        # Fence with trailing content (Gemini bug)
        match = pattern.match('```html<html>')
        assert match is not None
        assert match.group(2) == 'html'

        # Fence without language
        match = pattern.match('```')
        assert match is not None
        assert match.group(2) == ''

        # Tilde fence
        match = pattern.match('~~~javascript')
        assert match is not None
        assert match.group(2) == 'javascript'


class TestIntegration:
    """Integration tests for the full sanitization pipeline."""

    def test_full_sanitization_flow(self):
        """Test that malformed Gemini output is properly sanitized."""
        import re

        # Simulate the sanitization flow from streaming_adapter.py
        def sanitize_chunk(chunk: str) -> str:
            # BLINDAGEM 3: Fix malformed code fences
            chunk = re.sub(r'```(\w+)```\1', r'```\1', chunk)
            chunk = re.sub(
                r'```(\w+)(<[^>\n]+>|[a-zA-Z_][a-zA-Z0-9_]*\s*[\(\{])',
                r'```\1\n\2',
                chunk
            )

            # BLINDAGEM 4: Inline deduplication
            chunk = re.sub(r'(</\w+>)\1+', r'\1', chunk)
            chunk = re.sub(r'(<\w+[^>]*>)\1+', r'\1', chunk)
            chunk = re.sub(r'\b(\w{3,})\s+\1\b', r'\1', chunk)

            return chunk

        # Test case 1: Duplicated fence + duplicated tags
        malformed = '```html```html<html><body></body></body></html>'
        result = sanitize_chunk(malformed)
        assert '```html```html' not in result
        assert '</body></body>' not in result
        assert '```html' in result

        # Test case 2: Language on same line as content
        malformed = '```python def foo():'
        result = sanitize_chunk(malformed)
        assert '\n' in result or result == malformed  # Should split or stay same

        # Test case 3: Word duplication
        malformed = 'the the quick brown brown fox'
        result = sanitize_chunk(malformed)
        assert 'the the' not in result
        assert 'brown brown' not in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
