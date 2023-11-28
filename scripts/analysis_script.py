#@ ij.ImagePlus image
#@ String path
#@ String suffix
#@ output String csv_path

from ij import IJ
from ij.measure import ResultsTable
import os

print("Analyzing...")
csv_path = os.path.join(path, image.getTitle() + suffix + ".csv")
print(csv_path)

fields = ["area", "center"]
IJ.run("Set Measurements...",
           "{0} decimal=3".format(" ".join(fields)))
IJ.run(image, "Analyze Particles...", "size=100-3000 display clear include overlay stack")

table = ResultsTable.getActiveTable()
print("Saving table: " + csv_path)
table.save(csv_path)
print("Finished analyzing {0}.".format(image.getTitle()))