from os import listdir, getcwd, stat
from os.path import isfile, join
from pprint import pprint as pp
from collections import namedtuple
from time import perf_counter as pc
import cv2 as cv
print("CWD = ", getcwd())

# Import and time
t0 = pc()
import face_recognition as fr
print(f"{(pc() - t0)*1000:.0f}ms: Imported face_recognition")

# Get list of file paths for knowns
known_folder = "test-data\\known\\"
files = [join(known_folder, f) for f in listdir(known_folder) if isfile(join(known_folder, f))]

# Encode known people
KnownPerson = namedtuple("KnownPerson", "Name SamplePath Encoding")
KnownPeople = []
for file in files:
    known_image = fr.load_image_file(file)
    known_encoding = fr.face_encodings(known_image, num_jitters=5, model="large")[0]
    name = file.split("\\")[-1][0:-4]   # Just the file name, sans extension
    KnownPeople.append(KnownPerson(name, file, known_encoding))

print(f"Found {len(KnownPeople)} people in {known_folder}:")
pp([f"{kp.Name} in {kp.SamplePath}" for kp in KnownPeople])

# Get list of file paths for unknowns
search_path = "test-data\\unknown\\"
files = [join(search_path, f) for f in listdir(search_path) if isfile(join(search_path, f))]
print(f"Found {len(files)} unknowns in {search_path}.")

# Track statistics
encoding_generation_times = []
face_compare_times = []
expected_counts = []
found_counts = []
false_positive_counts = []
false_negative_counts = []
image_success_percent = [] # List of images and the percent of expected faces found

# Iterate through list of unknowns
for file in files:
    image = cv.imread(file, cv.IMREAD_COLOR)

    # Resize image if necessary
    scale_factor = 1000 / image.shape[1]
    resized = cv.resize(image, None, fx=scale_factor, fy=scale_factor)

    # Recognize faces using face_recognition
    t0 = pc()
    faces = fr.face_encodings(resized)
    encoding_generation_times.append(pc()-t0)

    # Determine expected results
    expected_people = [x for x in KnownPeople if x.Name in file]

    # Track actual results
    found_people = []

    # Actual facial recognition logic
    for face in faces:
        t1 = pc()

        # TODO: Modify this to look through all faces, compute distances, and choose the best match
        compare_results = fr.compare_faces([x.Encoding for x in KnownPeople], face, tolerance=.6)
        face_compare_times.append(pc()-t1)

        # Check this image to see if it contains any known faces
        for i in range(len(compare_results)):
            if compare_results[i]:
                found_people.append(KnownPeople[i])

    # Compare actual and expected results
    false_positives = [x for x in found_people if x not in expected_people]
    false_positive_counts.append(len(false_positives))
    false_negatives = [x for x in expected_people if x not in found_people]
    false_negative_counts.append(len(false_negatives))
    found_counts.append(len(found_people))
    expected_counts.append(len(expected_people))

    print(f" - {file} - ")
    if len(found_people) > 0:
        print(f"\t   Found {', '.join([x.Name for x in found_people])}")
        print(f"\tExpected {', '.join([x.Name for x in expected_people])}")
        print(f"\tF+: {len(false_positives):2} F-: {len(false_negatives)}")
    else:
        print(f"\tNo match for known image in {file} ({pc()-t0:.1f}s, {stat(file).st_size/1024:3,.0f}KB)")
    print()
print()
print(" ==== Face recognition complete! ====")
print(" - Statistics - ")

print(f"Encoding generation: {sum(encoding_generation_times)}, avg {sum(encoding_generation_times)/len(encoding_generation_times):.2}s, max {max(encoding_generation_times):.2}")
print(f"       Face compare: {sum(face_compare_times):3}s, avg {sum(face_compare_times)/len(face_compare_times)*1000:0}ms, max {max(face_compare_times)*1000:0}ms")
print(f"     Expected faces: {sum(expected_counts)}, avg {sum(expected_counts)/max(len(expected_counts),1):.2}, max {max(expected_counts)}")
print(f"        Found faces: {sum(found_counts)}, avg {sum(found_counts)/max(len(found_counts),1):.2}, max {max(found_counts)}")
success_percents = [found_counts[i]/expected_counts[i] for i in range(len(files)) if expected_counts[i] > 0]
print(f"          Success %: avg {sum(success_percents)/len(success_percents)*100:.1}%")
if len(false_positive_counts) > 0:
    print(f"    False positives: {sum(false_positive_counts)}, avg {sum(false_positive_counts)/len(false_positive_counts):.2}, max {max(false_positive_counts)}")
else:
    print("     False positives: 0")
if len(false_negative_counts) > 0:
    print(f"    False negatives: {sum(false_negative_counts)}, avg {sum(false_negative_counts)/len(false_negative_counts):.2}, max {max(false_negative_counts)}")
else:
    print("     False negatives: 0")

