from build123d import *

from realkey.Common import key_cutters, key


class SGLever(key.Key):
    SG_CUT_SPACINGS = {
        "87h": [0.167 * IN, 0.222 * IN, 0.271 * IN, 0.319 * IN, 0.378 * IN],
        "87h_45xx": [0.167 * IN, 0.222 * IN, 0.271 * IN, 0.319 * IN, 0.367 * IN, 0.415 * IN, 0.470 * IN],
        "9609": [0.167 * IN, 0.222 * IN, 0.271 * IN, 0.319 * IN, 0.378 * IN],
    }
    SG_CUT_WIDTHS = {
        "87h": [0.066 * IN, 0.052 * IN, 0.052 * IN, 0.052 * IN, 0.066 * IN],
        "87h_45xx": [0.066 * IN, 0.052 * IN, 0.052 * IN, 0.052 * IN, 0.052 * IN, 0.052 * IN, 0.066 * IN],
        "9609": [0.066 * IN, 0.052 * IN, 0.052 * IN, 0.052 * IN, 0.066 * IN],
    }
    SG_CUT_DEPTHS = {
        "87h": [i * 0.020 * IN for i in range(8)],
        "87h_45xx": [i * 0.020 * IN for i in range(8)],
        "9609": [i * 0.020 * IN for i in range(8)],
    }

    SG_KEY_WIDTH = {"87h": 0.080 * IN, "87h_45xx": 0.080 * IN, "9609": 0.070 * IN}
    SG_X_DATUM = {"87h": 59.936 * MM, "87h_45xx": 59.936 * MM, "9609": 2.145 * IN}
    SG_Y_DATUM = {"87h": 8.45 * MM, "87h_45xx": 8.45 * MM, "9609": 0.395 * IN}

    SG_THROAT_SPACING = {"87h": 1.0775 * IN, "87h_45xx": 1.0775 * IN, "9609": 1.0775 * IN}
    SG_THROAT_Y_DATUM = {"87h": 8.45 * MM, "87h_45xx": 8.45 * MM, "9609": 0.325 * IN}
    SG_THROAT_DEPTH = {"87h": 0.075 * IN, "87h_45xx": 0.040 * IN, "9609": 0.080 * IN}
    SG_THROAT_WIDTH = {"87h": 0.105 * IN, "87h_45xx": 0.105 * IN, "9609": 0.105 * IN}

    SG_GUARD_TIP_DEPTH = {"87h": 0.188 * IN, "87h_45xx": 0.188 * IN, "9609": 0.193 * IN}

    @classmethod
    def name(cls) -> str:
        return "sg_lever"

    @classmethod
    def display_name(cls) -> str:
        return "S&G Lever"

    @classmethod
    def profiles(cls) -> dict[str, str]:
        return {"87h": "87H", "87h_45xx": "87H (45XX)", "9609": "9609"}

    @classmethod
    def keyways(cls) -> dict[str, str]:
        return {"lever": "Lever"}

    @classmethod
    def basic_bitting_definition(cls) -> str:
        return "Cuts: Amount depends on profile, from 5 to 7.<br>Depths: Maximum Lift 0 to Minimum Lift 7.<br>Example: <i>24622</i>"

    @classmethod
    def advanced_bitting_definition(cls) -> str | None:
        return None

    @classmethod
    def validate_bitting(cls, profile: str, keyway: str, bitting: str):
        if not bitting.isnumeric():
            raise ValueError("Only numeric cuts are allowed")
        if profile in ["87h", "9609"] and len(bitting) > 5:
            raise ValueError(f"S&G {cls.profiles()[profile]} has a maximum of 5 cuts")
        if profile in ["87h_45xx"] and len(bitting) > 7:
            raise ValueError(f"S&G {cls.profiles()[profile]} has a maximum of 7 cuts")

        for cut in bitting:
            if int(cut) < 0 or int(cut) > 7:
                raise ValueError("Cut depths must be from 0 to 7")

    @classmethod
    def blank(cls, profile: str, keyway: str) -> Part:
        blank = None
        if profile == "87h" or profile == "87h_45xx":
            with BuildPart() as step_blank:
                add(import_step("resources/SargentAndGreenleaf/87H.step"))
            blank = step_blank.part
        elif profile == "9609":
            with BuildPart() as step_blank:
                add(import_step("resources/SargentAndGreenleaf/9609.step"))
            blank = step_blank.part
        else:
            raise NotImplementedError("Ha, that profile is not available yet!")
        if blank is None:
            raise ValueError("Issue loading blank")
        return Part(blank)

    @classmethod
    def key(cls, profile: str, keyway: str, bitting: str) -> key_cutters.Part:
        cls.validate_bitting(profile, keyway, bitting)

        sg_blank = cls.blank(profile, keyway)
        spacings = cls.SG_CUT_SPACINGS[profile]
        depths = cls.SG_CUT_DEPTHS[profile]
        widths = cls.SG_CUT_WIDTHS[profile]
        x_datum = cls.SG_X_DATUM[profile]
        y_datum = cls.SG_Y_DATUM[profile]
        throat_spacing = cls.SG_THROAT_SPACING[profile]
        throat_y_datum = cls.SG_THROAT_Y_DATUM[profile]
        throat_depth = cls.SG_THROAT_DEPTH[profile]
        throat_width = cls.SG_THROAT_WIDTH[profile]
        key_width = cls.SG_KEY_WIDTH[profile]

        lever_cuts: list[tuple[float, float, float]] = []
        for i, cut in enumerate(bitting):
            depth_index = int(cut)

            cut_x = x_datum - spacings[i]
            cut_y = y_datum + depths[depth_index]
            lever_cuts.append((cut_x, cut_y, widths[i]))

        # Add throat
        lever_cuts.append((x_datum - throat_spacing, throat_y_datum + throat_depth, throat_width))

        # Tip snip for guard keys
        if profile in cls.SG_GUARD_TIP_DEPTH:
            depth = cls.SG_GUARD_TIP_DEPTH[profile]
            lever_cuts.append((x_datum + 0.2 * IN, y_datum + depth, 0.4 * IN))

        lever_cutter = key_cutters.lever_cutter(lever_cuts, throat_y_datum - 0.001 * MM)

        with BuildPart() as sg_key:
            add(sg_blank)

            with BuildSketch():
                add(lever_cutter)
            extrude(amount=key_width * 2, mode=Mode.SUBTRACT)
        return Part(sg_key.part)


if __name__ == "__main__":
    from ocp_vscode import *

    # blank = SGLever.blank("87h", "lever")
    key = SGLever.key("9609", "lever", "40624")
    show_all()
    # export_step(key, "guard_key.step")
