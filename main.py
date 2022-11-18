import csv, pprint

import tokens

POSTFIX = {
    'an': 'alkane'
}

def load_sample_names(path: str) -> list[str]:
    names: list[str] = []

    with open(path) as file:
        raw = csv.reader(file)

        for entry in raw:
            names.extend(entry)
    return names

class WrongBranchError(Exception):

    def __init__(self) -> None:
        super().__init__()

class Parser:

    @staticmethod
    def load_numerals(path: str):
        numerals: dict = {}
        
        # Read .csv file
        with open(path) as file:
            raw = csv.reader(file)

            # For each row add entry to numerals
            for row in raw:
                number, *rest = row

                number = int(number)
                rest = list(x.strip() for x in rest)

                for prefix in rest: numerals[prefix] = number

        return numerals

    @staticmethod
    def load_multipliers(path: str):
        multipliers: dict = {}
        
        # Read .csv file
        with open(path) as file:
            raw = csv.reader(file)

            for row in raw:
                number, name = row

                multipliers[name.strip()] = number

        return multipliers

    def __init__(self) -> None:
        self.numerals = Parser.load_numerals('./data/numerals.csv')
        self.multipliers = Parser.load_multipliers('./data/multipliers.csv')
        self.postfixes = POSTFIX

    def consume_numeral(self, text: str) -> tuple[int, str]:
        # Check prefixes
        for option in self.numerals.keys():
            # If match was found return digit and text with prefix removed
            if text.startswith(option):
                token = tokens.NumericToken(self.numerals[option], option)
                rest = text[len(option):]
                # There is a issue with first ten alkans (-an) is overlapping with (...a-)
                # rest if rest != 'n' else 'an' is a fix
                return token, rest if rest != 'n' else 'an'
        raise WrongBranchError

    def consume_multiplier(self, text: str):
        for option in self.multipliers.keys():
            if text.startswith(option):
                token = tokens.MultiplierToken(self.multipliers[option], option)
                rest = text[len(option):]
                return token, rest
        raise WrongBranchError

    def consume_postfix(self, text: str):
        for option in self.postfixes.keys():
            if text.startswith(option):
                token = tokens.PostfixToken(self.postfixes[option], option)
                rest = text[len(option):]
                return token, rest
        raise WrongBranchError


    def parse(self, name: str):
        parsed_tokens = []
        funcs = [self.consume_multiplier, self.consume_numeral, self.consume_postfix]
        errors: int = 0
        while name and errors < len(funcs):
            errors = 0
            for func in funcs:
                try: token, name = func(name)
                except WrongBranchError:
                    errors += 1
                    continue
                parsed_tokens.append(token)

        return parsed_tokens

if __name__ == '__main__':
    parser = Parser()
    #numerals, all_prefixes = parser.load_numerals('./data/numerals.csv')
    #pprint.pprint(numerals, indent = 4)
    #print(all_prefixes)

    names = load_sample_names('./data/sample.csv')

    for name in names:
        parsed = parser.parse(name)

        print(f'{parsed} is {name}')
