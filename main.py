import imagej
from util import *
import frequency_alignment
import numpy as np
import time
import csv
import xarray
from scipy import spatial
from itertools import compress

### GET IMAGES ###
# path = create_dir_dialog()
path = "C:\\Users\\Jan\\Desktop\\ims"
if not is_valid_dir(path):
    print(f"Invalid path '{path}'. Terminating...")
    exit()
ims = get_images(path)
ims[0].is_reference = True
ims[1].has_aligned()

### ALIGN IMAGES ###
unaligned = [im for im in ims if not im.has_aligned()]
if len(unaligned) > 0:
    print(f'Missing alignments ({len(unaligned)} / {len(ims)-1}):')
    for missing in unaligned:
        print(f' - {missing.title}')

    base = next((im for im in ims if im.is_reference))
    base_imdata = base.load_im()
    for missing in unaligned:
        miss_imdata = missing.load_im()
        aligned, scale_diff = frequency_alignment.run(miss_imdata, reference=base_imdata)
        missing.aligned = (aligned*255).astype(np.uint8)
        missing.scale_factor = scale_diff
        save_im(missing.aligned, os.path.join(path, "preprocessed", ims[0].title))

### GET FIJI INSTANCE ###
setup_start = time.time()
ij = imagej.init('sc.fiji:fiji:2.14.0', mode="interactive")
print(f'Init in {time.time() - setup_start}s')

### PROCESS ALIGNED IMAGES ###
with open("scripts/pipeline_script.py") as f:
    script = f.read()
    for im in [im for im in ims if not im.has_segmented()]:
        args = {"images": [im.load_im()]}
        script_output = ij.py.run_script("python", script, args).getOutputs()
        results = script_output["results"]
        pysults = [ij.py.from_java(result) for result in results]
        numsults = [xarray.DataArray.to_numpy(pysult) for pysult in pysults]
        save_im(numsults[0], im.path + "\\results\\" + im.title)


# jaligned = [ij.py.to_imageplus(np.transpose(im, (2, 0, 1))) for im in aligned]
# with open("scripts/pipeline_script.py") as f:
#     script = f.read()
#     args = {"images": jaligned}
#     script_output = ij.py.run_script("python", script, args).getOutputs()
# results = script_output["results"]
# pysults = [ij.py.from_java(result) for result in results]
# numsults = [xarray.DataArray.to_numpy(pysult) for pysult in pysults]
#
# for num, title in zip(numsults, titles):
#     save_im(num, path+"\\results\\"+title)

### ANALYZE IMAGES ###
particles = []
with (open("scripts/analysis_script.py") as f):
    script = f.read()
    for res in results:
        suffix = "_results"
        args = {"image": res, "path": path, "suffix": suffix}
        script_output = ij.py.run_script("python", script, args).getOutputs()
        im_particles = []
        with open(ij.py.from_java(script_output["csv_path"])) as csvfile:
            reader = csv.DictReader(f=csvfile)
            reader.fieldnames[0] = "#"
            for particle in reader:
                im_particles.append([float(particle["XM"]), float(particle["YM"]), int(particle["Area"])])

        particles.append(np.array(im_particles))

print("Analysis complete.")

### FIND MATCHING PARTICLES BASED ON RELATIVE DISTANCE ###
for i in range(len(particles) - 1):
    ref = particles[i]
    comp = particles[i+1]
    distances = spatial.distance.cdist(ref[:, :2], comp[:, :2])
    closest = np.argmin(distances, axis=1)
    for j in range(len(closest)):
        ref_size = ref[j]
    1



# show_ims(*numsults, gray=True)
# py_tables = [ij.py.from_java(table) for table in tables]
print("Main finished.")
