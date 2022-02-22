test_dir = tests/
session_type_tests = $(test_dir)/tests_sessiontypes
type_checking_tests = $(test_dir)/tests_typechecking
type_check_dir = typecheck/

test:
	python3.10 $(type_checking_tests)/test_typecheck.py
	python3.10 $(type_checking_tests)/test_union.py

#usage: make check file=test.py
check:
	python3.10 $(type_check_dir)/check.py $(file)
