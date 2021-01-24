Generates dictionary index from bookmarks in the PDF for the 5th volume
of "Pramana Vachana Sangrha". Generates two files:
- index.txt (articles are in the PDF order)
- index-sorted.txt (sanskrit alphabet order: a, ā, i, ī, etc)

Tested on windows, shold work on any platform with trivial tool path fix.

Expectations:
- "tools/mutool-1.18.0.exe" exists (from mupdf)
- "../pramANa vachana sangraha v5 niruktarItyA padAnAM arthavivaraNam.pdf"
  exists with specific bookmarks arrangement.
