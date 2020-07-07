lint:
	pylint -rn -f parseable myguild

missing-doc-tag:
	@find topics -name '*.md' -exec grep -rL data-guild-docs {} \;
