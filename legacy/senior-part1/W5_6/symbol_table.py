from dataclasses import dataclass
import unicodedata
import logging

#unicodedata -->module implementing unicode char database features
#allows-->char classfication,normalization,script detection.

logger = logging.getLogger("Symbol Table")
#Creates logger named Symbol Table.
# --> WARNING | SymbolTable | Unicode identifier spoofing detected

logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

@dataclass
class SymbolEntry:
    name: str
    line: int
    column: int

class SymbolTable:

    def __init__(self):
        self.table = {}
        self.log = logger

    def normalize_identifier(self, name):
#nfkc-->normalization form compatibility composition.-->removes compatibility diff.,converts chars to standard form.
        return unicodedata.normalize("NFKC", name)        

    def add_symbol(self, name, line, column):
        normalized = self.normalize_identifier(name)
        #even cylliric gets mapped to the same normal key.
        if normalized not in self.table:
            self.table[normalized] = []

        #detects when 2 identifiers normalize to the same value but original text differs.    
        for entry in self.table[normalized]:        
                if entry.name != name:
                    self.log.warning(
                        f"WARNING: Possible Unicode spoofing: {entry.name} vs {name} at line {line}"
                    )
        self.table[normalized].append(
            SymbolEntry(name, line, column)
        )    

    

 #Add into table if it's a identifier
    def build_from_tokens(self, tokens):
        for tok in tokens:

            if tok.token_type.name == "IDENTIFIER":

                self.add_symbol(
                    tok.raw_value,
                    tok.line,
                    tok.column
                )           
 #Export Symbol Table--> <x, line=1, column=4>
    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:

            for name, entries in self.table.items():

                for e in entries:

                    f.write(
                        f"<{name}, line={e.line}, column={e.column}>\n"
                    )               
