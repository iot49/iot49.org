# This top-level micropython.cmake is responsible for listing
# the individual modules we want to include.
# Paths are absolute, and ${CMAKE_CURRENT_LIST_DIR} can be
# used to prefix subdirectories.

# Add projects
include(${CMAKE_CURRENT_LIST_DIR}/msgpack/micropython.cmake)
include(${CMAKE_CURRENT_LIST_DIR}/finaliserproxy/micropython.cmake)
include(${CMAKE_CURRENT_LIST_DIR}/ioctl/micropython.cmake)
