# parser

Source syntax parsing.

Owns tokenization and parse output for NamuMark-like syntax. The parser should
be deterministic and database-free.

## MVP Limits (Phase: Parser MVP)

The parser MVP implements core NamuMark-like functionality. This section documents what is supported and what is explicitly out of scope.

### Supported Block Elements

- **Headings**: `= Level 1 =`, `== Level 2 ==`, etc. (balanced equals signs required)
- **Paragraphs**: Plain text blocks separated by blank lines
- **Code blocks**: `{{{ code }}}` (inline or multiline)
- **Nowiki blocks**: `<nowiki>literal text</nowiki>` (preserves markup literally)
- **Unordered lists**: `* item`, `** nested`, `*** deeper`
- **Ordered lists**: `# item`, `## nested`, `### deeper`
- **Tables**: `||cell||cell||` (data) and `!!header!!header!!` (headers)
  - Cell options: colspan (`^2`), rowspan (`v2`), alignment (`>`, `<`, `<...<`), background (`#RRGGBB`)
  - Malformed table row recovery (auto-closes missing delimiters)
- **Horizontal rules**: `----` (4+ dashes)
- **Line breaks**: `\\` (two backslashes on a line)

### Supported Inline Elements

- **Bold**: `'''text'''`
- **Italic**: `''text''`
- **Strikethrough**: `~~text~~`
- **Internal links**: `[[Page]]` or `[[Page|Label]]`
  - Special link types: `[[Category:Name]]`, `[[Redirect:Target]]`, `[[Backlink:Name]]`
- **External links**: `[http://example.com]` or `[http://example.com label]` (http, https, ftp)
- **Footnotes**: `[* footnote text *]` (supports repeated footnotes)

### Supported Macros

- **Include/Transclusion**: `#include(PageName)` (extracts page reference)
- **Folding**: `[[^Title]]` (collapsed sections; extracts title reference)

### Metadata Extraction

Parser extracts the following metadata from documents:
- Links (internal link targets)
- Categories (document categories)
- Headings (with level information)
- External links (URLs with protocols)
- Redirects (redirect targets)
- Backlinks (backlink references)
- Footnotes (footnote content)
- Transclusions (included page names)
- Foldings (folding section titles)

### MVP Limitations (Out of Scope)

The following features are NOT supported in the MVP:

1. **Inline code**: Backticks (`` `code` ``) are not recognized
2. **Subscript/Superscript**: No `~~subscript~~` or `^^superscript^^` syntax
3. **Underline**: No underline markup
4. **Definition lists**: No `; term : definition` syntax
5. **Media**: No image (`[[File:...]]`) or other media syntax
6. **HTML/Entities**: No raw HTML; entity patterns are recognized but not validated
7. **Comments**: No comment syntax (e.g., `<!-- -->`)
8. **Variables/Templates**: No template inclusion (`{{...}}`) or variable expansion
9. **Conditional blocks**: No if/switch/etc. blocks
10. **Include parameters**: `#include` does not support parameters
11. **Macro parameters**: Folding and other macros do not support parameters
12. **Table features**:
    - No nested tables
    - No table captions or summary attributes
    - No cell spanning across multiple header/data boundaries
    - No table sorting attributes
13. **List features**:
    - Cannot mix ordered and unordered list types in same block
    - No list attributes
14. **Block nesting**:
    - No nested block elements (e.g., lists within tables, tables within quotes)
    - Code and nowiki blocks terminate all other contexts
15. **Link features**:
    - No section fragment links (e.g., `[[Page#Section]]`)
    - No named parameters (e.g., `[[Link|text|class=special]]`)
    - Links are extracted but not resolved
16. **Footnote features**:
    - No automatic numbering
    - No footnote definitions section
17. **Section editing**:
    - No edit section markers
18. **Custom elements**:
    - Only `<nowiki>` is supported; other HTML tags are treated as text
    - No custom block-level elements

### Determinism Guarantee

The parser is fully deterministic: the same input always produces identical output, with no external dependencies (database-free, no randomness).
