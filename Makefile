REQUIRED_BINS := geckodriver
$(foreach bin,$(REQUIRED_BINS),\
    $(if $(shell command -v $(bin) 2> /dev/null),$(info Found required `$(bin)`),$(error Please install `$(bin)`)))

-include .env


install:
	@pipenv install


.PHONY: scrape
scrape:
	@pipenv run scrape
