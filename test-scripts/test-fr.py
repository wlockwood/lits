from typing import List
from os import listdir, getcwd, stat
from os.path import isfile, join
from pprint import pprint as pp
from collections import namedtuple
from time import perf_counter as pc

import numpy
from PIL import Image as pilmage

print("CWD = ", getcwd())
TOLERANCE = 0.6  # Lower tolerance requires a closer match
goal_size = 1250  # For resizing images

# Import and time
t0 = pc()
import face_recognition as fr

print(f"{(pc() - t0) * 1000:.0f}ms: Imported face_recognition")

# Get list of file paths for knowns
known_folder = "..\\test-data\\known\\"
files = [join(known_folder, f) for f in listdir(known_folder) if isfile(join(known_folder, f))]

# Encode known people
t0 = pc()
KnownPerson = namedtuple("KnownPerson", "Name SamplePath Encoding")
KnownPeople = []
for file in files:
    known_image = fr.load_image_file(file)
    known_encoding = fr.face_encodings(known_image, num_jitters=5, model="large")[0]
    name = file.split("\\")[-1][0:-4]  # Just the file name, sans extension
    KnownPeople.append(KnownPerson(name, file, known_encoding))
print(f"{(pc() - t0) * 1000:.0f}ms: Encoded known people")

print(f"Found {len(KnownPeople)} people in {known_folder}:")
pp([f"{kp.Name} in {kp.SamplePath}" for kp in KnownPeople])

# Get list of file paths for unknowns
search_path = "../test-data/unknown\\"
files = [join(search_path, f) for f in listdir(search_path) if isfile(join(search_path, f))]
print(f"Found {len(files)} unknowns in {search_path}.")

# Track statistics
encoding_generation_times = []
face_compare_times = []
expected_counts = []
found_counts = []
false_positive_counts = []
false_negative_counts = []

# Iterate through list of unknowns
ComparedFace = namedtuple("ComparedFace", "Person Distance")
ComparedFace.__str__ = lambda self: f"{self.Person.Name} ({self.Distance:.3f})"

for file in files:
    cper = len(found_counts) * 100.0 / len(files)  # Completion percentage
    print(f"{cper:2.0f}% - {file} - ")
    content = pilmage.open(file)

    # Resize image to around 1k pixels

    scale_factor = goal_size / max(content.size[0], content.size[1])
    new_x, new_y = int(round(content.size[0] * scale_factor)), \
                   int(round(content.size[1] * scale_factor))
    resized = content.resize((new_x, new_y))
    as_numpy_arr = numpy.array(resized)

    # Recognize faces using face_recognition
    t0 = pc()
    faces_in_image = fr.face_encodings(as_numpy_arr)
    encoding_generation_times.append(pc() - t0)
    print(f"\tFound {len(faces_in_image)} faces")

    # Determine expected results
    expected_people: List[KnownPerson] = [x for x in KnownPeople if x.Name in file]

    # Track actual results
    found_people: List[KnownPerson] = []

    # Actual facial recognition logic
    for face in faces_in_image:
        t1 = pc()
        compare_results = fr.face_distance([x.Encoding for x in KnownPeople], face)
        face_compare_times.append(pc() - t1)

        # Filter list step by step. I broke this into multiple lines for debugging.
        possible_matches = [ComparedFace(KnownPeople[i], compare_results[i]) for i in range(len(compare_results))]

        # Remove faces that too unlike the face we're checking.
        possible_matches: List[ComparedFace] = [x for x in possible_matches if x.Distance < TOLERANCE]
        print(f"\tBy tolerance, {len(possible_matches)} likely matches: ", ', '.join([str(x) for x in possible_matches]))

        # Removing already-found people
        possible_matches  = [x for x in possible_matches if x.Person not in found_people]
        print(f"\tBy newness, {len(possible_matches)} likely matches: ", ', '.join([str(x) for x in possible_matches]))

        # Sort by chance of facial distance ascending
        possible_matches = sorted(possible_matches, key=lambda x: x.Distance)
        print(f"\tAfter sorting, {len(possible_matches)} likely matches: ", ', '.join([str(x) for x in possible_matches]))

        if len(possible_matches) > 0:
            best_match = possible_matches[0].Person
            print(f"\tBest match: {str(possible_matches[0])}")
            found_people.append([x for x in KnownPeople if x.Name == best_match[0]][0])
            # print(f"Likely matches: ", [x.Name for x in likely_matches])


    # Compare actual and expected results
    false_positives = [x for x in found_people if x not in expected_people]
    false_positive_counts.append(len(false_positives))
    false_negatives = [x for x in expected_people if x not in found_people]
    false_negative_counts.append(len(false_negatives))
    found_counts.append(len(found_people))
    expected_counts.append(len(expected_people))


    if len(found_people) > 0 or len(expected_people) > 0:
        print(f"\t   Found {', '.join([x.Name for x in found_people])}")
        print(f"\tExpected {', '.join([x.Name for x in expected_people])}")
        print(f"\tF+: {len(false_positives):2} F-: {len(false_negatives)}")
    else:
        print("No people found or expected.")
print()
print(" ==== Face recognition complete! ====")
print(f" - Settings: Tolerance = {TOLERANCE}   resize_to = {goal_size}")
print(" - Statistics - ")
print(f"Encoding generation: {sum(encoding_generation_times):,.1f}s, avg {sum(encoding_generation_times) / len(encoding_generation_times):.2}s, max {max(encoding_generation_times):.2}")
print(f"       Face compare: {sum(face_compare_times)*1000:.3f}ms, avg {sum(face_compare_times) / len(face_compare_times) * 1000:.3f}ms, max {max(face_compare_times) * 1000:.3f}ms")
print(f"     Expected faces: {sum(expected_counts)}, avg {sum(expected_counts) / max(len(expected_counts), 1):.2}, max {max(expected_counts)}")
print(f"        Found faces: {sum(found_counts)}, avg {sum(found_counts) / max(len(found_counts), 1):.2}, max {max(found_counts)}")

success_percents = [(100 if expected_counts[i] == 0 and found_counts[i] == 0 else
                     ((found_counts[i]-(false_negative_counts[i]-false_positive_counts[i])/2) * 100.0 / expected_counts[i]))
                    for i in range(len(files)) if expected_counts[i] > 0]
print(f"          Success %: avg {sum(success_percents) / len(success_percents):.1f}%")
if len(false_positive_counts) > 0:
    print(f"    False positives: {sum(false_positive_counts)}, avg {sum(false_positive_counts) / len(false_positive_counts):.2}, max {max(false_positive_counts)}")
else:
    print("     False positives: 0")
if len(false_negative_counts) > 0:
    print(f"    False negatives: {sum(false_negative_counts)}, avg {sum(false_negative_counts) / len(false_negative_counts):.2}, max {max(false_negative_counts)}")
else:
    print("     False negatives: 0")
