class Table:
    def __init__(self, columns: list):
        self.columns = columns

    class ColumnItem:
        def __init__(self, value: str, newline: bool, exclusive: bool = False):
            self.value = value
            self.newline = newline
            self.exclusive = exclusive

    # Puts {x} spaces around a string
    @staticmethod
    def spaceout(string: str, spaces: int):
        output = ""
        spaces2int = int((spaces - len(string)) / 2)
        spaces2float = (spaces - len(string)) / 2
        if spaces2int != 0:
            output = " " * spaces2int
        if spaces2float != spaces2int:
            if string.endswith("."):
                output = output + " " + string
            else:
                output = output + string + " "
        else:
            output = output + string
        if spaces2int != 0:
            output = output + " " * spaces2int
        return output

    # Returns an asci table
    # "Don't look at the code of this function it's a half working mess!"
    def show(self):
        # You have been warned!
        rows = []
        rowsint = 2
        for item in self.columns[0]:
            if item.newline:
                rowsint = rowsint + 2
            else:
                rowsint = rowsint + 1
        for row in range(rowsint):
            rows.append("")

        for column_i, column in enumerate(self.columns):
            longest = 0
            for item in column:
                if len(item.value) > longest:
                    longest = len(item.value)
            for i in range(len(column)):
                column[i].value = Table.spaceout(column[i].value, longest)

            rows[0] = rows[0] + "═" * (longest + 2) + "╤"
            z = 1
            for i, item in enumerate(column):
                if item.exclusive:
                    rows[z] = rows[z] + " " + item.value + " " + "║"
                elif len(self.columns) > column_i + 1:
                    if self.columns[column_i + 1][i].exclusive:
                        rows[z] = rows[z] + " " + item.value + " " + "║"
                    else:
                        rows[z] = rows[z] + " " + item.value + " " + "│"
                else:
                    rows[z] = rows[z] + " " + item.value + " " + "│"
                if item.newline:
                    if i != len(column) - 1:
                        z = z + 1
                        if item.exclusive or column[i + 1].exclusive:
                            rows[z] = rows[z] + "═" * (longest + 2) + "●"
                        elif len(self.columns) > column_i + 1:
                            if self.columns[column_i + 1][i].exclusive:
                                rows[z] = rows[z] + "─" * (longest + 2) + "●"
                            elif self.columns[column_i + 1][i + 1].exclusive:
                                rows[z] = rows[z] + "─" * (longest + 2) + "●"
                            else:
                                rows[z] = rows[z] + "─" * (longest + 2) + "┼"
                        else:
                            rows[z] = rows[z] + "─" * (longest + 2) + "┼"
                z = z + 1
            rows[z] = rows[z] + "═" * (longest + 2) + "╧"

        for i in range(len(rows)):
            if i == 0:
                rows[i] = "╔" + rows[i][:-1] + "╗"
            elif i == len(rows) - 1:
                rows[i - 1] = "╚" + rows[i - 1][:-1] + "╝"
        z = 0
        for i, item in enumerate(self.columns[0]):
            z = z + 1
            if item.newline:
                rows[z] = "║" + rows[z][:-1] + "║"
                if z == len(rows) - 3:
                    break
                z = z + 1
                rows[z] = "╟" + rows[z][:-1] + "╢"
            else:
                rows[z] = "║" + rows[z][:-1] + "║"

        output = ""
        for row in rows:
            output = output + row + "\n"
        return output
