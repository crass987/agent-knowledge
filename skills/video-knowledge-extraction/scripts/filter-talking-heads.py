#!/usr/bin/env python3
"""Filter talking head frames from keyframes directory.

Uses OpenCV face detection to classify frames as CONTENT or TALKING_HEAD.
Outputs only CONTENT frames to stdout (one per line).
Optionally deletes TALKING_HEAD files with --delete flag.

Usage:
    python3 filter-talking-heads.py keyframes/ [--delete] [--verbose]
"""
import cv2
import sys
import os

FACE_CASCADE = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
PROFILE_CASCADE = cv2.data.haarcascades + 'haarcascade_profileface.xml'


def has_face(image_path):
    """Detect if image contains a face (frontal or profile)."""
    img = cv2.imread(image_path)
    if img is None:
        return False
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    face_cascade = cv2.CascadeClassifier(FACE_CASCADE)
    profile_cascade = cv2.CascadeClassifier(PROFILE_CASCADE)

    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))
    profiles = profile_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))

    return len(faces) > 0 or len(profiles) > 0


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    keyframes_dir = sys.argv[1]
    delete_mode = '--delete' in sys.argv
    verbose = '--verbose' in sys.argv

    if not os.path.isdir(keyframes_dir):
        print(f"Error: {keyframes_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    face_cascade_path = FACE_CASCADE
    if not os.path.exists(face_cascade_path):
        print("Error: OpenCV haarcascade not found", file=sys.stderr)
        sys.exit(1)

    files = sorted(f for f in os.listdir(keyframes_dir) if f.endswith(('.png', '.jpg', '.jpeg')))
    content_count = 0
    head_count = 0

    for f in files:
        path = os.path.join(keyframes_dir, f)
        if has_face(path):
            head_count += 1
            if verbose:
                print(f"TALKING_HEAD: {f}", file=sys.stderr)
            if delete_mode:
                os.remove(path)
        else:
            content_count += 1
            print(f)
            if verbose:
                print(f"CONTENT: {f}", file=sys.stderr)

    total = content_count + head_count
    print(f"\n# {content_count}/{total} content frames ({head_count} talking heads filtered)", file=sys.stderr)


if __name__ == '__main__':
    main()
