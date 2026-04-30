from build123d import *

from realkey.Common import key

class SR(key.Key):
    SR_KEY_X_DATUM = 28*MM
    SR_KEY_Y_DATUM = 7.5*MM
    SR_KEY_WIDTH = 2*MM
    SR_KEY_BLADE_HEIGHT = 8.25*MM
    SR_KEY_BLADE_WIDTH = 0.75*MM
    SR_KEY_OFFSET = 1.0*MM

    SR_CUT_SPACINGS = [i*2.25*MM + 5.5*MM for i in range(11)]
    SR_CUT_DEPTHS = [0*MM, 0.625*MM, 1.575*MM, 2*MM] # last cut jumps to 2mm based on known cuts

    @classmethod
    def name(cls) -> str:
        return "miwa_sr"

    @classmethod
    def display_name(cls) -> str:
        return "MIWA SR"

    @classmethod
    def profiles(cls) -> dict[str, str]:
        return {"10cut" : "10-cut"}

    @classmethod
    def keyways(cls) -> dict[str, str]:
        return {"sr" : "SR"}

    @classmethod
    def blank(cls, profile: str, keyway: str) -> key.Part:
        if profile not in cls.profiles(): raise ValueError("Invalid profile specified!")
        if keyway not in cls.keyways(): raise ValueError("Invalid keyway specified!")

        miwa_svg = import_svg("resources/MIWA.svg", flip_y=False, label_by="inkscape:label")
        profile_face = miwa_svg.filter_by(lambda shape: shape.label == "#profile_sr_" + profile)[0].faces()[0]
        profile_face.position -= profile_face.bounding_box().min
        
        keyway_face = miwa_svg.filter_by(lambda shape: shape.label == "#keyway_"+keyway)[0]
        keyway_face.position -= keyway_face.bounding_box().center()
        keyway_face.translate((1,0,0))
        
        with BuildPart() as sr_blank:
            with BuildSketch():
                add(profile_face)
            extrude(amount = cls.SR_KEY_WIDTH)
            
            with BuildSketch(Plane.YZ.offset(cls.SR_KEY_X_DATUM)):
                with Locations((cls.SR_KEY_Y_DATUM + cls.SR_KEY_BLADE_HEIGHT / 2, cls.SR_KEY_WIDTH / 2)):
                    Rectangle(cls.SR_KEY_BLADE_HEIGHT + 5.0*MM, cls.SR_KEY_WIDTH)
                    kw = add(keyway_face, mode = Mode.PRIVATE)
                    offset(kw, amount = -0.125*MM, kind = Kind.INTERSECTION, mode = Mode.SUBTRACT) 
            extrude(amount = 50*MM, mode = Mode.SUBTRACT)            
        return Part(sr_blank.part)

    @classmethod
    def cut_definition(cls) -> str:
        return "There are 4 cut depths, listed from tip to bow.<br/>" \
        "The maximum cut is not a cut, and is labelled 0, with the minimum cut being 3.<br/>" \
        "Do note that position 8 lacks a slider/wafer, so despite there being 11 holes, only 10 are populated.<br/>" \
        "We ignore this cut when reading bitting.<br/>" \
        "<i>E.g. 1101203021</i>"

    @classmethod
    def validate_bitting(cls, profile: str, keyway: str, bitting: str):
        if not bitting.isnumeric():
            raise ValueError("Only numeric cuts are allowed")
        if len(bitting) > 10:
            raise ValueError("Only up to 10 cuts are allowed")
                
        for cut in bitting:
            if int(cut) < 0 or int(cut) > 3:
                raise ValueError("Cut depths must be from 0 to 3")

    @classmethod
    def key(cls, profile: str, keyway: str, bitting: str) -> key.Part:
        cls.validate_bitting(profile, keyway, bitting)

        sr_blank = SR.blank(profile, keyway)
        mirror_plane = Plane.XZ.offset(-cls.SR_KEY_Y_DATUM - cls.SR_KEY_BLADE_HEIGHT / 2)

        with BuildPart() as sr_key:
            add(sr_blank)

            for i, cut in enumerate(bitting):
                depth_index = int(cut)
                spacing_index = i if i<8 else i + 1 # there is a blank cut at position 8
                if depth_index == 0: continue # No point doing math when this does no cut
                
                cut_x = cls.SR_KEY_X_DATUM + cls.SR_CUT_SPACINGS[spacing_index]
                cut_y = cls.SR_KEY_Y_DATUM - 2*MM + cls.SR_CUT_DEPTHS[depth_index]
                
                with BuildSketch() as cutter:
                    with Locations((cut_x, cut_y)):
                        Trapezoid(6*MM, 4*MM, 60)
                    mirror(about = mirror_plane)
                extrude(amount = cls.SR_KEY_WIDTH*2, mode = Mode.SUBTRACT)
        return Part(sr_key.part)

if __name__ == '__main__':
    from ocp_vscode import *
    #sr_blank = SR.blank("10cut", "sr")
    #export_step(sr_blank, "sr_blank.step")
    sr_key = SR.key("10cut", "sr", "1101203021")
    export_step(sr_key, "sr_key.step")
    show_all()

    