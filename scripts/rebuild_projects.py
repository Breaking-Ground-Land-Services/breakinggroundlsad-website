#!/usr/bin/env python3
from scripts.build_site import apply_base_to_chrome, build_home, build_projects

build_home()
build_projects()
apply_base_to_chrome()
print("rebuilt home + projects")
