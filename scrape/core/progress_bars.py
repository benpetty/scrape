import enlighten


class ProgressBars:
    def __init__(self):
        self.manager = enlighten.get_manager()

    def get_bar_formats(self, key: str = "default"):
        std_bar_format = (
            "{desc}{desc_pad}{percentage:3.0f}%|{bar}| "
            + "{count:{len_total}d}/{total:d} "
            + "[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]"
        )
        bar_formats = {
            "default": self.manager.term.red(std_bar_format),
            "red_text": self.manager.term.red(std_bar_format),
            "red_on_white": self.manager.term.red_on_white(std_bar_format),
            "x11_colors": self.manager.term.peru_on_seagreen(std_bar_format),
            "rbg_text": self.manager.term.color_rgb(2, 5, 128)(std_bar_format),
            "rbg_background": self.manager.term.on_color_rgb(255, 190, 195)(
                std_bar_format
            ),
        }
        return bar_formats.get(key, bar_formats.get("default"))
