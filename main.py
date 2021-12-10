from upload import *

artists_id_list = [2071509, 7501609, 6374004, 265295, 6744566, 9852013, 1424225, 2310735]

auth()
for id in artists_id_list:
    upload(id)