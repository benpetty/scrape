REQUIRED_BINS := geckodriver uv
$(foreach bin,$(REQUIRED_BINS),\
    $(if $(shell command -v $(bin) 2> /dev/null),$(info Found required `$(bin)`),$(error Please install `$(bin)`)))

-include .env
export

.PHONY: install scrape

install:
	@uv sync --extra dev

scrape:
	@uv run scrape
