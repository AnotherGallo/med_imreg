from scipy.fft import fft2, fftshift
from skimage.color import rgb2gray
from skimage.filters import window, difference_of_gaussians
from skimage.transform import warp_polar, rotate, warp, AffineTransform
from skimage.registration import phase_cross_correlation, optical_flow_ilk

from util import *
import time

"""Frequency alignment is based on the following example. 
https://scikit-image.org/docs/stable/auto_examples/registration/plot_register_rotation.html 
We first estimate the rotation between two images, apply it and then use the average optical flow to get the 
displacement between the images"""


def get_shifted_fft(im, low_sig=5, high_sig=10):
    """
    Computes the shifted FFT of an input image. For that purpose it first applies a bandpass filter via difference of
    Gaussians.
    :param im: Image to get the shifted FFT of.
    :param low_sig: The smaller sigma value for the bandpass filter.
    :param high_sig: The larger sigma value for the bandpass filter.
    :return: Shifted FFT of the input image.
    """
    bp_im = difference_of_gaussians(im, low_sig, high_sig)
    w_im = bp_im * window('hann', im.shape)
    return np.abs(fftshift(fft2(w_im)))


def run(im, reference):
    print(f'Starting alignment...')
    start = time.time()

    transform = compute_transform(im, reference)

    # Apply computed transformation to the original images
    shifted_back = rotate(im, transform["rotation"].rotation, clip=True)
    aligned = warp(shifted_back, transform["translation"], mode="constant", preserve_range=False)

    show_ims(reference, im, title="originals")
    show_ims(shifted_back, shifted_back, title="comparison")

    print(f"Aligned in {time.time() - start}s")
    return aligned, transform["scale"]


def compute_transform(im, reference):
    base, rt = crop_to_same_size(reference, im)
    base = rgb2gray(base)
    gray_rt = rgb2gray(rt)
    # Work with shifted FFT magnitudes
    base_fs = get_shifted_fft(base)
    rts_fs = get_shifted_fft(gray_rt)
    shape = base_fs.shape
    radius = shape[0] // 8  # only take lower frequencies
    # Create log-polar transformed FFT mag images and register
    warped_base_fs = warp_polar(base_fs, radius=radius, output_shape=shape, scaling='log', order=0)[:shape[0] // 2,
                     :]  # only use half of FFT
    warped_rts_fs = warp_polar(rts_fs, radius=radius, output_shape=shape, scaling='log', order=0)
    warped_rts_fs = warped_rts_fs[:shape[0] // 2, :]
    shifts, error, phase_diff = phase_cross_correlation(warped_base_fs, warped_rts_fs,
                                                        upsample_factor=10, normalization=None)
    # Use translation parameters to calculate rotation parameters
    shiftr, shiftc = shifts[:2]
    klog = radius / np.log(radius)
    shift_scale = 1 / (np.exp(shiftc / klog))
    recovered_angle = (360 / shape[0]) * shiftr
    # Compute relative displacement by taking average of optical flow along two axis
    shifted_back = rotate(gray_rt, -recovered_angle)
    shift_y, shift_x = np.mean(optical_flow_ilk(base, shifted_back), axis=(1, 2))
    transform = {"rotation": AffineTransform(rotation=-recovered_angle),
                 "translation": AffineTransform(translation=(shift_x, shift_y)),
                 "scale": AffineTransform(scale=shift_scale)}
    print(f"shift x {shift_x}, shift y {shift_y}, rotation {recovered_angle}, scale {shift_scale}")
    return transform


if __name__ == "__main__":
    path = create_dir_dialog()
    run()