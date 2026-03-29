import re
import mwparserfromhell

def wikitext_to_clean_intro(raw_content):

    wikicode = mwparserfromhell.parse(raw_content)
    sections = wikicode.get_sections()
    intro = sections[0]
    clean_text = intro.strip_code(normalize=True, collapse=True)
    clean_text = clean_text.replace("'''", "").replace("''", "")
    clean_text = re.sub(r'\(\s*(or|and|,|;)?\s*\)', '', clean_text)
    clean_text = clean_text.replace("\n", "")
    
    return clean_text.strip()