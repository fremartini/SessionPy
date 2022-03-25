test_dir = tests/
session_type_tests = $(test_dir)/tests_sessiontypes
type_checking_tests = $(test_dir)/tests_typechecking
helper_tests = $(test_dir)/tests_helpers
statemachine_tests = $(test_dir)/tests_statemachine
src_dir = src/

test:
	python3.10 $(type_checking_tests)/test_typecheck.py
	python3.10 $(type_checking_tests)/test_paramtypes.py
	python3.10 $(type_checking_tests)/test_union.py
	python3.10 $(helper_tests)/test_immutable_list.py
	python3.10 $(helper_tests)/test_immutable_map.py
	python3.10 $(session_type_tests)/test_channels.py
	python3.10 $(session_type_tests)/test_recursion_and_labels.py
	python3.10 $(statemachine_tests)/test_statemachine.py

#usage: make check file=test.py
check:
	python3.10 $(src_dir)/check.py $(file)
