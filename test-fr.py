from os import listdir, getcwd, stat
from os.path import isfile, join
from pprint import pprint as pp
from collections import namedtuple
from time import perf_counter as pc
print("CWD = ", getcwd())

# Some test files
ki_path = "test-data\\known\\William Lockwood.jpg"
will_uk = "test-data\\unknown\\IMG_20200718_165924.jpg"
will_sub_uk = "test-data\\unknown\\Test subfolder\\will2.jpg"
mushroom = "test-data\\unknown\\IMG_20200718_164509.jpg"
smallpano = "test-data\\unknown\\PANO_20151029_143756.jpg"

# Import and time
t0 = pc()
import face_recognition as fr
print(f"{(pc() - t0)*1000:f}ms: Imported face_recognition")

# Get known person's encoding
known_image = fr.load_image_file(ki_path)
will_encode = fr.face_encodings(known_image)[0]

# Get list of file paths for knowns
known_folder = "test-data\\known\\"
files = [join(known_folder, f) for f in listdir(known_folder) if isfile(join(known_folder, f))]
print(f"Found {len(files)} in {known_folder}:")
pp(files)

KnownPerson = namedtuple("KnownPerson", "Name SamplePath Encoding")
KnownPeople = []
for file in files:
    known_image = fr.load_image_file(file)
    known_encoding = fr.face_encodings(known_image, num_jitters=5, model="large")[0]
    name = file.split("\\")[-1][0:-3]   # Just the file name, sans extension
    KnownPeople.append(KnownPerson(name, file, known_encoding))

# Get list of file paths for unknowns
search_path = "test-data\\unknown\\"
files = [join(search_path, f) for f in listdir(search_path) if isfile(join(search_path, f))]
print(f"Found {len(files)} unknowns in {search_path}.")

# Iterate through list of unknowns
encoding_generation_times = []
face_compare_times = []
for file in files:
    t0 = pc()
    unknown_image = fr.load_image_file(file)
    t1 = pc()
    faces = fr.face_encodings(unknown_image)
    encoding_generation_times.append(pc()-t1)
    found = False
    for face in faces:
        t1 = pc()
        compare_results = fr.compare_faces([x.Encoding for x in KnownPeople], face, tolerance=.6)
        face_compare_times.append(pc()-t1)
        for i in range(len(compare_results)):
            if compare_results[i]:
                print(f"Found '{KnownPeople[i].Name}' in {file} ({pc() - t0:2.1f}s, {stat(file).st_size/1024:3,.0f}KB)")
        if any(compare_results):
            found = True
            break
    if not found:
        print(f"No match for known image in {file} ({pc()-t0:.1f}s, {stat(file).st_size/1024:3,.0f}KB)")

print(f"Encoding generation: avg {sum(encoding_generation_times)/len(encoding_generation_times):.2}s, max {max(encoding_generation_times)}")
print(f"Face compare: avg {sum(face_compare_times)/len(face_compare_times):.2}s, max {max(face_compare_times)}")

