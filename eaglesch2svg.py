import xmltodict
import attrdict
from schematic import Schematic
import argparse
import svgwrite


class MyParser(object):

    def __init__(self):
        self._parser = argparse.ArgumentParser(description="")
        self._parser.add_argument("--input", "-I", help="schematic input",
                                  default="untitled.sch")
        self._parser.add_argument("--output", "-O", help="SVG input",
                                  default="svg.svg")
        self.args = self._parser.parse_args(namespace=self)


def main():
    parser = MyParser()
    filename = parser.input
    output = parser.output

    with open(filename, "r") as f:
        read = f.read()
    sch = xmltodict.parse(read)
    sch = attrdict.AttrDict(sch["eagle"]["drawing"]["schematic"])
    # instances = list(sch.sheets.sheet.instances.instance)
    # print([instance["@part"] for instance in instances])
    sch = Schematic(sch)
    dwg = svgwrite.Drawing(filename=output, debug=True)
    dwg.viewbox(-350, -350, 700, 700)
    symbols = dwg.defs
    [symbols.add(symbol) for symbol in sch.symbols]

    dwg.add(sch.schematic)
    # print(schematic.tostring())

    dwg.save(pretty=True)


if __name__ == "__main__":
    main()
