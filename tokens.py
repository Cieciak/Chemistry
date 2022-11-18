from dataclasses import dataclass

@dataclass
class NumericToken:
    number: int
    prefix: str

@dataclass
class MultiplierToken:
    amount: int
    name: str

@dataclass
class PostfixToken:
    name: str
    postfix: str