# Language definition:
# P = SP
# S = ID
# S = E
# ID = E
# E = TE'
# E' = +TE' | - TE' | &
# T = FT' | F'T'
# T' = * FT' | / FT' | &
# F = ( E ) | num
# F' = F^F
# num = [+-]?([0-9]+(.[0-9]+)?|.[0-9]+)(e[0-9]+)+)?)
# var = [a-zA-Z]+

import re

class Variable:
    def __init__(self, index, value):
        self.index = index
        self.value = value

class Lexer:
    OPEN_PAR = 1
    CLOSE_PAR = 2
    OPERATOR = 3
    NUM = 4
    VARIABLE = 5

    def __init__(self, data):
        self.data = data
        self.hashTable = { 'x': 6}
        self.current = 0
        self.previous = -1
        self.num_re = re.compile(r"[+-]?(\d+(\.\d*)?|\.\d+)(e\d+)?")
        self.var_re = re.compile(r"[a-zA-Z]+")
    def __iter__(self):
        self.current = 0
        return self

    def error(self, msg=None):
        err = (
            f"Error at {self.current}: "
            f"{self.data[self.current - 1:self.current + 10]}"
        )
        if msg is not None:
            err = f"{msg}\n{err}"
        raise Exception(err)

    def put_back(self):
        self.current = self.previous
    def get_id(self, variable):
        return self.hashTable.get(variable)
    def add_id(self, value, variable):
        self.hashTable[variable] = value
        return value
    def next_operator(self):
        char = self.data[self.current + 1]
        if char in "+/*^=":
            return (Lexer.OPERATOR, char)
        return None
    def __next__(self):
        if self.current < len(self.data):
            while self.data[self.current] in " \t\n\r":
                self.current += 1
            self.previous = self.current
            char = self.data[self.current]
            self.current += 1

            if char == "(":
                return (Lexer.OPEN_PAR, char)
            if char == ")":
                return (Lexer.CLOSE_PAR, char)
            if char in "+/*^=":
                return (Lexer.OPERATOR, char)

            matchVar = self.var_re.match(self.data[self.current - 1 :])
            match = self.num_re.match(self.data[self.current - 1 :])

            if matchVar is not None:
                self.current += matchVar.end() - 1
                return (Lexer.VARIABLE, matchVar.group().replace(" ", ""))
            if match is None and matchVar is None:
                if char == "-":
                    return (Lexer.OPERATOR, char)
                raise Exception(
                    f"Error at {self.current}: "
                    f"{self.data[self.current - 1:self.current + 10]}"
                )
            else:
                self.current += match.end() - 1
                return (Lexer.NUM, match.group().replace(" ", ""))
        raise StopIteration()


def parse_E(data):
    T = parse_T(data)
    E_prime = parse_E_prime(data)
    return T if E_prime is None else T + E_prime


def parse_E_prime(data):
    try:
        token, operator = next(data)
    except StopIteration:
        return None

    if token == Lexer.OPERATOR:
        if operator not in "+-":
            data.error(f"Unexpected token: '{operator}'.")
        T = parse_T(data)
        _E_prime = parse_E_prime(data)
        return T if operator == "+" else -1 * T
    data.put_back()
    return None


def parse_T(data):
    F = parse_F(data)
    T_prime = parse_T_prime(data)
    F_prime = parse_F_prime(data)

    if F_prime is not None:
        return F ** F_prime
    return F if T_prime is None else F * T_prime

def parse_F_prime(data):
    try:
        token, operator = next(data)
    except StopIteration:
        return None
    if token == Lexer.OPERATOR and operator in "^":
        F = parse_F(data)
        _F_prime = parse_F_prime(data)
        return F if operator == "^" else None
    data.put_back()
    return None

def parse_T_prime(data):
    try:
        token, operator = next(data)
    except StopIteration:
        return None
    if token == Lexer.OPERATOR and operator in "*/":
        F = parse_F(data)
        # We don't need the result of the recursion,
        # only the recuscion itself
        _T_prime = parse_T_prime(data)  # noqa
        return F if operator == "*" else 1 / F
    data.put_back()
    return None


def parse_F(data):
    """Parse an expression F."""
    try:
        token, value = next(data)
    except StopIteration:
        raise Exception("Unexpected end of source.") from None

    if token == Lexer.OPEN_PAR:
        E = parse_E(data)
        if next(data) != (Lexer.CLOSE_PAR, ")"):
            data.error("Unbalanced parenthesis.")
        return E
    if token == Lexer.NUM:
        return float(value)
    if token == Lexer.VARIABLE:
        return data.get_id(value)
    raise data.error(f"A Unexpected token: {value}.")

def parse_S(data):
    ID = parse_ID(data)
    EQ = parse_EQ(data)
    data.add_id(EQ, ID)
    if EQ is None:
        return parse_E(data)
    return parse_S(data)

def parse_EQ(data):
    try:
        token, operator = next(data)
    except StopIteration:
        return None
    if token == Lexer.OPERATOR and operator in "=":
        return parse_E(data)
    data.put_back()
    return None

def parse_ID(data):
    try:
        token, value = next(data)
    except StopIteration:
        return None
    if token == Lexer.VARIABLE:
        if data.next_operator() == (Lexer.OPERATOR, "="):
            return value
    data.put_back()
    return None

def parse_P(data):
    return parse_S(data)
    if S is not None:
        return parse_P(data)
    else:
        return S

def parse(source_code):
    lexer = Lexer(source_code)
    return parse_P(lexer)


if __name__ == "__main__":
    expressions = [
        "2 + 2 + 2",
        "2 + 2 ^ 2",
        "x = 2 ^ 2 c = 2 y = 4 x + y * c"
    ]
    for expression in expressions:
        print(f"Expression: {expression}\t Result: {parse(expression)}")
