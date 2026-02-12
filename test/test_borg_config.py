'''Test loading borg config files.'''

# Imports - mock and borg
from borg.borg import get_files_to_compare


def test_get_files_to_compare():

    template = {'template': {'files': ['.gitignore', 'Makefile']}}
    local = {'template': {'skip_files': ['.gitignore']}}
    result = get_files_to_compare(local, template)
    assert '.gitignore' not in result
    assert result == ['Makefile']

