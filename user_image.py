import os
import numpy as np
from PIL import Image


class UserImage:

    def __init__(self, path: str, is_reference: bool = False):
        self.path = os.path.dirname(path)
        self.title = os.path.basename(path)
        self.is_reference = is_reference
        self._segmented = None
        self._aligned = None
        self.scale_factor = 1

    def __str__(self):
        ref = " (Reference)" if self.is_reference else ""
        return self.path + self.title + ref

    def load_im(self) -> np.array:
        """
        Reads the image data from drive.
        :return: Image data as np.ndarray.
        """
        im = np.asarray(Image.open(os.path.join(self.path,self.title)).convert("RGB"))
        return im

    @property
    def aligned(self):
        # Getter
        if self._aligned is not None:
            pass
        elif self.is_reference:
            self._aligned = self.load_im()
        else:
            try:
                self._aligned = np.asarray(Image.open(self.path + "\\preprocessed\\" + self.title).convert("RGB"))
            except:
                pass

        return self._aligned

    @aligned.setter
    def aligned(self, aligned):
        self._aligned = aligned

    def has_aligned(self):
        return (os.path.isfile(os.path.join(self.path, "preprocessed", self.title))
                or self._aligned is not None or self.is_reference)

    @property
    def segmented(self):
        # Getter
        if self._segmented is None:
            try:
                self._segmented = np.asarray(
                    Image.open(os.path.join(self.path, "preprocessed", self.title))
                    .convert("RGB"))
            except:
                pass
        return self._segmented

    @segmented.setter
    def segmented(self, segmented):
        self._segmented = segmented

    def has_segmented(self):
        return (os.path.isfile(os.path.join(self.path, "results", self.title))
                or self._segmented is not None)
