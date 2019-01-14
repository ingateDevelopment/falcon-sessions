.develop: $(shell find falcon_sessions -type f)
	@pip install -e .
	@touch .develop

test: .develop
	py.test --flake8 --doctest-modules ./tests ./falcon_sessions

vtest: .develop
	py.test --flake8 --doctest-modules ./tests ./falcon_sessions -v

cov: .develop
	py.test --flake8 --doctest-modules --cov falcon_sessions --cov-report html --cov-report term ./tests ./falcon_sessions
	@echo "open file://`pwd`/htmlcov/index.html"

release: ~/.pypirc
	python setup.py bdist_wheel upload
