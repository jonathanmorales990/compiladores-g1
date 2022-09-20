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


class ParserError(Exception):
    """An error exception for parser errors."""


class Lexer:
    OPEN_PAR = 1
    CLOSE_PAR = 2
    OPERATOR = 3
    NUM = 4
    VARIABLE = 5

    def __init__(self, data):
        self.data = data
        self.hashTable = {}
        self.current = 0
        self.previous = -1
        self.num_re = re.compile(r"[+-]?(\d+(\.\d*)?|\.\d+)(e\d+)?")
        self.var_re = re.compile(r"[a-zA-Z]+")

    def __iter__(self):
        self.current = 0
        return self

    def error(self, msg=None):
        err = (
            f"Error at pos {self.current}: "
            f"{self.data[self.current - 1:self.current + 10]}"
        )
        if msg is not None:
            err = f"{msg}\n{err}"
        raise ParserError(err)

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
    def peek(self):
        if self.current < len(self.data):
            current = self.current
            while self.data[current] in " \t\n\r":
                current += 1
            previous = current
            char = self.data[current]
            current += 1
            if char == "(":
                return (Lexer.OPEN_PAR, char, current)
            if char == ")":
                return (Lexer.CLOSE_PAR, char, current)
            if char in "+/*^=":
                return (Lexer.OPERATOR, char, current)
            match = self.num_re.match(self.data[current - 1 :])
            matchVar = self.var_re.match(self.data[current - 1 :])

            if matchVar is not None:
                self.current += matchVar.end() - 1
                return (Lexer.VARIABLE, matchVar.group().replace(" ", ""), current)
            if match is None:
                if char == "-":
                    return (Lexer.OPERATOR, char, current)
                raise Exception(
                    f"Error at {current}: "
                    f"{self.data[current - 1:current + 10]}"
                )
            current += match.end() - 1
            return (Lexer.NUM, match.group().replace(" ", ""), current)
        return (None, None, self.current)

    def __next__(self):
        token_id, token_value, current = self.peek()
        if token_id is not None:
            self.previous = self.current
            self.current = current
            return (token_id, token_value)
        raise StopIteration()


def parse_E(data):
    T = parse_T(data)
    E_prime = parse_E_prime(data)
    return T + (E_prime or 0)


def parse_E_prime(data):
    try:
        token, operator = next(data)
    except StopIteration:
        return 0
    if token == Lexer.OPERATOR and operator in "+-":
        T = parse_T(data)
        E_prime = parse_E_prime(data)
        return (T if operator == "+" else -1 * T) + (E_prime or 0)

    if token not in [Lexer.OPERATOR, Lexer.OPEN_PAR, Lexer.CLOSE_PAR, Lexer.VARIABLE]:
        data.error(f"Invalid character: {operator}")

    data.put_back()
    return 0


def parse_T(data):
    F = parse_F(data)
    T_prime = parse_T_prime(data)
    F_prime = parse_F_prime(data)
    if F_prime is not None:
        return F ** F_prime
    return F * (T_prime or 1)

def parse_F_prime(data):
    try:
        token, operator = next(data)
    except StopIteration:
        return None
    if token == Lexer.OPERATOR and operator in "^":
        F = parse_F(data)
        # We don't need the result of the recursion,
        # only the recuscion itself
        _F_prime = parse_F_prime(data)  # noqa
        return F if operator == "^" else None
    data.put_back()
    return None

def parse_T_prime(data):
    try:
        token, operator = next(data)
    except StopIteration:
        return 1
    if token == Lexer.OPERATOR and operator in "*/":
        F = parse_F(data)
        T_prime = parse_T_prime(data)
        return (F if operator == "*" else 1 / F) * T_prime

    if token not in [Lexer.OPERATOR, Lexer.OPEN_PAR, Lexer.CLOSE_PAR, Lexer.VARIABLE]:
        data.error(f"Invalid character: {operator}")

    data.put_back()
    return 1


def parse_F(data):
    try:
        token, value = next(data)
    except StopIteration:
        raise Exception("Unexpected end of source.") from None
    if token == Lexer.OPEN_PAR:
        E = parse_E(data)
        try:
            if next(data) != (Lexer.CLOSE_PAR, ")"):
                data.error("Unbalanced parenthesis.")
        except StopIteration:
            data.error("Unbalanced parenthesis.")
        return E
    if token == Lexer.NUM:
        return float(value)
    if token == Lexer.VARIABLE:
        return data.get_id(value)
    raise data.error(f"Unexpected token: {value}.")

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
