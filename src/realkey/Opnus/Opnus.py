from math import atan2, sqrt, pi

from build123d import *
from ocp_vscode import *

from realkey.Common import key

class Memolis(key.Key):
    MEMOLIS_KEY_WIDTH = 3.25*MM
    MEMOLIS_KEY_HEIGHT = 8.5*MM
    MEMOLIS_KEY_SHOULDER_START = 31*MM
    MEMOLIS_KEY_BOTTOM_START = 6.25*MM

    MEMOLIS_R_CUT_SPACINGS = [i*3.75*MM + 7*MM for i in range(7)] # Right of keyway, with the arrow being at the top
    MEMOLIS_L_CUT_SPACINGS = [i*3.75*MM + 9*MM for i in range(7)]
    MEMOLIS_CUT_DEPTHS = [i*0.35*MM for i in range(6)]

    MEMOLIS_MAX_DEPTH = MEMOLIS_CUT_DEPTHS[-1]
    MEMOLIS_CUT_SURFACE_WIDTH = 1*MM


    @classmethod
    def name(cls) -> str:
        return "opnus_memolis"

    @classmethod
    def profiles(cls) -> set[str]:
        return {"memolis", "memolis_change"}

    @classmethod
    def keyways(cls) -> set[str]:
        return {"memolis"}

    @classmethod
    def blank(cls, profile: str, keyway: str) -> Part:
        if profile not in cls.profiles(): raise ValueError("Invalid profile specified!")
        if keyway not in cls.keyways(): raise ValueError("Invalid keyway specified!")

        paclock_svg = import_svg("resources/Opnus.svg", flip_y=False, label_by="inkscape:label")

        blank_profile = paclock_svg.filter_by(lambda shape: shape.label == "#profile_" + profile)[0].faces()[0]
        blank = extrude(blank_profile, cls.MEMOLIS_KEY_WIDTH)
        blank.position -= blank.bounding_box().min

        keyway_shape = paclock_svg.filter_by(lambda shape: shape.label == "#keyway_"+keyway)[0]
        keyway_shape = keyway_shape.mirror(Plane.XZ)
        keyway_shape.position -= keyway_shape.bounding_box().min

        keyway_cutter = Pos(-0.2*MM, -0.2*MM) * Rectangle(8.8*MM, 3.5*MM,0,(Align.MIN, Align.MIN))    
        keyway_cutter -= keyway_shape
        keyway_cutter = offset(Sketch(keyway_cutter), 0.005*MM)
    
        keyway_cutter = Sketch(Location((cls.MEMOLIS_KEY_SHOULDER_START,cls.MEMOLIS_KEY_BOTTOM_START,0),(90,90,0)) * keyway_cutter)
        keyway_cutter = extrude(keyway_cutter, 40*MM)
    
        blank -= keyway_cutter

        key_tip_edges = blank.edges().filter_by_position(Axis.X, 63.5,65)
        blank = chamfer(key_tip_edges, 0.75*MM)

        top_fillet_edges = select_edges(blank, [3,35,109,114]) if profile == "memolis" else select_edges(blank, [113,3,35,118])
        blank = chamfer(top_fillet_edges, cls.MEMOLIS_CUT_SURFACE_WIDTH / sqrt(2))

        tip_edges_2nd = select_edges(blank, [133,132,45,7]) if profile == "memolis" else select_edges(blank, [7,45,137,138]) 
        blank = chamfer(tip_edges_2nd, 0.25*MM)

        return Part(blank, "Opnus Memolis Key Blank")

    @classmethod
    def cut_definition(cls) -> str:
        return "There are 14 cuts from depths 0 to 5, cut 1 starts nearest to the bow on the right of keyway side (triangle on lock face is top of keyway), and alternate sides. Cuts 1 and 14 are always fixed for a given lock, but the rest can be changed with the appropriate change key and new key."
    
    @classmethod
    def key_cutter(cls):
        base = RectangleRounded(1.5*MM, 1.25*MM, 0.624*MM)
        base = extrude(base, cls.MEMOLIS_MAX_DEPTH)

        trapezoid_angle = 180/pi * atan2(2*cls.MEMOLIS_MAX_DEPTH, 5.5*MM)
        side = Trapezoid(6.5*MM, cls.MEMOLIS_MAX_DEPTH, trapezoid_angle, align=Align.MIN)
        side = Pos(3.25*MM,0.5*MM,cls.MEMOLIS_MAX_DEPTH) * Rotation(90,0,180) * side
        side = extrude(Sketch(side), cls.MEMOLIS_CUT_SURFACE_WIDTH)
        side_bottom = side.faces().filter_by_position(Axis.Z,-1,0.1)[0]       
        top = Pos(0,0,cls.MEMOLIS_MAX_DEPTH) * make_hull(Rectangle(6.5*MM, cls.MEMOLIS_CUT_SURFACE_WIDTH).edges() + Rectangle(cls.MEMOLIS_CUT_SURFACE_WIDTH, 2.5*MM).edges())

        cutter = loft(side_bottom + top)
        cutter += base
        return cutter
    
    @classmethod
    def key(cls, profile: str, keyway: str, cuts: str) -> Part:
        a_key = cls.blank(profile, keyway)
        cutter = cls.key_cutter()
        mirror_plane_1 = Plane.XZ.offset(-cls.MEMOLIS_KEY_BOTTOM_START - cls.MEMOLIS_KEY_HEIGHT/2)
        mirror_plane_2 = Plane.XY.offset(cls.MEMOLIS_KEY_WIDTH/2)

        for i, cut in enumerate(cuts):
            is_right_side = (i % 2 == 0)
            depth_index = int(cut)
            cut_index = i//2

            cut_x = cls.MEMOLIS_R_CUT_SPACINGS[cut_index] if is_right_side else cls.MEMOLIS_L_CUT_SPACINGS[cut_index]
            cut_x += cls.MEMOLIS_KEY_SHOULDER_START
            cut_depth = cls.MEMOLIS_CUT_DEPTHS[depth_index]
            rotation = 45 if is_right_side else -45

            cut_y = cls.MEMOLIS_KEY_BOTTOM_START
            if not is_right_side:
                cut_y += cls.MEMOLIS_KEY_HEIGHT

            cutter_tool = Pos(0,0,-cut_depth-cls.MEMOLIS_CUT_SURFACE_WIDTH/2) * cutter
            cutter_tool = Location((cut_x,cut_y,cls.MEMOLIS_KEY_WIDTH),(rotation,0,0)) * cutter_tool
            
            a_key -= cutter_tool
            cutter_tool = mirror(Part() + cutter_tool, mirror_plane_1)
            cutter_tool = mirror(cutter_tool, mirror_plane_2)
            a_key -= cutter_tool
        return Part(a_key, "Opnus Memolis Key")

if __name__ == '__main__':
    from ocp_vscode import *
    a_key = Memolis.key("memolis_change", "memolis", "45005500323521")
    #export_step(a_key, "memolis_change_key.step")
    show_all()