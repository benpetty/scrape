#!/usr/bin/env python

import sys


def main():
    try:

        from scrape.radio_nat_turner import main

        exit_status = main()

    except KeyboardInterrupt:

        from scrape.core.exit_status import ExitStatus

        exit_status = ExitStatus.ERROR_CTRL_C

    if hasattr(exit_status, "value"):
        sys.exit(exit_status.value)
    else:
        print("✅ done")
        sys.exit()


if __name__ == "__main__":
    main()
