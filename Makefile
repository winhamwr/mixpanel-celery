test:
	(scripts/run_tests.py)

removepyc:
	find . -name "*.pyc" | xargs rm

docs:
	cd docs && make html;

ghdocs:
	scripts/doc2ghpages