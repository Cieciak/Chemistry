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

if __name__ == '__main__':

    tokenizer = Tokenizer(PRIMARY_TOKEN_TABLE)

    compounds = [
        '2,3,4-trijodo-7-2-metylobutano-9-bromo-12-tenesoheksadekan'
        '5,6-dibromohept-3-en',
        'tetrafluorometan',
        'etyn',
        'buten',
        'nonen',
        '1,2-dimetylobutan',
        '1-metylo-2,3-dibromopentan',
        '2,2-dijododekan',
        '4-butylononan',
        'tridekan',
        'tritriakontan',
        '3-pentanon',
        'butan-2-on',
        '4-etynodekan',
        '5-etenodekan',
    ]

    for compound in compounds:

        pts = tokenizer.pre_tokenize(compound)
        #print(pts)
        ts = tokenizer.tokenize(pts)
        pprint.pprint(ts, indent = 4)
        print()