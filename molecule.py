from typing import Self
from dataclasses import dataclass

@dataclass
class Bond:
    id: int
    degree: int

class Node:
    __all: list[Self] = []

    @staticmethod
    def make_bond(N_1: Self, N_2: Self, degree: int):
        N_1_BOND = Bond(N_2.get_id(), degree)
        N_2_BOND = Bond(N_1.get_id(), degree)

        N_1.bonds.append(N_1_BOND)
        N_2.bonds.append(N_2_BOND)
        
        N_1.data[N_2.value] = N_1.data.get(N_2.value, 0) + 1
        

    @classmethod
    def get_by_id(cls: Self, _id, *, default = None, test = True):
        for node in cls.__all:
            if node.get_id() == _id: return node
        if test: raise ValueError(f'There is no node with id {_id}')
        else: return default

    def __init__(self, value: str) -> None:
        self.__id = id(self)
        self.__all.append(self)
        self.__pointer: int | None = None

        self.value = value
        self.data = {}
        self.bonds = []
        self.bond_count = 0
    
    def get_id(self):
        return self.__id

    def set_pointer(self, _id: int):
        self.__pointer = _id

    def get_pointer(self) -> int | None:
        return self.__pointer

    def get_bond(self, _id: int) -> Bond:
        other = Node.get_by_id(_id, test = False)
        if other is None: return Bond(0,0)
        S_ID = [bond.id for bond in self.bonds]
        O_ID = [bond.id for bond in other.bonds]

        if self.get_id() in O_ID and other.get_id() in S_ID:
            bond = [bond for bond in self.bonds if bond.id == other.get_id()][0]
            return bond

    def evaluate_bonds(self):
        total = sum(bond.degree for bond in self.bonds)
        self.bond_count = total

    def add_secondary(self: Self, node: Self, degree: int):
        Node.make_bond(self, node, degree)

    def add_hydrogens(self):
        for _ in range(4 - self.bond_count):
            hydrogen = Node('H')
            self.add_secondary(hydrogen, 1)

    def __repr__(self) -> str:
        return self.value

class Molecule:

    BOND_SYMBOL = {
        0: ' ',
        1: '-',
        2: '=',
        3: '≡',
    }

    SUBSCRIPT = {
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

    def __init__(self, length: int):
        self.length = length
        self.head: Node = None

    def __repr__(self):
        output = ''
        current = self.head
        while current:
            data = ''
            # TODO: Make this work for n digit number
            for key, val in current.data.items(): data += f'{key}{Molecule.SUBSCRIPT[str(val)]}'
            bond = current.get_bond(current.get_pointer())
            output += f'{current.value}{data}{Molecule.BOND_SYMBOL[bond.degree]}'
            current = current.get_by_id(current.get_pointer(), test = False)
        return output

    def sumaric(self):
        total = {}
        current = self.head
        while current:
            total


    def evaluate_bonds(self):
        current = self.head
        while current:
            current.evaluate_bonds()
            current = Node.get_by_id(current.get_pointer(), test = False)

    def add_hydrogens(self):
        current = self.head
        while current:
            current.add_hydrogens()
            current = Node.get_by_id(current.get_pointer(), test = False)

    def get_nth_coal(self, n):
        n -= 1
        current = self.head
        while n:
            n -= 1
            current = Node.get_by_id(current.get_pointer())
        return current

    def get_last_chain(self):
        if self.head is None: return None
        current = self.head
        while current.get_pointer() is not None:
            current = Node.get_by_id(current.get_pointer())
        return current

    def make_carbon_chain(self):
        for index in range(self.length):
            new = Node('C')
            if self.head is None: self.head = new
            else:
                last = self.get_last_chain()
                last_bond = Bond(new.get_id(), 1)
                new_bond = Bond(last.get_id(), 1)

                new.bonds.append(new_bond)
                last.bonds.append(last_bond)

                last.set_pointer(new.get_id())

    def change_bond_dergree(self, n: int, degree: int):
        curr = self.get_nth_coal(n)
        next = self.get_nth_coal(n + 1)
        bond = curr.get_bond(next.get_id())
        bond.degree = degree
        bond = next.get_bond(curr.get_id())
        bond.degree = degree
        print(bond)


if __name__ == '__main__':

    h = Node('Br')
    g = Node('Cl')
    f = Node('F')

    m = Molecule(10)
    m.make_carbon_chain()
    #m.change_bond_dergree(1, 2)
    #m.change_bond_dergree(6, 3)

    Node.make_bond(m.get_nth_coal(1), g, 1)
    Node.make_bond(m.get_nth_coal(1), f, 1)
    Node.make_bond(m.get_nth_coal(1), h, 1)

    m.evaluate_bonds()
    m.add_hydrogens()
    print(m)