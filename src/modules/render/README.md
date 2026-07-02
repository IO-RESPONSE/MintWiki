# render

Safe HTML rendering with comprehensive sanitization and escaping.

Owns safe HTML rendering, sanitization rules (HTML escaping, CSS validation, URL schemes),
conversion from parser output to sanitized HTML, render metadata extraction, heading ID generation,
table HTML rendering, and deterministic render cache key construction.

## Render Safety Rules

### 1. HTML Escaping

**Rule**: All user-provided text content must be HTML-escaped before rendering.

All text content flows through `escape_html()` which escapes:
- `&` → `&amp;` (ampersand)
- `<` → `&lt;` (less-than)
- `>` → `&gt;` (greater-than)
- `"` → `&quot;` (double quote)
- `'` → `&#x27;` (single quote)

**Purpose**: Prevents XSS attacks by rendering HTML special characters as entity references.

**Applied to**: All text in paragraphs, headings, lists, tables, code blocks, and nowiki content.

### 2. CSS Sanitization

**Rule**: CSS values must be sanitized to prevent injection attacks.

`sanitize_css_value()` blocks:

**Keywords** (always rejected):
- `expression`, `behavior` — IE XSS vectors
- `@import`, `@keyframes` — Resource loading and animation definitions
- `@-moz-`, `@-webkit-`, `@-ms-` — Vendor-specific at-rules
- `javascript`, `data`, `vbscript` — Code execution schemes
- `-moz-binding` — Mozilla binding XSS

**Functions** (blocked patterns):
- `expression()` — IE dynamic expression
- `url()` — When containing `javascript:`, `data:`, or `vbscript:`
- `var()` — CSS variables for override attempts

**Patterns** (blocked):
- Unicode escapes: `\0`, `\00` (null byte obfuscation)
- CSS comments: `/*` and `*/` (hidden malicious patterns)
- Whitespace in schemes: Indicates obfuscation attempt

**Safe values** (pass sanitization):
- Colors: `red`, `#FF0000`, `rgb(255, 0, 0)`, `rgba(0, 0, 0, 0.5)`
- Dimensions: `10px`, `50%`, `2em`, `auto`
- Layout: `block`, `inline`, `flex`, `grid`
- Properties: `bold`, `italic`, `left`, `center`, `1px solid black`

**Applied to**: Table cell styling, text alignment, padding, background colors.

### 3. URL Sanitization

**Rule**: URLs must use safe schemes to prevent code execution.

`sanitize_url()` enforces whitelist of safe schemes:
- `http`, `https` — Standard web URLs
- `ftp`, `ftps` — File transfer
- `mailto` — Email links
- `tel`, `sms` — Communication links
- `geo` — Location links

**Blocked schemes** (always rejected):
- `javascript:` — Arbitrary JavaScript execution
- `data:` — Data URLs with embedded HTML/JavaScript
- `vbscript:` — Legacy VBScript execution

**Relative URLs** (always safe):
- `/path/to/page`, `./relative/path`, `../parent/path` — pass unmodified

**Applied to**: Link targets, form actions, redirects, image sources.

### 4. Content Escaping

**Nowiki content** (`render_nowiki()`):
- Escape HTML special characters
- Wrap in `<code>` tag
- Prevents wiki markup interpretation

**Code blocks** (`render_code_block()`):
- Escape HTML special characters
- Wrap in `<pre><code>` tags
- Preserves formatting while preventing XSS

### 5. Render Cache Key

**Rule**: Cache keys must be deterministic and incorporate parser version.

`build_render_cache_key(source: str, parser_version: str)`:
- **Format**: `render:v{version}:{sha256_hash}`
- **Components**: Parser version + SHA256 hash of source
- **Properties**: Deterministic, version-aware, collision-resistant
- **Invalidation**: Parser version changes invalidate all caches

**Purpose**: Ensures cache hits only occur when parser version matches, preventing stale renders.

## Security Assumptions

These rules assume:
- HTML output is the only attack surface
- Sanitizers are applied before HTML generation
- All user input is untrusted
- Parser is trusted

## Testing

All safety rules are tested:
- `tests/modules/render/test_escape.py` — HTML escaping
- `tests/modules/render/test_css_sanitizer.py` — CSS validation
- `tests/modules/render/test_url_sanitizer.py` — URL schemes
- `tests/modules/render/test_code_block.py` and `test_nowiki.py` — Content escaping
