# @ ij.ImagePlus[] images
# @OUTPUT ij.ImagePlus[] results

from ij import IJ, plugin
from ij import gui
import ij.WindowManager as WM

import sys
import time

IM_PREFIX = "pps"

def deconvolve_channels(im):
    IJ.run(im, "Colour Deconvolution", "vectors=H&E hide")
    channels = []
    for i in range(0, 3):
        title = im.getTitle() + "-(Colour_{0})".format(i + 1)
        ch = WM.getImage(title)
        ch.setTitle("{0}_".format(IM_PREFIX) + title)
        channels.append(ch)
    return channels


def pairwise_add(im_title):
    ims = [WM.getImage("{0}_".format(IM_PREFIX) + im_title + "-(Colour_{0})".format(x)) for x in range(1, 4)]

    results = []
    for i in range(3):
        # print("Adding images {0} and {1}".format(ims[i].title, ims[(i + 1) % 3].title))
        mix = plugin.ImageCalculator.run(ims[i], ims[(i + 1) % 3], "Add create")
        results.append(mix)

        mix.setTitle("{0}_sum of ch{1} ch{2}".format(IM_PREFIX, i, (i + 1) % 3))
        mix.show()

    return results


def boost_contrast(im):
    IJ.setMinAndMax(im, 240, 255)


def threshold(im, lower=254, upper=255):
    IJ.setRawThreshold(im, lower, upper, "Black & White")
    IJ.run(im, "Convert to Mask", "")
    IJ.run(im, "Invert", "")


def erode_dilate(im, iters, count, operation):
    ops = {"e": "Erod", "d": "Dilat"}

    if operation not in ops: return
    op = ops[operation]

    # print("{0}ing '{1}' [iters:{2}, count:{3}]".format(op, im.title, iters, count))
    IJ.run(
        im, "Options...", "iterations={0} count={1} black do={2}e".format(iters, count, op))


def breakpoint(msg="Breakpoint"):
    ync = gui.YesNoCancelDialog(None, "Breakpoint", msg)
    confirmed = ync.yesPressed()
    if not confirmed:
        sys.exit()


def create_mask(channels, title=""):
    for ch in channels:
        boost_contrast(ch)
        threshold(ch)
    mask = plugin.ImageCalculator.run(channels[0], channels[1], "Add create")
    erode_dilate(mask, 2, 1, "d")
    IJ.run(mask, "Fill Holes", "")
    mask.setTitle("{0}_mask ".format(IM_PREFIX) + title)
    return mask


def low_thresh(channels, title=""):
    blue = channels[0]
    blue.setTitle("{0}_Low_t ".format(IM_PREFIX) + title)
    threshold(blue, 148, 255)
    IJ.run(blue, "Invert", "")
    return blue


def pipeline(ims):
    start = time.time()

    # takes separate RGB channels and combines them into a single RGB image
    for i, im in enumerate(ims):
        title = "im {0}".format(i)
        im.setTitle(title)
        im.show()
        IJ.run("Stack to RGB")
        im.hide()
        ims[i] = WM.getImage(title + " (RGB)")

    results = []
    for im in ims:
        # deconvolve and pairwise add channels
        channels = deconvolve_channels(im)
        ch_copy = [ch.duplicate() for ch in channels]
        sums = pairwise_add(im.getTitle())
        IJ.run("Tile", "")

        # create mask
        mask = create_mask(sums, im.getTitle())
        mask.show()

        # create low threshold mask
        low_t = low_thresh(ch_copy, im.getTitle())
        low_t.show()

        # create final product
        result = plugin.ImageCalculator.run(low_t, mask, "Multiply create")
        result.setTitle("result " + im.getTitle())
        result.show()
        IJ.run(result, "Fill Holes", "")
        IJ.run(result, "Remove Outliers...", "radius=2 threshold=50 which=Bright")
        results.append(result)

        # close all unnecessary windows
        for title in WM.getImageTitles():
            if IM_PREFIX in title:
                img = WM.getImage(title)
                img.changes = False
                img.close()

    print("Pipeline finished in {0}s".format(time.time() - start))
    return results


### CLEAN UP PREVIOUS SESSION ###
def cleanup():
    confirmed = False
    for imgTitle in WM.getImageTitles():
        if not confirmed:
            caution_msg = "You are about to close all open images. Proceed?"
            ync = gui.YesNoCancelDialog(None, "Warning", caution_msg)
            confirmed = ync.yesPressed()
            if not confirmed:
                break
        img = WM.getImage(imgTitle)
        img.changes = False
        img.close()
    for title in WM.getImageTitles():
        print("Failed to close {0}".format(title))

    print("finished clean up")


if __name__ == '__main__':
    cleanup()

    ### PROCESS IMAGES ###
    results = None
    if len(images) >= 1:
        results = pipeline(images)

    for i, result in enumerate(results):
        result.setRoi(None)
        result.show()

    print("Process finished.")
