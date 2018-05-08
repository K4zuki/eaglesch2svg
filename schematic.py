"""
based on Eagle 7.5.0 DTD
"""

import attrdict
import svgwrite
import re
import pprint


class BaseObject(object):
    name = ""
    MM = 3
    layer2color = {
        "94": "maroon",
        "95": "silver",
        "96": "silver",
    }
    mirror = False
    spin = False
    angle = 0
    get_bool = {"no": False, "yes": True}
    attr = attrdict.AttrDict({})

    def val2mm(self, value):
        return (value * self.MM)

    def coord2mm(self, position):
        x, y = position
        return (self.val2mm(x), self.val2mm(y))

    def rot(self, rotate="R0"):
        mirror, spin, angle = re.findall(re.compile(r"([M]*)([S]*)R(\d+)"), rotate).pop()
        return (bool(mirror), bool(spin), int(angle))


class Wire(BaseObject):
    """
    <!ELEMENT wire EMPTY>
    <!ATTLIST wire
              x1            %Coord;        #REQUIRED
              y1            %Coord;        #REQUIRED
              x2            %Coord;        #REQUIRED
              y2            %Coord;        #REQUIRED
              width         %Dimension;    #REQUIRED
              layer         %Layer;        #REQUIRED
              extent        %Extent;       #IMPLIED
              style         %WireStyle;    "continuous"
              curve         %WireCurve;    "0"
              cap           %WireCap;      "round"
              >
              <!-- extent: Only applicable for airwires -->
              <!-- cap   : Only applicable if 'curve' is not zero -->
    """
    style2dasharray = {
        "continuous": "continuous",
    }
    stroke_linecap = "round"

    def __init__(self, obj):
        print(self.__class__.__name__)
        print(obj.keys())
        x1 = float(obj.get("@x1"))
        x2 = float(obj.get("@x2"))
        y1 = float(obj.get("@y1"))
        y2 = float(obj.get("@y2"))
        width = float(obj["@width"])
        layer = obj["@layer"]
        style = obj.get("@style", "continuous")
        curve = obj.get("@curve", "0")

        self.start = self.coord2mm((x1, y1))
        self.end = self.coord2mm((x2, y2))
        self.stroke_fill = self.layer2color[layer]
        self.stroke_width = self.val2mm(width)
        self.stroke_dasharray = self.style2dasharray[style]
        self.rotate = int(curve)


class Rect(BaseObject):
    """
    <!ELEMENT rectangle EMPTY>
    <!ATTLIST rectangle
              x1            %Coord;        #REQUIRED
              y1            %Coord;        #REQUIRED
              x2            %Coord;        #REQUIRED
              y2            %Coord;        #REQUIRED
              layer         %Layer;        #REQUIRED
              rot           %Rotation;     "R0"
              >
    """

    def __init__(self, obj):
        print(self.__class__.__name__)
        print(obj.keys())
        x1 = float(obj.get("@x1"))
        x2 = float(obj.get("@x2"))
        y1 = float(obj.get("@y1"))
        y2 = float(obj.get("@y2"))
        layer = obj.get("@layer")
        rot = obj.get("@rot", "R0")

        self.insert = self.coord2mm((x1, y1))
        self.size = self.coord2mm((x1-x2, y1-y2))
        self.stroke_fill = self.layer2color[layer]
        self.mirror, self.spin, self.angle = self.rot(rot)


class Text(BaseObject):
    """
    <!ELEMENT text (#PCDATA)>
    <!ATTLIST text
              x             %Coord;        #REQUIRED
              y             %Coord;        #REQUIRED
              size          %Dimension;    #REQUIRED
              layer         %Layer;        #REQUIRED
              font          %TextFont;     "proportional"
              ratio         %Int;          "8"
              rot           %Rotation;     "R0"
              align         %Align;        "bottom-left"
              distance      %Int;          "50"
              >
    """

    normalset = {"bottom": "alphabetic", "top": "text-before-edge",
                 "left": "start", "right": "end"
                 }
    mirrorset = {"bottom": "text-before-edge", "top": "alphabetic",
                 "left": "end", "right": "start",
                 "text-before-edge": "alphabetic", "alphabetic": "text-before-edge",
                 "end": "start", "start": "end"
                 }

    def __init__(self, obj):
        print(self.__class__.__name__)
        print(obj.keys())
        x1 = float(obj.get("@x"))
        y1 = float(obj.get("@y"))
        size = float(obj.get("@size"))
        layer = obj.get("@layer")
        font = obj.get("@font", "proportional")
        rot = obj.get("@rot", "R0")
        align = obj.get("@align", "bottom-left")

        self.insert = self.coord2mm((x1, y1))
        self.font_size = self.val2mm(size)
        self.stroke_fill = self.layer2color[layer]
        self.mirror, self.spin, angle = self.rot(rot)
        self.dominant_baseline, self.text_anchor, self.angle = self.align(align, self.mirror, angle)

    def align(self, align, mirror, rotate):
        align = align.split("-")
        if len(align) == 2:
            vert, horiz = align
            baseline = self.normalset[vert] if not mirror else self.mirrorset[vert]
            anchor = self.normalset[horiz] if not mirror else self.mirrorset[horiz]
        else:
            baseline = "middle"
            anchor = "middle"

        if rotate % 180 == 90:
            rotate = 90
            baseline = self.mirrorset[baseline]
            anchor = self.mirrorset[anchor]
        else:
            rotate = 0
        return (baseline, anchor, rotate)


class Dimension(BaseObject):
    pass


class Circle(BaseObject):
    """
    <!ELEMENT circle EMPTY>
    <!ATTLIST circle
              x             %Coord;        #REQUIRED
              y             %Coord;        #REQUIRED
              radius        %Coord;        #REQUIRED
              width         %Dimension;    #REQUIRED
              layer         %Layer;        #REQUIRED
              >
    """

    def __init__(self, obj):
        print(self.__class__.__name__)
        print(obj.keys())
        x = float(obj["@x"])
        y = float(obj["@y"])
        radius = float(obj["@radius"])
        layer = obj["@layer"]
        font = obj.get("@font", "proportional")
        rot = obj.get("@rot", "R0")
        align = obj.get("@align", "bottom-left")

        self.center = self.coord2mm((x, y))
        self.r = radius
        self.stroke_fill = self.layer2color[layer]
        self.mirror, self.spin, self.angle = self.rot(rot)


class Pin(BaseObject):
    """
    <!ELEMENT pin EMPTY>
    <!ATTLIST pin
              name          %String;       #REQUIRED
              x             %Coord;        #REQUIRED
              y             %Coord;        #REQUIRED
              visible       %PinVisible;   "both"
              length        %PinLength;    "long"
              direction     %PinDirection; "io"
              function      %PinFunction;  "none"
              swaplevel     %Int;          "0"
              rot           %Rotation;     "R0"
              >
    """
    appear_pinname = {"off": False, "pin": True, "pad": False, "both": True}
    appear_padname = {"off": False, "pin": False, "pad": True, "both": True}

    def __init__(self, obj):
        print(self.__class__.__name__)
        print(obj.keys())

        self.get_length = {"point": 0,
                           "short": self.val2mm(2.54),
                           "middle": self.val2mm(5.08),
                           "long": self.val2mm(7.62)}
        self.name = obj["@name"]
        x = float(obj["@x"])
        y = float(obj["@y"])
        visible = obj.get("@visible")
        rot = obj.get("@rot", "R0")
        length = obj.get("@length", "long")

        self.name = obj["@name"]
        self.start = self.coord2mm((x, y))
        self.pin_name = self.appear_pinname[visible]
        self.pin_number = self.appear_padname[visible]
        self.mirror, self.spin, self.angle = self.rot(rot)
        self.end = self.get_end(self.start, length, self.rot)

    def get_end(self, start, length, rot):
        offset = self.get_length[length]
        x, y = start
        if self.rot == 0:
            x += offset*(-1 if self.mirror else 1)
        elif self.rot == 90:
            y += offset*(-1 if self.mirror else 1)
        elif self.rot == 180:
            x -= offset*(-1 if self.mirror else 1)
        elif self.rot == 270:
            y -= offset*(-1 if self.mirror else 1)
        return self.coord2mm((x, y))


class Attribute(Text):
    """
    <!ELEMENT attribute EMPTY>
    <!ATTLIST attribute
              name          %String;       #REQUIRED
              value         %String;       #IMPLIED
              x             %Coord;        #IMPLIED
              y             %Coord;        #IMPLIED
              size          %Dimension;    #IMPLIED
              layer         %Layer;        #IMPLIED
              font          %TextFont;     #IMPLIED
              ratio         %Int;          #IMPLIED
              rot           %Rotation;     "R0"
              display       %AttributeDisplay; "value"
              constant      %Bool;         "no"
              >
              <!-- display: Only in <element> or <instance> context -->
              <!-- constant:Only in <device> context -->
    """

    def __init__(self, obj):
        super().__init__(obj)
        self.name = obj["@name"]
        self.value = obj["@value"]
        self.display = obj.get("@display", "value")


class Instance(BaseObject):
    """
    <!ELEMENT instance (attribute)*>
    <!ATTLIST instance
              part          %String;       #REQUIRED
              gate          %String;       #REQUIRED
              x             %Coord;        #REQUIRED
              y             %Coord;        #REQUIRED
              smashed       %Bool;         "no"
              rot           %Rotation;     "R0"
              >
              <!-- rot: Only 0, 90, 180 or 270 -->
    """
    symbol = None
    attributes = []

    def __init__(self, obj):
        print(self.__class__.__name__)
        print(obj.keys())
        x = float(obj["@x"])
        x = float(obj["@x"])
        rot = obj.get("@rot", "R0")
        smashed = obj.get("@smashed", "no")
        attributes = obj.get("attribute")

        self.gate = obj["@gate"]
        self.part = obj["@part"]
        self.center = self.coord2mm((x, y))
        self.smashed = self.get_bool[smashed]
        self.mirror, self.spin, self.angle = self.rot(rot)
        self.attributes = [Attribute(attribute) for attribute in attributes]


class Part(BaseObject):
    """
    <!ELEMENT part (attribute*, variant*)>
    <!ATTLIST part
              name          %String;       #REQUIRED
              library       %String;       #REQUIRED
              deviceset     %String;       #REQUIRED
              device        %String;       #REQUIRED
              technology    %String;       ""
              value         %String;       #IMPLIED
              >
    """
    attributes = []
    variants = []

    def __init__(self, obj):
        print(self.__class__.__name__)
        print(obj.keys())
        self.name = obj["@name"]
        self.library = obj["@library"]
        self.deviceset = obj["@deviceset"]
        self.device = obj["@device"]
        self.technology = obj.get("@technology", "")
        self.attribute = obj.get("@attribute", "")
        self.value = obj.get("@value")


class Library(BaseObject):
    """
    <!ELEMENT library (description?, packages?, symbols?, devicesets?)>
    <!ATTLIST library
              name          %String;       #REQUIRED
              >
              <!-- name: Only in libraries used inside boards or schematics -->
    """
    description = ""
    packages = None  # this matters with brd/lbr files but not with sch
    symbols = []
    devicesets = []

    def __init__(self, obj):
        print(self.__class__.__name__)
        print(obj.keys())
        # libraries = list(obj.libraries.library) if obj["libraries"] is not None else []
        self.name = obj["@name"]
        self.description = obj.get("description", "")

        if obj["symbols"] is not None:
            symbols = obj["symbols"]["symbol"]
            if isinstance(symbols, list):
                self.symbols = [Symbol(symbol) for symbol in symbols]
            else:
                self.symbols = [Symbol(symbols)]

        if obj["devicesets"] is not None:
            devicesets = obj["devicesets"]["deviceset"]
            if isinstance(devicesets, list):
                self.devicesets = [Deviceset(deviceset) for deviceset in devicesets]
            else:
                self.devicesets = [Deviceset(devicesets)]


class Deviceset(BaseObject):
    """
    <!ELEMENT deviceset (description?, gates, devices)>
    <!ATTLIST deviceset
              name          %String;       #REQUIRED
              prefix        %String;       ""
              uservalue     %Bool;         "no"
              >
    """
    description = None
    gates = []
    devices = []

    def __init__(self, obj):
        print(self.__class__.__name__)
        print(obj.keys())
        # libraries = list(obj.libraries.library) if obj["libraries"] is not None else []
        self.name = obj["@name"]
        self.description = obj.get("description", "")
        self.prefix = obj.get("@prefix", "")
        uservalue = obj.get("@uservalue", "no")

        self.uservalue = self.get_bool[uservalue]


class Connect(BaseObject):
    """
    <!ELEMENT connect EMPTY>
    <!ATTLIST connect
              gate          %String;       #REQUIRED
              pin           %String;       #REQUIRED
              pad           %String;       #REQUIRED
              route         %ContactRoute; "all"
              >
    """

    def __init__(self, gate, pin, pad, route="all"):
        print(self.__class__.__name__)
        print(obj.keys())
        self.gate = obj["@gate"]
        self.pin = obj["@pin"]
        self.pad = obj["@pad"]
        self.route = obj.get("@route", "all")


class Device(BaseObject):
    """
    <!ELEMENT device (connects?, technologies?)>
    <!ATTLIST device
              name          %String;       ""
              package       %String;       #IMPLIED
              >
    """
    connects = None
    technologies = None

    def __init__(self, obj):
        print(self.__class__.__name__)
        print(obj.keys())
        self.name = obj.get("@name", "")
        self.package = obj.get("@package")
        self.connects = obj.get("connects")
        self.technologies = obj.get("technologies")


class Technology(BaseObject):
    """
    <!ELEMENT technology (attribute)*>
    <!ATTLIST technology
              name          %String;       #REQUIRED
              >
    """
    attributes = []

    def __init__(self, obj):
        print(self.__class__.__name__)
        print(obj.keys())
        self.name = obj["@name"]
        attributes = obj.get("attribute")
        self.attributes = [Attribute(attribute) for attribute in attributes]


class Gate(BaseObject):
    """
    <!ELEMENT gate EMPTY>
    <!ATTLIST gate
              name          %String;       #REQUIRED
              symbol        %String;       #REQUIRED
              x             %Coord;        #REQUIRED
              y             %Coord;        #REQUIRED
              addlevel      %GateAddLevel; "next"
              swaplevel     %Int;          "0"
              >
    """

    def __init__(self, obj):
        print(self.__class__.__name__)
        print(obj.keys())
        self.name = obj["@name"]
        symbol = obj["@symbol"]
        x = float(obj["@x"])
        x = float(obj["@x"])

        self.center = self.coord2mm((x, y))


class Frame(BaseObject):
    """
    <!ELEMENT frame EMPTY>
    <!ATTLIST frame
              x1            %Coord;       #REQUIRED
              y1            %Coord;       #REQUIRED
              x2            %Coord;       #REQUIRED
              y2            %Coord;       #REQUIRED
              columns       %Int;         #REQUIRED
              rows          %Int;         #REQUIRED
              layer         %Layer;       #REQUIRED
              border-left   %Bool;        "yes"
              border-top    %Bool;        "yes"
              border-right  %Bool;        "yes"
              border-bottom %Bool;        "yes"
              >
    """

    border = attrdict.AttrDict({})

    def __init__(self, obj):
        print(self.__class__.__name__)
        print(obj.keys())
        x1 = float(obj.get("@x1"))
        x2 = float(obj.get("@x2"))
        y1 = float(obj.get("@y1"))
        y2 = float(obj.get("@y2"))
        layer = obj.get("@layer")
        columns = obj.get("@columns")
        raws = obj.get("@rows")
        border_left = obj.get("@border-left", "yes")
        border_top = obj.get("@border-top", "yes")
        border_right = obj.get("@border-right", "yes")
        border_bottom = obj.get("@border-bottom", "yes")

        self.insert = self.coord2mm((x1, y1))
        self.size = self.coord2mm((x1-x2, y1-y2))
        self.stroke_fill = self.layer2color[layer]
        border.left = get_bool[border_left]
        border.top = get_bool[border_top]
        border.right = get_bool[border_right]
        border.bottom = get_bool[border_bottom]


class Symbol(BaseObject):
    """
    <!ELEMENT symbol (description?, (polygon | wire | text | dimension | pin | circle | rectangle | frame)*)>
    <!ATTLIST symbol
              name          %String;       #REQUIRED
              >
    """
    description = None
    polygons = []
    wires = []
    texts = []
    dimensions = []
    pins = []
    circles = []
    rectangles = []
    frames = []

    def __init__(self, obj):
        print(self.__class__.__name__)
        print(obj.keys())
        self.name = obj["@name"]

        self.description = obj.get("description", "")
        if obj.get("polygon") is not None:
            polygons = obj.polygon
            if isinstance(polygons, list):
                self.polygons = [Polygon(polygon) for polygon in polygons]
            else:
                self.polygons = [Polygon(polygons)]

        if obj.get("wire") is not None:
            wires = obj["wire"]
            if isinstance(wires, list):
                self.wires = [Wire(wire) for wire in wires]
            else:
                self.wires = [Wire(wires)]
        #
        dimensions = list(obj["dimension"]) if obj.get("dimension") is not None else []
        #
        if obj.get("text") is not None:
            texts = obj["text"]
            if isinstance(texts, list):
                self.texts = [Text(text) for text in texts]
            else:
                self.texts = [Text(texts)]
        #
        if obj.get("pin") is not None:
            pins = obj["pin"]
            if isinstance(pins, list):
                self.pins = [Pin(pin) for pin in pins]
            else:
                self.pins = [Pin(pins)]
        #
        if obj.get("circle") is not None:
            circles = obj["circle"]
            if isinstance(circles, list):
                self.circles = [Circle(circle) for circle in circles]
            else:
                self.circles = [Circle(circles)]
        #
        if obj.get("rectangle") is not None:
            rectangles = obj["rectangle"]
            if isinstance(rectangles, list):
                self.rectangles = [Rect(rectangle) for rectangle in rectangles]
            else:
                self.rectangles = [Rect(rectangles)]
        #
        if obj.get("frame") is not None:
            frames = list(obj["frame"])
            if isinstance(frames, list):
                self.frames = [Frame(frame) for frame in frames]
            else:
                self.frames = [Frame(frames)]


class Sheet(BaseObject):
    """
    <!ELEMENT sheet (description?, plain?, moduleinsts?, instances?, busses?, nets?)>
    """
    description = None
    plain = None
    moduleinsts = []
    instances = []
    busses = []
    nets = []

    def __init__(self, obj):
        print(self.__class__.__name__)
        print(obj.keys())
        self.description = obj.get("description")
        self.plain = obj.get("plain")
        self.instances = obj.get("instances")
        print(type(self.instances))


class Plain(BaseObject):
    """
    <!ELEMENT plain (polygon | wire | text | dimension | circle | rectangle | frame | hole)*>
    """
    polygons = []
    wires = []
    texts = []
    dimensions = []
    pins = []
    circles = []
    rectangles = []
    frames = []

    def __init__(self, obj):
        print(self.__class__.__name__)
        print(obj.keys())


class Schematic(BaseObject):
    """
    <!ELEMENT schematic (description?, libraries?, attributes?, variantdefs?, classes?, modules?, parts?, sheets?, errors?)>
    <!ATTLIST schematic
              xreflabel     %String;       #IMPLIED
              xrefpart      %String;       #IMPLIED
              >
    """
    description = []
    libraries = []
    attributes = []
    variantdef = []
    classes = []
    modules = []
    parts = []
    sheets = []
    errors = []

    def __init__(self, obj):
        print("Schematic")
        print(obj.keys())
        self.description = attrdict.AttrDict(obj.get("description", {}))

        if obj["libraries"] is not None:
            libraries = obj["libraries"]["library"]
            if isinstance(libraries, list):
                self.libraries = [Library(library) for library in libraries]
            else:
                self.libraries = [Library(libraries)]

        if obj["attributes"] is not None:
            attributes = obj["attributes"]["attribute"]
            if isinstance(attributes, list):
                self.attributes = [Attribute(attribute) for attribute in attributes]
            else:
                self.attributes = [Attribute(attributes)]

        if obj["parts"] is not None:
            parts = obj["parts"]["part"]
            if isinstance(parts, list):
                self.parts = [Part(part) for part in parts]
            else:
                self.part = [Part(parts)]

        if obj["sheets"] is not None:
            sheets = obj["sheets"]["sheet"]
            if isinstance(sheets, list):
                self.sheets = [Sheet(sheet) for sheet in sheets]
            else:
                self.sheets = [Sheet(sheets)]
