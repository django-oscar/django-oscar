#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oscarsandbox.settings.oscarsandbox")

    from django.core.management import execute_from_command_line

    if "run_maintenance" not in sys.argv:
        execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
