test_dir = tests/
session_type_tests = $(test_dir)/tests_sessiontypes
type_checking_tests = $(test_dir)/tests_typechecking
helper_tests = $(test_dir)/tests_helpers
type_check_dir = typecheck/

test:
	python3.10 $(type_checking_tests)/test_typecheck.py
	python3.10 $(type_checking_tests)/test_union.py
	python3.10 $(helper_tests)/immutable_list_tests.py
	python3.10 $(helper_tests)/immutable_map_tests.py

#usage: make check file=test.py
check:
	python3.10 $(type_check_dir)/check.py $(file)
