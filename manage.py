#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    
    home_dir = os.path.expanduser('~')
    os.environ['quisby_conf_dir'] = os.path.join(home_dir,".config/pquisby")
    
    sys.path.append('./pquisby')
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "quisby_api.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()