from build123d import *

from realkey.Common import key_cutters, key


class SG44XXGuard(key.Key):
    SG44XX_CUT_SPACINGS = [0.167 * IN, 0.222 * IN, 0.271 * IN, 0.319 * IN, 0.378 * IN]
    SG44XX_CUT_WIDTHS = [0.066 * IN, 0.052 * IN, 0.052 * IN, 0.052 * IN, 0.066 * IN]
    SG44XX_CUT_DEPTHS = [i * 0.020 * IN for i in range(8)]

    SG44XX_KEY_WIDTH = 2 * MM
    SG44XX_X_DATUM = 59.936 * MM  # Tip Stop
    SG44XX_Y_DATUM = 8.45 * MM

    SG44XX_THROAT_SPACING = 1.0775 * IN
    SG44XX_THROAT_DEPTH = 0.075 * IN
    SG44XX_THROAT_WIDTH = 0.105 * IN

    @classmethod
    def name(cls) -> str:
        return "sg_44xx_guard"

    @classmethod
    def display_name(cls) -> str:
        return "S&G 44XX Guard"

    @classmethod
    def profiles(cls) -> dict[str, str]:
        return {"87h": "87H", "9609": "9609 (4443)"}

    @classmethod
    def keyways(cls) -> dict[str, str]:
        return {"lever": "Lever"}

    @classmethod
    def basic_bitting_definition(cls) -> str:
        return "Cuts: Maximum of 5, defined from tip to bow.<br>Depths: Maximum Lift 0 to Minimum Lift 7, factory keys use even cuts only.<br>Example: <i>24622</i>"

    @classmethod
    def advanced_bitting_definition(cls) -> str | None:
        return None

    @classmethod
    def validate_bitting(cls, profile: str, keyway: str, bitting: str):
        if not bitting.isnumeric():
            raise ValueError("Only numeric cuts are allowed")
        if len(bitting) > 5:
            raise ValueError("S&G 44XX Guard has a maximum of 5 cuts")
        for cut in bitting:
            if int(cut) < 0 or int(cut) > 7:
                raise ValueError("Cut depths must be from 0 to 7")

    @classmethod
    def blank(cls, profile: str, keyway: str) -> Part:
        blank = None
        if profile == "87h":
            with BuildPart() as step_blank:
                add(import_step("resources/SargentAndGreenleaf/87H.step"))
            blank = step_blank.part
        else:
            raise NotImplementedError("Ha, that profile is not available yet!")
        if blank is None:
            raise ValueError("Issue loading blank")

        blank = blank.rotate(Axis.Z, 90)
        bbb = blank.bounding_box().min
        blank.position -= bbb

        return Part(blank)

    @classmethod
    def key(cls, profile: str, keyway: str, bitting: str) -> key_cutters.Part:
        cls.validate_bitting(profile, keyway, bitting)

        sg_blank = cls.blank(profile, keyway)

        with BuildPart() as sg_key:
            add(sg_blank)

            with BuildSketch():
                # Throat notch
                with Locations((cls.SG44XX_X_DATUM - cls.SG44XX_THROAT_SPACING, cls.SG44XX_Y_DATUM + cls.SG44XX_THROAT_DEPTH / 2 - 0.001 * MM)):
                    Rectangle(cls.SG44XX_THROAT_WIDTH, cls.SG44XX_THROAT_DEPTH)

                for i, cut in enumerate(bitting):
                    depth_index = int(cut)

                    cut_x = cls.SG44XX_X_DATUM - cls.SG44XX_CUT_SPACINGS[i]
                    cut_depth = cls.SG44XX_CUT_DEPTHS[depth_index]
                    cut_y = cls.SG44XX_Y_DATUM + cut_depth / 2 - 0.001 * MM

                    with Locations((cut_x, cut_y)):
                        Rectangle(cls.SG44XX_CUT_WIDTHS[i], cut_depth + 0.0005 * MM)
            extrude(amount=cls.SG44XX_KEY_WIDTH * 2, mode=Mode.SUBTRACT)
        show_all()
        return Part(sg_key.part)


if __name__ == "__main__":
    from ocp_vscode import *

    # blank = SG44XXGuard.blank("87h", "lever")
    key = SG44XXGuard.key("87h", "lever", "67067")
    # export_step(key, "guard_key.step")
