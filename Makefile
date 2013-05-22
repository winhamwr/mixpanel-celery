removepyc:
	find . -name "*.pyc" | xargs rm

ghdocs:
	scripts/doc2ghpages

autodoc:
	scripts/doc4allmods mixpanel
