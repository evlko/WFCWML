from enum import Enum, auto

import matplotlib.pyplot as plt

from project.utils.utils import Utils
from project.visualization.renderer import Renderer
from project.wfc.grid import Grid
from project.wfc.pattern import MetaPattern


class TextToShow(Enum):
    NONE = auto()
    ENTROPY = auto()
    HEIGHT = auto()


class GridRenderer(Renderer):
    offset = 0.15

    def draw(
        self,
        grid: Grid,
        title: str = None,
        show_borders: bool = False,
        seed: int | None = 42,
        show: bool = True,
        save_path: str | None = None,
        text_to_show: TextToShow = TextToShow.NONE,
        show_image: bool = True,
    ) -> None:
        """Draw the grid using images for the patterns."""
        fig, ax = plt.subplots(
            grid.height,
            grid.width,
            figsize=(grid.width, grid.height),
        )

        if title:
            fig.suptitle(title)

        for x, y, meta_pattern in grid.iter_cells():
            cell_ax = ax[x, y]
            text = None
            image = None
            background_color = None
            text_color = "black"
            meta_pattern: MetaPattern | None = grid.grid[x, y]

            if text_to_show == TextToShow.ENTROPY:
                text = str(grid.entropy[x, y])
                if text == "0":
                    text_color = "white"
                    background_color = "red"
            if meta_pattern and text_to_show == TextToShow.HEIGHT:
                text = str(meta_pattern.is_walkable)
                background_color = "white" if text == "1" else "black"
                text_color = "black" if text == "1" else "white"
            if meta_pattern and show_image:
                custom_seed = (lambda s: s + x * 100 + y + y**2 if s else None)(seed)
                pattern = Utils.weighted_choice(meta_pattern.patterns, seed=custom_seed)
                image = pattern.image_path

            self.render_cell(
                image_path=image,
                text=text,
                ax=cell_ax,
                axis=show_borders,
                text_color=text_color,
                background_color=background_color,
            )

        plt.subplots_adjust(
            left=self.offset,
            right=1 - self.offset,
            bottom=self.offset,
            top=1 - self.offset,
            hspace=0,
            wspace=0,
        )

        if save_path:
            plt.savefig(save_path, bbox_inches="tight", pad_inches=0)
        if show:
            plt.show()
        plt.close()


grid_renderer = GridRenderer()
