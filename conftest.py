# pytest runs this file automatically, before it imports any test files.
# app.py creates and seeds its database the moment it is imported, so we
# point FOOD_DB at a throwaway file FIRST. That way the tests never touch
# the real food.db.
import os
import tempfile

test_dir = tempfile.mkdtemp()  # a new empty folder each time pytest runs
os.environ["FOOD_DB"] = os.path.join(test_dir, "test_food.db")
