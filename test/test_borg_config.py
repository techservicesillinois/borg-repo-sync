'''Test loading borg config files.'''

from borg.borg import get_files_to_compare


def test_get_files_to_compare():

    config = {
            'template': {
                'files': ['.gitignore', 'Makefile'],
                'skip_files': ['.gitignore']
            }
    }
    result = get_files_to_compare(config)
    assert '.gitignore' not in result
    assert result == ['Makefile']

