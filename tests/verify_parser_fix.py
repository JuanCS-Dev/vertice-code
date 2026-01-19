import unittest
from vertice_tui.core.parsing.tool_call_parser import ToolCallParser


class TestParserFix(unittest.TestCase):
    def test_positional_args_parsing(self):
        """Verify the parser now handles positional arguments which caused the E2E failure."""

        # This is the format Claude was outputting that failed before
        claude_output = 'write_file("test_e2e_bridge.txt", "Vértice E2E Pass")'

        # Extract using the patched parser
        results = ToolCallParser.extract(claude_output)

        print(f"\nParsing: {claude_output}")
        print(f"Results: {results}")

        # Assertions
        self.assertEqual(len(results), 1, "Should find 1 tool call")
        name, args = results[0]
        self.assertEqual(name, "write_file")
        self.assertEqual(args.get("path"), "test_e2e_bridge.txt")
        self.assertEqual(args.get("content"), "Vértice E2E Pass")
        print("✅ SUCCESS: Parser now handles positional arguments!")


if __name__ == "__main__":
    unittest.main()
