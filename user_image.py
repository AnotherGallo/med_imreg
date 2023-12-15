import os
import numpy as np
from PIL import Image
from pathlib import Path
import pyvips


class UserImage:

    def __init__(self, image, path: str, is_reference: bool = False):
        p = Path(path)
        self.path = path
        """Full path to the image file."""
        self.directory = p.parent
        """Directory of the image file."""
        self.title = p.stem
        """Title of the image file."""
        self.suffix = p.suffix
        """Suffix of the image file with leading dot. (e.g. '.png', '.tiff')"""

        self.image: pyvips.Image = image
        self._scaled_down: pyvips.Image = None
        self.is_reference: bool = is_reference
        """Whether the given UserImage is the reference image which all other images need to be aligned to."""
        self._segmented = None
        self.alignment: dict = {}

    def __str__(self):
        ref = " (Reference)" if self.is_reference else ""
        return self.path + ref

    def load_im(self) -> np.array:
        """
        Reads the image data from drive.
        :return: Image data as np.ndarray.
        """
        im = np.asarray(self.image)
        return im

    @property
    def scaled_down(self) -> pyvips.Image:
        """A scaled down version of original the image. Width is <=5000."""
        if self._scaled_down is None:
            factor = min(5000/self.image.width, 1)
            self._scaled_down = self.image.resize(factor) if factor < 1 else self.image
        return self._scaled_down

    @property
    def segmented(self):
        # Getter
        if self._segmented is None:
            try:
                self._segmented = np.asarray(
                    Image.open(os.path.join(self.directory, "results", self.title + self.suffix))
                    .convert("RGB"))
            except:
                pass
        return self._segmented

    @segmented.setter
    def segmented(self, segmented):
        self._segmented = segmented

    def has_segmented(self):
        return (os.path.isfile(os.path.join(self.directory, "results", self.title + self.suffix))
                or self._segmented is not None)