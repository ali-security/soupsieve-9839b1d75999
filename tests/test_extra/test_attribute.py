"""Test attribute selectors."""
import subprocess
import sys
from .. import util

# Maximum time (in seconds) a malformed selector is allowed to take before it is considered hung.
COMPILE_TIMEOUT = 20


class TestAttribute(util.TestCase):
    """Test attribute selectors."""

    MARKUP = """
    <div id="div">
    <p id="0">Some text <span id="1"> in a paragraph</span>.</p>
    <a id="2" href="http://google.com">Link</a>
    <span id="3">Direct child</span>
    <pre id="pre">
    <span id="4">Child 1</span>
    <span id="5">Child 2</span>
    <span id="6">Child 3</span>
    </pre>
    </div>
    """

    def test_attribute_not_equal_no_quotes(self):
        """Test attribute with value that does not equal specified value (no quotes)."""

        # No quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!=\\35]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_quotes(self):
        """Test attribute with value that does not equal specified value (quotes)."""

        # Quotes
        self.assert_selector(
            self.MARKUP,
            "body [id!='5']",
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def test_attribute_not_equal_double_quotes(self):
        """Test attribute with value that does not equal specified value (double quotes)."""

        # Double quotes
        self.assert_selector(
            self.MARKUP,
            'body [id!="5"]',
            ["div", "0", "1", "2", "3", "pre", "4", "6"],
            flags=util.HTML5
        )

    def assert_fails_fast(self, pattern):
        """Assert that a bad pattern fails with a syntax error instead of hanging the regular expression engine."""

        # Compile in a separate process. A pattern that triggers catastrophic backtracking cannot be
        # reliably interrupted with a timer on every platform (`signal.SIGALRM` is not available on Windows).
        source = '\n'.join(
            [
                'import soupsieve as sv',
                'try:',
                '    sv.compile({})'.format(pattern),
                'except sv.SelectorSyntaxError:',
                '    pass',
                'else:',
                "    raise AssertionError('Expected a SelectorSyntaxError')",
                ''
            ]
        )

        try:
            status = subprocess.run(
                [sys.executable, '-c', source],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=COMPILE_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            self.fail('Compiling the pattern did not complete in {} seconds'.format(COMPILE_TIMEOUT))
        self.assertEqual(status.returncode, 0, status.stdout.decode('utf-8', 'replace'))

    def test_bad_attribute_unclused(self):
        """Test bad attribute fails for syntax error, not timeout error."""

        # Unclosed, double quoted attribute value: `[a="xxx...`
        self.assert_fails_fast("'[a=' + chr(34) + ('x' * 300)")

    def test_bad_attribute_unclused_single_quote(self):
        """Test bad attribute with a single quoted value fails for syntax error, not timeout error."""

        # Unclosed, single quoted attribute value: `[a='xxx...`
        self.assert_fails_fast("'[a=' + chr(39) + ('x' * 300)")

    def test_bad_attribute_unclused_no_quote(self):
        """Test bad attribute with an unquoted value fails for syntax error, not timeout error."""

        # Unclosed, unquoted attribute value: `[a=xxx...`
        self.assert_fails_fast("'[a=' + ('x' * 300)")
