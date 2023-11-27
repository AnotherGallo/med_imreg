import numpy as np
import tkinter
from tkinter import filedialog
import matplotlib.pyplot as plt
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from user_image import UserImage

import os
from pathlib import Path


def create_dir_dialog() -> str:
    """
    Opens up a directory select dialog.
    :return: Path to selected directory.
    """
    root = tkinter.Tk()
    root.withdraw()

    return filedialog.askdirectory(initialdir="/Users/janlarionow/Desktop/imgs")


def is_valid_dir(usr_path: str) -> bool:
    """
    Checks whether the given path exists and if it exists whether it leads to a directory.
    :param usr_path: Path to be checked.
    :return: True iff the given path is valid given the aforementioned criteria.
    """
    return os.path.exists(usr_path) and os.path.isdir(usr_path)


# def load_im(path: str) -> np.ndarray:
#     """
#     Reads an image under the given path.
#     :param path: String representing the path of the image.
#     :return: Image data as np.ndarray.
#     """
#     im = np.asarray(Image.open(path).convert("RGB"))
#     return im


def get_images(path: str) -> list[UserImage]:
    """
    Returns list containing all images in a directory.
    :param path: Directory containing the images.
    :return: List with images.
    Returns empty list if no images are present or if path doesn't exist or if path isn't a
    directory.
    """

    ims = []
    for root, dirs, files in os.walk(path):
        for file in sorted(files):
            if file.endswith((".png", ".jpg", ".jpeg")):
                im_path = os.path.join(root, file)
                print(f'Loading image {im_path}')
                im, Image.open(im_path)
                im = UserImage(im, im_path)
                ims.append(im)
        break
    return ims


def save_im(im, path: str):
    directory = os.path.dirname(path)
    Path(directory).mkdir(parents=True, exist_ok=True)
    print(f"Saving image {path}")

    im_data = im.aligned
    image = Image.fromarray(im_data)

    meta = PngInfo()
    meta.add_text("ScaleFactor", im.scale_factor)
    image.save(path, pnginfo=meta)


def crop_center(im: np.ndarray, crop_x: int, crop_y: int) -> np.ndarray:
    """
    Creates a cropped view of the specified image with the
    :param im: Image to be cropped.
    :param crop_x: Desired new image width. If larger than the original width, original size will be used.
    :param crop_y: Desired new image height. If larger than the original height, original size will be used.
    :return: Cropped *view* of the original image
    """
    y, x, _ = im.shape
    crop_x = crop_x if crop_x <= x else x
    crop_y = crop_y if crop_y <= y else y
    start_x = x // 2 - (crop_x // 2)
    start_y = y // 2 - (crop_y // 2)
    return im[start_y:start_y + crop_y, start_x:start_x + crop_x, :]


def crop_to_same_size(*ims):
    """
    Crops all input images around their respective center to the size of the smallest image.
    Doesn't create new images but rather views of the originals.
    :param ims: Images to be cropped
    :return: Array of the cropped views.
    """
    dims = [im.shape for im in ims]

    # new height, new width
    nh, nw, _ = np.min(np.array(dims), axis=0)
    cropped = [crop_center(img, nw, nh) for img in ims]

    return cropped


def show_ims(*ims, title: str = "", gray: bool = False):
    """
    Takes in images and plots them in one single result image.
    :param ims: Images to be displayed.
    :param title: Title of the resulting figure.
    :param gray: Set True, if the image is gray-scaled.
    """
    IMS_PER_ROW = 4
    amt_ims = len(ims)
    size_y, size_x = 15 * (amt_ims // IMS_PER_ROW + 1), 10 * min(amt_ims, IMS_PER_ROW)
    f = plt.figure(figsize=(size_x, size_y))

    for i, img in enumerate(ims):
        f.add_subplot(amt_ims // IMS_PER_ROW + 1, min(amt_ims, IMS_PER_ROW), i + 1)
        plt.axis('off')
        if not gray:
            plt.imshow(img)
        else:
            plt.imshow(img, cmap="gray")
        plt.title(title)

    plt.show()


if __name__ == "__main__":
    ims, titles = get_images("C:\\Users\\Jan\\Desktop\\ims")
    res, titles = get_images("C:\\Users\\Jan\\Desktop\\ims\\results")
    show_ims(*ims, title="Test", gray=True)

    x = 23
