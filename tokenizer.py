from dataclasses import dataclass
from collections import namedtuple
from enum import Enum, auto
import re, csv, pprint

IUPAC_Rule = namedtuple('IUPAC_Rule', ['type', 'value'])

# This holds regexes for primary parsing
PRIMARY_TOKEN_TABLE = {
    'locant': '^-?\d+(,\d+)*-',
    'raw_text': '^[a-z]+',
}

class PrimaryTokenType(Enum):
    LOCANT: str = 'locant'
    RAW_TEXT: str = 'raw_text'

    DIGIT: str = 'digit'
    GROUP: str = 'group'
    FUNCTIONAL: str = 'functional'
    MULTIPLIER: str = 'multiplier'
    ELEMENT: str = 'element'

@dataclass
class PrimaryToken:
    type: PrimaryTokenType
    value: str

    def __repr__(self) -> str:
        return f'{self.type}: {self.value}'

class TokenType(Enum):

    LOCANT: str = 'locant'
    DIGIT: str = 'digit'
    GROUP: str = 'group'
    MULTIPLIER: str = 'multiplier'
    ELEMENT: str = 'element' 

@dataclass
class Token: 
    type: TokenType
    data: list

class GenericParserError(Exception):

    def __init__(self, text: str) -> None:
        super().__init__(text)

class Tokenizer:

    @staticmethod
    def load_affixes(path: str) -> dict[str, IUPAC_Rule]:
        output = {}
        with open(path) as file:
            raw = csv.reader(file)

            # Scan each row and get all options
            for row in raw:
                if len(row) <= 1: continue

                identifier, _type, *rest = [word.strip() for word in row]

                for option in rest:
                    output[option] = IUPAC_Rule(PrimaryTokenType(_type), identifier)

        return output

    @staticmethod
    def flatten(array: list) -> list:
        output = []
        for element in array:
            if type(element) == list:
                output.extend(Tokenizer.flatten(element))
            else:
                output.append(element)
        return output

    def __init__(self, ptt: dict[str, str]) -> None:

        # Compile given primary token table to patterns and store them
        # dict[PrimaryTokenType, Pattern]
        self.compiled_primary_tt: dict = {}
        for key, value in ptt.items():
            self.compiled_primary_tt[PrimaryTokenType(key)] = re.compile(value)

        self.affixes = Tokenizer.load_affixes('./data/affixes.csv')

    def pre_tokenize(self, text: str) -> list[PrimaryToken]:
        output: list[PrimaryToken] = []
        # Try to parse compound using regexes
        while text:
            for token, pattern in self.compiled_primary_tt.items():
                # Match pattern with text
                m = re.match(pattern, text)
                if m:
                    start, end = m.span()
                    value = text[:end]
                    text = text[end:]
                    output.append(PrimaryToken(token, value))
                    break
            # If failed to parse scream
            else:
                raise GenericParserError(f'No matching token in \"{text}\"')
        return output

    def tokenize(self, token_string: list[PrimaryToken]):
        output = token_string[::1]
        for index, token in enumerate(token_string):
            match token.type:
                case PrimaryTokenType.LOCANT:
                    output[index] = self.parse_locant(token)
                case PrimaryTokenType.RAW_TEXT:
                    output[index] = self.parse_raw_text(token)

        return Tokenizer.flatten(output)

    def parse_raw_text(self, token: PrimaryToken):
        output = []
        raw = token.value
        while raw:
            for affix, rule in self.affixes.items():
                if raw.startswith(affix):
                    raw = raw[len(affix):]
                    # This is to prevent eating up -a from alkanes
                    if raw == 'n': raw = affix[-1] + raw
                    # Get rid of syntactic sugar from Polish names
                    if rule.type == PrimaryTokenType.FUNCTIONAL: break
                    output.append(Token(rule.type, [rule.value, ]))
                    break
            else:
                raise GenericParserError(f'No pattern matching \"{raw}\"')
        return output

    def parse_locant(self, token: PrimaryToken):
        pattern = re.compile('\d+')

        return Token(TokenType.LOCANT, pattern.findall(token.value))

class Node:

    def __init__(self, value, kids) -> None:
         self.value = value
         self.kids = kids

    def __repr__(self) -> str:
        return f'{self.value}{self.kids[::-1]}'

class Molecule: 


    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens[::-1]

        self.main_group = None
        self.main_chain = None
        self.number_search = False
        self.proto_number = 0
        self.number_queue = []
        self.multipiler_queue = []
        self.locant_queue = []
        self.locant_places = []

    def __repr__(self) -> str:
        out = f'{self.main_group} {self.locant_places} {self.locant_queue} {self.number_queue}'
        return out

    def generate(self):
        while self.tokens:
            self.consume()

        if self.proto_number:
            self.number_queue.append(self.proto_number)
            self.proto_number = 0
            self.number_search = False

        self.main_chain = self.number_queue.pop(0)

        self.skeleton = [Node('C', []) for i in range(self.main_chain)]
        bond = (0, 0 )
        if self.main_group != 'alkan':
            i = int(self.locant_places.pop(0)[0])
            bond = (i, i+1)

        copy = self.number_queue.copy()
        for locant, place in zip(self.locant_queue, self.locant_places):


            for p in place:
                if locant[0]:
                    self.skeleton[int(p)-1].kids.append(locant[1])
                else:
                    self.skeleton[int(p)-1].kids.append(copy.pop(0))



        for i, node in enumerate(self.skeleton):
            if len(node.kids) != 4:
                if i == 0:
                    node.kids.append(f'H{3-len(node.kids)}')
                elif i == len(self.skeleton) -1:
                    node.kids.append(f'H{3-len(node.kids)}')
                elif (i == bond[0]-1 or bond[1]-1) and (not self.main_group == 'alkan'):
                    f = {'alken': 2, 'alkin': 1}
                    node.kids.append(f'H{f[self.main_group]-len(node.kids)}')
                else:
                    node.kids.append(f'H{2-len(node.kids)}')

            for i, kid in enumerate(node.kids):
                if type(kid) == int:
                    node.kids[i] = f'C{kid}H{2*kid+1}'

        a = [f'{node.value}{"(" + "".join(node.kids) + ")"}' if len(node.kids) > 1 else f'{node.value}{node.kids[0]}' for node in self.skeleton]
        f =  {'alken': 2, 'alkin': 1, 'alkan': 0}
        symbol = '-≡='[f[self.main_group]]

        o = ''
        for i, c in enumerate(a):
            o += f'{c}{symbol if i == bond[0]-1 else "-"}'

        t = {
            '1':'₁',
            '2':'₂',
            '3':'₃',
            '4':'₄',
            '5':'₅',
            '6':'₆',
            '7':'₇',
            '8':'₈',
            '9':'₉',
            '0':'₀',
        }

        out = ''
        for char in o:
            if char in t:
                out += t[char]
            else: out += char

        return out[:-1]

    def consume(self):
        current = self.tokens.pop(0)
        match current.type:

            case PrimaryTokenType.GROUP:
                if self.main_group is None: self.main_group = current.data[0]
                else: self.locant_queue.append((False, current.data[0]))
                if self.proto_number:
                    self.number_queue.append(self.proto_number)
                    self.proto_number = 0
                    self.number_search = False


            case PrimaryTokenType.DIGIT:
                if self.number_search == False:
                    self.number_search = True
                self.proto_number += int(current.data[0]) * self.multipiler_queue.pop(0) if self.multipiler_queue else int(current.data[0])

            case PrimaryTokenType.MULTIPLIER:
                self.multipiler_queue.append(int(current.data[0]))

            case PrimaryTokenType.ELEMENT:
                if self.proto_number:
                    self.number_queue.append(self.proto_number)
                    self.proto_number = 0
                    self.number_search = False
                self.locant_queue.append((True, current.data[0]))

            case TokenType.LOCANT:
                if self.proto_number:
                    self.number_queue.append(self.proto_number)
                    self.proto_number = 0
                    self.number_search = False
                self.locant_places.append(current.data)

            case _:
                print(current.type)
                if self.proto_number:
                    self.number_queue.append(self.proto_number)
                    self.proto_number = 0
                    self.number_search = False



if __name__ == '__main__':

    tokenizer = Tokenizer(PRIMARY_TOKEN_TABLE)

    compounds = [
        '2,3,4-trijodo-7-butylo-9-bromo-12-tenesoheksadekan',
        '5,6-dibromohept-3-en',
        #'tetrafluorometan',
        'et-1-yn',
        'but-1-en',
        'non-1-en',
        #'1,2-dimetylobutan',
        '1-metylo-2,3-dibromopentan',
        '2,2-dijododekan',
        '4-butylononan',
        'tridekan',
        'tritriakontan',
        '4-etynodekan',
        '5-etenodekan',
        'pentan',
        'pentadekan',
        'etan',
    ]

    for compound in compounds:

        pts = tokenizer.pre_tokenize(compound)
        #print(pts)
        ts = tokenizer.tokenize(pts)
        #pprint.pprint(ts, indent = 4)
        #print()

        mol = Molecule(ts)
        t = mol.generate()
        print(t)