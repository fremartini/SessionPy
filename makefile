test_dir = tests/
session_type_tests = $(test_dir)/tests_sessiontypes
type_checking_tests = $(test_dir)/tests_typechecking
helper_tests = $(test_dir)/tests_helpers
src_dir = src/

test:
	python3.10 $(type_checking_tests)/test_typecheck.py
	python3.10 $(type_checking_tests)/test_paramtypes.py
	python3.10 $(type_checking_tests)/test_union.py
	python3.10 $(helper_tests)/immutable_list_tests.py
	python3.10 $(helper_tests)/immutable_map_tests.py
	python3.10 $(session_type_tests)/channel_tests.py
	python3.10 $(session_type_tests)/test_recursion_and_labels.py

#usage: make check file=test.py
check:
	python3.10 $(src_dir)/check.py $(file)
