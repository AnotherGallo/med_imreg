import imagej
from util import *
import frequency_alignment
import numpy as np
import time
import csv
import xarray

### GET IMAGES ###
# Get path from user, exit if invalid
# path = create_dir_dialog()
path = "C:/Users/Jan/Desktop/test_ims/tiffs"
if not is_valid_dir(path):
    print(f"Invalid path '{path}'. Exiting...")
    exit()

# Try loading images, exit if none found
ims = get_images(path)
if not ims:
    print(f'No images found in {path}. Exiting...')
    exit()

# Ask for reference image, exit if none provided
# ref_title = create_file_dialog(path)
ref_title = ims[0].path
if not ref_title:
    print(f'No file chosen. Exiting...')
    exit()

# Catch sudden changes in files contained in directory
tries = 0
while tries < 3:
    if ref_title in [im.path for im in ims]:
        for im in ims:
            if im.path == ref_title:
                im.is_reference = True
                break
        break
    else:
        ims = get_images(path)
        tries += 1

if not any(im.is_reference for im in ims):
    print(f'No reference image found. Exiting...')
    exit()

### GET IMAGE ALIGNMENT PARAMETERS ###
base = next((im for im in ims if im.is_reference))
all_transforms = get_transforms(path, base.title)

# if some images miss alignments relative to the base, compute and append them to dict
unaligned = [im for im in ims if im.path not in all_transforms and not im.is_reference]
if unaligned:
    print(f'Missing alignments ({len(unaligned)} / {len(ims)-1}):')
    for missing in unaligned:
        print(f' - {missing.title}')

    base_imdata = base.scaled_down
    base_imdata = base_imdata.numpy()
    for missing in unaligned:
        miss_imdata = missing.scaled_down
        miss_imdata = miss_imdata.numpy()
        transform, rel_translate = frequency_alignment.run(miss_imdata, reference=base_imdata)

        rx, ry = rel_translate
        shift_y = ry * missing.image.width
        shift_x = rx * missing.image.height


        transform_dict = {'rotation': transform.rotation,
                          'shift x': shift_x,
                          'shift y': shift_y,
                          'scale': transform.scale[0]}
        missing.alignment = transform_dict
        all_transforms[missing.path] = transform_dict

    transforms_to_disk(path, base.title, all_transforms)
else:
    print("Alignment for all images present. Skipping computation, loading from file...\n"
          f"If you want to recompute the alignments, delete {os.path.join(path, base.title)}.json.")

### APPLY ALIGNMENT PARAMETERS ###
# TODO: fix writing to disk of image data
for im in [imm for imm in ims if not imm.is_reference]:
    # Align and write image to disc
    im.alignment = all_transforms[im.path]
    im.aligned = im.image.rotate(-im.alignment["rotation"], idx=im.alignment["shift x"], idy=im.alignment["shift y"])
    im.image.write_to_file(im.path)

### GET FIJI INSTANCE ###
print(f'Loading Fiji...')
setup_start = time.time()
ij = imagej.init('sc.fiji:fiji:2.14.0', mode="interactive")
print(f'Init in {time.time() - setup_start}s')

### PROCESS ALIGNED IMAGES ###
with open("scripts/pipeline_script.py") as f:
    script = f.read()
    for im in [im for im in ims if not im.has_segmented()]:
        args = {"directory": im.directory,
                "title": im.title,
                "suffix": im.suffix}
        script_output = ij.py.run_script("python", script, args).getOutputs()

        results = script_output["results"]
        pysults = [ij.py.from_java(result) for result in results]
        numsults = [xarray.DataArray.to_numpy(pysult) for pysult in pysults]
        im.segmented = numsults[0]

### UNDO TRANSFORMS - RESTORE ORIGINAL IMAGES ###
for im in [imm for imm in ims if not imm.is_reference]:
    target = pyvips.Target.new_to_file(im.path)
    im.image.write_to_target(target, im.suffix)


### ANALYZE IMAGES ###
# TODO: Doesn't work at all yet. Remove break statement to run
particles = []
with (open("scripts/analysis_script.py") as f):
    script = f.read()
    for im in ims:
        break
        suffix = "_results"
        args = {"image": ij.py.to_imageplus(im.segmented),
                "path": im.directory,
                "title": im.title,
                "suffix": suffix}
        script_output = ij.py.run_script("python", script, args).getOutputs()

        im_particles = []
        with open(ij.py.from_java(script_output["csv_path"])) as csvfile:
            reader = csv.DictReader(f=csvfile)
            reader.fieldnames[0] = "#"
            for particle in reader:
                im_particles.append([float(particle["XM"]), float(particle["YM"]), int(particle["Area"])])

        particles.append(np.array(im_particles))

print("Analysis complete.")
