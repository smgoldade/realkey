from math import copysign
from build123d import *
from ocp_vscode import *

from realkey.Common import key_cutters, key

class Desmo(key.Key):
    DESMO_KEY_BLADE_HEIGHT = 9.5*MM
    DESMO_KEY_WIDTH = 3*MM
    DESMO_KEY_SHOULDER_START = 27.725*MM
    DESMO_KEY_BOTTOM = 22*MM
    DESMO_KEY_TOP = 16.75*MM

    DESMO_CUT_SPACINGS = [i*3.5*MM + 4.5*MM for i in range(10)]
    DESMO_CUT_DEPTHS = [i*-0.5*MM + 3.5*MM for i in range(6)]

    DESMO_PIN_DIAMETER = 3*MM
    DESMO_PIN_HEIGHT = 1*MM
    DESMO_TRACK_TOLERANCE = 0.75*MM
    DESMO_TRACK_SOFTENING = 0.55

    @classmethod
    def name(cls) -> str:
        return "assa_desmo"

    @classmethod
    def profiles(cls) -> set[str]:
        return {"desmo_6pin", "desmo_8pin", "desmo_10pin"}

    @classmethod
    def keyways(cls) -> set[str]:
        return {"desmo"}

    @classmethod
    def blank(cls, profile: str, keyway: str) -> Part:
        if profile not in cls.profiles(): raise ValueError("Invalid profile specified!")
        if keyway not in cls.keyways(): raise ValueError("Invalid keyway specified!")

        assa_svg = import_svg("resources/ASSA.svg", flip_y=False, label_by="inkscape:label")
        profile_face = assa_svg.filter_by(lambda shape: shape.label == "#profile_" + profile)[0].faces()[0]
        profile_face.position -= profile_face.bounding_box().min

        keyway_face = assa_svg.filter_by(lambda shape: shape.label == "#keyway_"+keyway)[0]
        keyway_face.position -= keyway_face.bounding_box().center()
        keyway_face = keyway_face.rotate(Axis.Z, -90)
        
        with BuildPart() as desmo_blank:
            with BuildSketch():
                add(profile_face)
            extrude(amount = cls.DESMO_KEY_WIDTH)
            
            with BuildSketch(Plane.YZ.offset(cls.DESMO_KEY_SHOULDER_START)):
                with Locations((cls.DESMO_KEY_BOTTOM - cls.DESMO_KEY_BLADE_HEIGHT/2,cls.DESMO_KEY_WIDTH/2)):
                    Rectangle(cls.DESMO_KEY_BLADE_HEIGHT+5.0*MM, cls.DESMO_KEY_WIDTH)
                    add(keyway_face, mode = Mode.SUBTRACT)      
            extrude(amount = 50*MM, mode = Mode.SUBTRACT)
        return Part(desmo_blank.part)

    @classmethod
    def cut_definition(cls) -> str:
        return "Key cuts are defined from highest to lowest as 1 through 6, all right side cuts come before all left side cuts."

    @classmethod
    def key(cls, profile: str, keyway: str, cuts: str) -> Part:
        if len(cuts) % 2 != 0:
            raise ValueError("Number of cuts must be even")
        match profile:
            case "desmo_6pin":
                if len(cuts) > 6:
                    raise ValueError("6 pin profile only supports 6 cuts")
            case "desmo_8pin":
                if len(cuts) > 8:
                    raise ValueError("8 pin profile only supports 8 cuts")
            case "desmo_10pin":
                if len(cuts) > 6:
                    raise ValueError("10 pin profile only supports 10 cuts")


        desmo_blank = cls.blank(profile, keyway)
                
        right_track = [(0.0, 0.0)] * 18
        left_track =  [(0.0, 0.0)] * 18
        
        right_cuts = cuts[:int(len(cuts)/2)]
        left_cuts = cuts[int(len(cuts)/2):]

        def calculate_tracks(track: list[tuple[float,float]], cuts : str):
            for i, cut in enumerate(cuts):
                depth_index = int(cut) - 1
                # We must skip past the key retention spot located at index 2
                cut_index = i if i < 2 else i + 1

                cut_x = cls.DESMO_CUT_SPACINGS[cut_index]
                cut_x += cls.DESMO_KEY_SHOULDER_START

                cut_y = cls.DESMO_KEY_BOTTOM
                cut_y -= cls.DESMO_CUT_DEPTHS[depth_index] + cls.DESMO_PIN_HEIGHT / 2 # Cuts are "centered" in the track, measurements were taken to the bottom of track

                # The cut height for the notch appears to match the next cut on ASSA cut keys
                if i == 2:
                    track[4] = (cls.DESMO_KEY_SHOULDER_START + cls.DESMO_CUT_SPACINGS[2] - cls.DESMO_PIN_DIAMETER / 2, cut_y)
                    track[5] = (cls.DESMO_KEY_SHOULDER_START + cls.DESMO_CUT_SPACINGS[2] + cls.DESMO_PIN_DIAMETER / 2, cut_y)

                track[cut_index*2] = (cut_x - cls.DESMO_PIN_DIAMETER / 2, cut_y)
                track[cut_index*2+1] = (cut_x + cls.DESMO_PIN_DIAMETER / 2, cut_y)

                # Extend the cut out to the tip.. Different pin count Desmos do this differently, but this is practical
                if i == len(cuts)-1:
                    while cut_index < 8:
                        cut_index += 1
                        track[cut_index*2] = (cls.DESMO_CUT_SPACINGS[cut_index] + cls.DESMO_KEY_SHOULDER_START - cls.DESMO_PIN_DIAMETER / 2, cut_y)
                        track[cut_index*2+1] = (cls.DESMO_CUT_SPACINGS[cut_index] + cls.DESMO_KEY_SHOULDER_START  + cls.DESMO_PIN_DIAMETER / 2, cut_y)
        
        calculate_tracks(right_track, right_cuts)
        calculate_tracks(left_track, left_cuts)

        def build_track(track_points: list[tuple[float,float]], z_height: float) -> Part:
            with BuildPart() as track:
                with BuildPart(Plane.XZ.offset(-track_points[0][1])):
                    with Locations((track_points[0][0], z_height)):
                        Cylinder(cls.DESMO_PIN_DIAMETER / 2 + cls.DESMO_TRACK_TOLERANCE / 2, cls.DESMO_PIN_HEIGHT) 

                for v_0, v_1 in zip(track_points[0:-2], track_points[1:]):
                    if v_0[1] != v_1[1]:
                        # Angle cut

                        # Slope used for adjustments
                        s = (v_1[1] - v_0[1]) / (v_1[0] - v_0[0])
                        ramp_up = s < 0

                        # On a real key, this is just a sweep of the pin across the track
                        # On this design, it uses maximal fitting ramps so that a 3D printed key works too
                        # This can make the ramps look quite gnarly, but it generates working keys for all bittings

                        v0b = [0, 0, z_height] # current pin bottom center
                        v0t = [0, 0, z_height] # current pin top center
                        v1b = [0, 0, z_height] # next pin bottom center
                        v1t = [0, 0, z_height] # next pin top center     

                        if ramp_up:
                            v0b[0] = v_0[0] - cls.DESMO_PIN_DIAMETER / 2
                            v0b[1] = v_0[1] + cls.DESMO_PIN_HEIGHT / 2
                            v0t[0] = v_0[0]
                            v0t[1] = v_0[1] - cls.DESMO_PIN_HEIGHT / 2
                            v1b[0] = v_1[0] 
                            v1b[1] = v_1[1] + cls.DESMO_PIN_HEIGHT / 2
                            v1t[0] = v_1[0] + cls.DESMO_PIN_DIAMETER / 2
                            v1t[1] = v_1[1] - cls.DESMO_PIN_HEIGHT / 2

                            b_slope = (v1b[1] - v0b[1]) / (v1b[0] - v0b[0])
                            v1b[0] -= (cls.DESMO_PIN_HEIGHT / 2) / b_slope
                            v1b[1] -= cls.DESMO_PIN_HEIGHT / 2
                            v0t[0] += (cls.DESMO_PIN_HEIGHT / 2) / b_slope
                            v0t[1] += cls.DESMO_PIN_HEIGHT / 2
                        else:
                            v0b[0] = v_0[0]
                            v0b[1] = v_0[1] + cls.DESMO_PIN_HEIGHT / 2
                            v0t[0] = v_0[0] - cls.DESMO_PIN_DIAMETER / 2
                            v0t[1] = v_0[1] - cls.DESMO_PIN_HEIGHT / 2
                            v1b[0] = v_1[0] + cls.DESMO_PIN_DIAMETER / 2
                            v1b[1] = v_1[1] + cls.DESMO_PIN_HEIGHT / 2
                            v1t[0] = v_1[0]
                            v1t[1] = v_1[1] - cls.DESMO_PIN_HEIGHT / 2

                            b_slope = (v1b[1] - v0b[1]) / (v1b[0] - v0b[0])
                            v0b[0] -= (cls.DESMO_PIN_HEIGHT / 2) / b_slope
                            v0b[1] -= cls.DESMO_PIN_HEIGHT / 2
                            v1t[0] += (cls.DESMO_PIN_HEIGHT / 2) / b_slope
                            v1t[1] += cls.DESMO_PIN_HEIGHT / 2

                        
                        with BuildSketch(Plane.XZ.offset(-v0b[1])):
                            with Locations((v0b[0], z_height)):
                                Circle(cls.DESMO_PIN_DIAMETER / 2 + cls.DESMO_TRACK_TOLERANCE / 2)
                        with BuildLine() as b:
                            Line(Vertex(v0b), Vertex(v1b))
                        sweep()
                        with BuildSketch(Plane.XZ.offset(-v0t[1])):
                            with Locations((v0t[0], z_height)):
                                Circle(cls.DESMO_PIN_DIAMETER / 2 + cls.DESMO_TRACK_TOLERANCE / 2)
                        with BuildLine() as t:
                            Line(Vertex(v0t), Vertex(v1t))
                        sweep()
                    else:
                        # Straight cut
                        with BuildSketch(Plane.YZ.offset(v_0[0])):
                            with Locations((v_0[1], z_height)):
                                Rectangle(cls.DESMO_PIN_HEIGHT, cls.DESMO_PIN_DIAMETER + cls.DESMO_TRACK_TOLERANCE)
                        with BuildLine():
                            Line(v_0, v_1)
                        sweep()        
            return Part(track.part)
        
        with BuildPart() as desmo_key:
            add(desmo_blank)
            add(build_track(right_track, -0.75*MM), mode = Mode.SUBTRACT)
            add(build_track(left_track, cls.DESMO_KEY_WIDTH + 0.75*MM), mode = Mode.SUBTRACT)

            # The tip cut on Desmo follows the tip and goes all the way to the track equally
            tip_x = 55*MM
            match profile:
                case "desmo_8pin":
                    tip_x = 51.5*MM
                case "desmo_6pin":
                    tip_x = 48*MM

            tip_edges = desmo_blank.edges().filter_by_position(Axis.X, tip_x, 100)
            tip_edges = tip_edges.group_by(Axis.Z)[0] + tip_edges.group_by(Axis.Z)[-1]

            with BuildPart(mode = Mode.SUBTRACT) as tip_snip:
                for tip_edge in tip_edges:
                    v_0 = tip_edge.vertices()[0]
                    v_1 = tip_edge.vertices()[1]

                    v_0n = [float(v_0.X),float(v_0.Y),float(v_0.Z)]
                    v_1n = [float(v_1.X),float(v_1.Y),float(v_1.Z)]

                    is_left = True if v_0.Z > cls.DESMO_KEY_WIDTH else False
                    z_off = 0.375*MM if is_left else -0.375*MM
                           
                    if v_0n[1] > cls.DESMO_KEY_TOP and v_0n[1] < cls.DESMO_KEY_BOTTOM:
                        v_0n[1] = left_track[-1][1] if is_left else right_track[-1][1]
                        v_1n[0] += cls.DESMO_PIN_DIAMETER

                    if v_1n[1] > cls.DESMO_KEY_TOP and v_1n[1] < cls.DESMO_KEY_BOTTOM:
                        v_1n[1] = left_track[-1][1] if is_left else right_track[-1][1]
                        v_0n[0] += cls.DESMO_PIN_DIAMETER
                                       
                    with BuildSketch(Plane.XZ.offset(-v_0n[1])):
                        with Locations((v_0n[0], v_0n[2] + z_off)):
                            Ellipse(x_radius = cls.DESMO_PIN_DIAMETER*3/2, y_radius = cls.DESMO_PIN_DIAMETER/2)
                    with BuildLine() as test_line:
                        Line(Vertex(v_0n), Vertex(v_1n))
                    sweep()

            with BuildLine(Plane.XY.offset(cls.DESMO_KEY_WIDTH)) as left_track_cut:
                Polyline(left_track)
            with BuildLine(Plane.XY) as right_track_cut:
                Polyline(right_track)
            with BuildLine(Plane.XY) as spacing:
                for key_cut in cls.DESMO_CUT_SPACINGS:
                    Line((cls.DESMO_KEY_SHOULDER_START + key_cut,0),(cls.DESMO_KEY_SHOULDER_START + key_cut,40))
            show_object(left_track_cut)
            show_object(right_track_cut)
            show_object(spacing)
            show_object(desmo_key)
            
        return Part(desmo_key.part)
 

if __name__ == '__main__':
    from ocp_vscode import *
    #desmo_blank = Desmo.blank("desmo_8pin", "desmo")
    desmo_key = Desmo.key("desmo_8pin", "desmo", "24421322")
    #desmo_key = Desmo.key("desmo_6pin", "desmo", "632145")
    export_step(desmo_key, "desmo_key.step")
    #export_step(desmo_key, "100percentsatisfaction.step")
    #export_step(blank, "desmo_blank.step")
    #show_all()