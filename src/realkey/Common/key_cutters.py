from build123d import *
import math


def hpc_cw1011():
    tip_width = 0.044 * IN
    cutter_width = 0.25 * IN
    cutter_height = 2.375 * IN / 2
    angle = 90

    a = tip_width / 2
    b = cutter_width / 2
    c = b * math.tan(math.radians(angle / 2))

    cutter_points = [(-a, -cutter_height), (a, -cutter_height), (b, c - cutter_height), (b, 0), (-b, 0), (-b, c - cutter_height), (-a, -cutter_height)]

    with BuildPart() as hpc_cw1011:
        with BuildSketch():
            with BuildLine():
                Polyline(cutter_points)
            make_face()
        revolve(axis=Axis.X)
    if hpc_cw1011.part is None:
        return None
    hpc_cw1011.part.locate(Location((0, cutter_height)))
    return hpc_cw1011.part


def angled_cutter(cuts: list[tuple[float, float]], min_cut_width: float, neutral_y: float, angle: float):
    """Generates a specialized cutter with a fixed angle. The angled cut is placed halfway between two adjacent cuts.

    Args:
        cuts (list[tuple[float, float]]): A list of cut centers, specified as (x, y)
        min_cut_width (float): The minimum width a cut should be, used to validate if the cuts are possible
        neutral_y (float): The default neutral position for ramp in and ramp out, typically the Y value of the top of the key with a little cushion to close the shape.
        angle (float): The desired angle of all cuts, defined as the angle between the ramps and a the bottom of the bitting
    """
    cut_slope = math.tan(math.radians(angle))
    half_min_width = min_cut_width / 2

    cut_points: list[tuple[float, float]] = []

    # calculate leading angled cut
    c0_y = cuts[0][1]
    dy = c0_y - neutral_y
    dx = abs(dy / cut_slope)
    cut_points.append((cuts[0][0] - half_min_width - dx, neutral_y))

    def append_segment(p: list[tuple[float, float]], x: float, y: float):
        p.append((x - half_min_width, y))
        p.append((x + half_min_width, y))

    # iterates (c0,c1),(c1,c2),(c2,c3), etc..
    for (c0x, c0y), (c1x, c1y) in zip(cuts[0:-1], cuts[1:]):
        # first make a segment for the c0 cut
        append_segment(cut_points, c0x, c0y)

        intercut_change = c1y - c0y
        if intercut_change != 0:
            intercut_space = c1x - c0x - min_cut_width
            intercut_midpoint = (c1x - c0x) / 2
            angled_cut_space = abs(intercut_change / cut_slope)

            if angled_cut_space > intercut_space:
                raise ValueError(f"Unable to make angled cut. [Space required = {angled_cut_space}, available = {intercut_space}]")

            c_0ax = c0x + (intercut_midpoint - angled_cut_space / 2)
            c_1ax = c0x + (intercut_midpoint + angled_cut_space / 2)

            cut_points.append((c_0ax, c0y))
            cut_points.append((c_1ax, c1y))

        # add segment for c1 cut
        append_segment(cut_points, c1x, c1y)

    # calculate trailing angled cut
    cl_y = cuts[-1][1]
    dy = cl_y - neutral_y
    dx = abs(dy / cut_slope)
    cut_points.append((cuts[-1][0] + dx + half_min_width, neutral_y))

    with BuildSketch() as cutter:
        with BuildLine():
            Polyline(cut_points)
        make_face()
    return cutter.sketch


def angled_cutter_with_widths(cuts: list[tuple[float, float]], min_cut_widths: list[float], neutral_y: float, angle: float):
    """Generates a specialized cutter with a fixed angle. The angled cut is placed halfway between two adjacent cuts.

    Args:
        cuts (list[tuple[float, float]]): A list of cut centers, specified as (x, y)
        min_cut_widths (list[float]): The minimum width a cut should be, used to validate if the cuts are possible
        neutral_y (float): The default neutral position for ramp in and ramp out, typically the Y value of the top of the key with a little cushion to close the shape.
        angle (float): The desired angle of all cuts, defined as the angle between the ramps and a the bottom of the bitting
    """
    if len(cuts) != len(min_cut_widths):
        raise ValueError("Angled cutter widths not the same length as cuts")

    cut_slope = math.tan(math.radians(angle))
    cut_points: list[tuple[float, float]] = []

    # calculate leading angled cut
    half_min_width = min_cut_widths[0] / 2
    c0_y = cuts[0][1]
    dy = c0_y - neutral_y
    dx = abs(dy / cut_slope)
    cut_points.append((cuts[0][0] - half_min_width - dx, neutral_y))

    def append_segment(p: list[tuple[float, float]], x: float, y: float, width: float):
        p.append((x - width / 2, y))
        p.append((x + width / 2, y))

    # iterates (c0,c1),(c1,c2),(c2,c3), etc..
    i = 0
    for (c0x, c0y), (c1x, c1y) in zip(cuts[0:-1], cuts[1:]):
        min_width = min_cut_widths[i]

        # first make a segment for the c0 cut
        append_segment(cut_points, c0x, c0y, min_width)

        intercut_change = c1y - c0y
        if intercut_change != 0:
            intercut_space = c1x - c0x - min_width / 2
            intercut_midpoint = (c1x - c0x) / 2
            angled_cut_space = abs(intercut_change / cut_slope)

            if angled_cut_space > intercut_space:
                raise ValueError(f"Unable to make angled cut. [Cut {i}, Space required = {angled_cut_space}, available = {intercut_space}, min = {min_width}]")

            c_0ax = c0x + (intercut_midpoint - angled_cut_space / 2)
            c_1ax = c0x + (intercut_midpoint + angled_cut_space / 2)

            cut_points.append((c_0ax, c0y))
            cut_points.append((c_1ax, c1y))

        # add segment for c1 cut
        append_segment(cut_points, c1x, c1y, min_width)
        i += 1

    print(cuts)
    print(cut_points)
    # calculate trailing angled cut
    half_min_width = min_cut_widths[-1] / 2
    cl_y = cuts[-1][1]
    dy = cl_y - neutral_y
    dx = abs(dy / cut_slope)
    cut_points.append((cuts[-1][0] + dx + half_min_width, neutral_y))

    with BuildSketch() as cutter:
        with BuildLine():
            Polyline(cut_points)
        make_face()
    return cutter.sketch
