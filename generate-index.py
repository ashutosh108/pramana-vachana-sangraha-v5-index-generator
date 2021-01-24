import re
import subprocess
import unicodedata

PDF_FILE_NAME = "../pramANa vachana sangraha v5 niruktarItyA padAnAM arthavivaraNam.pdf"
MUTOOL_PATH="tools\\mutool-1.18.0.exe"
PAGE_SHIFT=40

san_letters = ['a', 'ā', 'i', 'ī', 'u', 'ū', 'ṛ', 'ṝ', 'e', 'ai', 'o', 'au', 'ṁ', 'ṃ', 'ḥ',
    'k', 'kh', 'g', 'gh', 'ṅ',
    'c', 'ch', 'j', 'jh', 'ñ',
    'ṭ', 'ṭh', 'ḍ', 'ḍh', 'ṇ',
    't', 'th', 'd', 'dh', 'n',
    'p', 'ph', 'b', 'bh', 'm',
    'y', 'r', 'l', 'v',
    'ś', 'ṣ', 's', 'h',
    ]

san_letter_regex = "(" + str.join("|", sorted(san_letters, key=lambda x: len(unicodedata.normalize("NFD", x)), reverse=True)) + "|.)"

def sanskrit_letters(text):
    return re.findall(san_letter_regex, text)

def mycmp(i1, i2):
    if i1 < i2:
        return -1
    elif i1 == i2:
        return 0
    else:
        return +1
    
def sanskrit_cmp_letters(letter1, letter2):
    if (not letter1 in san_letters) or (not letter2 in san_letters):
        return mycmp(letter1, letter2)
    return mycmp(san_letters.index(letter1), san_letters.index(letter2))
 
def sanskrit_cmp_arrays(arr1, arr2):
    for i in range(min(len(arr1), len(arr2))):
        cmp = sanskrit_cmp_letters(arr1[i], arr2[i])
        if cmp < 0:
            return -1
        elif cmp > 0:
            return +1
    if len(arr1) < len(arr2):
        return -1
    elif len(arr1) == len(arr2):
        return 0
    else:
        return +1

class Bookmark:
    def __init__(self, text, shastra, page, shastra_ref=None):
        self.text = text
        self.shastra = shastra
        self.page = page
        if shastra_ref is None:
            m = re.match(r'(.*)\s+\((.*(?:\d|\.\.\.).*)\)$', text)
            if m:
                self.text = m.group(1)
                self.shastra_ref = "{} {}".format(shastra, m.group(2))
            else:
                self.shastra_ref = shastra
        else:
            self.shastra_ref = shastra_ref

    def __str__(self):
        return "{} ({}) — p.{}".format(self.text, self.shastra_ref, self.page)
    def __lt__(self, other):
        we = sanskrit_letters(self.text.lower())
        them = sanskrit_letters(other.text.lower())
        return sanskrit_cmp_arrays(we, them) < 0
        

def get_bookmarks_text(pdf_filename):
    result = subprocess.run(
        [MUTOOL_PATH, "show", pdf_filename, "outline"],
        capture_output=True,
        text=True,
        check=True,
        encoding="utf8")
    return result.stdout

def embed_shastra_name(shastra_name, bookmark_name):
    m = re.match(r'(.*)\s+\((.*(?:\d|\.\.\.).*)\)$', bookmark_name)
    if m:
        return "{} ({} {})".format(m.group(1), shastra_name, m.group(2))
    return "{} ({})".format(bookmark_name, shastra_name)

def abbreviate_shastra_name(shastra_name):
    map = {
        "Gītā-bhāṣyam": "gī-bhā",
        "Gītā-tātparya-nirṇayaḥ": "gī-tā-ni",
        "Ṛg-bhāṣyam": "ṛg-bhā",
        "Viṣṇu-tatva-vinirṇayaḥ": "vi-ta-ni",
        "Tatvodyotaḥ": "tatvodyotaḥ",
        "Karmanirṇayaḥ": "karmanirṇayaḥ",
        "Brahma-sūtra-bhāṣyam": "br-sū-bhā",
        "Īśāvāsyopaniṣad-bhāṣyam": "īśā-up-bhā",
        "Atharvaṇopaniṣad-bhāṣyam": "atha-up-bhā",
        "Māṇḍūkyopaniṣad-bhāṣyam": "mā-up-bhā",
        "Kenopaniṣad-bhāṣyam": "ke-up-bhā",
        "Kaṭhopaniṣad-bhāṣyam": "kaṭha-up-bhā",
        "Taittirīyopaniṣad-bhāṣyam": "tai-up-bhā",
        "Aitareyopaniṣad-bhāṣyam": "ai-up-bhā",
        "Chandogyopaniṣad-bhāṣyam": "cha-up-bhā",
        "Bṛhadāraṇyakopaniṣad-bhāṣyam": "bṛ-up-bhā",
        "Bhāgavata tātparya-nirṇayaḥ": "bhā-tā-ni",
    };
    if shastra_name in map:
        return map[shastra_name]
    raise Exception(shastra_name)
    return shastra_name

def get_bookmarks(pdf_filename):
    text = get_bookmarks_text(pdf_filename)
    shastra_name = "unknown"
    bm = []
    for line in text.splitlines():
        match = re.match(r'^[|+-](\t+)"([^"]*)"\t#(\d+)$', line)
        if not match:
            print("error: ", line, "\n")
            break
        (tabs, bookmark_name, page) = match.groups()
        if len(tabs) < 2:
            continue
        # skip Bhāgavatam canto opening bookmarks
        if len(tabs) == 3 and re.match(r'^\d+\.x', bookmark_name):
            continue
        if len(tabs) == 2:
            shastra_name = abbreviate_shastra_name(bookmark_name)
        else:
            bm += [Bookmark(bookmark_name, shastra_name, int(page) - PAGE_SHIFT)]
    return bm

def gen_all_words_for_bookmark(bm):
    new_bm = [Bookmark(bm.text, bm.shastra, bm.page, bm.shastra_ref)]
    # skip bookmarks with '(' in text to avoid these two cases:
    # narāṇāṁ) [utpattiḥ (hareḥ, narāṇāṁ)]
    # ubhaya) [vivakṣā (eka, ubhaya)]
    if not '(' in bm.text:
        for m in re.findall(r'[-,]\s+([^\s,]+)', bm.text):
            new_bm += [Bookmark("{} [{}]".format(m, bm.text), bm.shastra, bm.page, bm.shastra_ref)]
    return new_bm

def gen_all_words(bookmarks):
    new_bookmarks = []
    for bm in bookmarks:
        new_bookmarks += gen_all_words_for_bookmark(bm)
    return new_bookmarks

############## main #################
utf8 = open(1, 'w', encoding='utf-8', closefd=False)
index = open('pramANa vachana sangraha v5 index.txt', 'w', encoding='utf-8')

bookmarks = get_bookmarks(PDF_FILE_NAME)

prev_shastra = None
for bm in bookmarks:
    if bm.shastra != prev_shastra and prev_shastra != None:
        print("", file=index)
    prev_shastra = bm.shastra
    print(bm, file=index)

#bookmarks.sort()

index_sorted = open('pramANa vachana sangraha v5 index-sorted.txt', 'w', encoding='utf-8')
for bm in sorted(gen_all_words(bookmarks)):
    print(bm, file=index_sorted)
