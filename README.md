## Commands

### Compare and Update

`borg` can compare or update a local folder to match a template repository.

An expected use case is keeping a code repository in sync with a [GitHub Template Repository][gittemp].
Any web URL containing example files may be used.

`.borg.toml` tells `borg` where to find the template repository. The template repository must include at least `.borg.template.toml`, which specifies which of the other files available in the template repository should be kept in sync by `borg`. See `Configuration` for more details on configurating `borg`.

`borg compare` may be used during a CI/CD pipeline to issue a warning if files differ from the template repository. The command `borg compare` will have no output if all specified files match the template repository. If any files differ, they will be listed in the output of `borg compare`, and `borg` will exit with a non-zero exit code.

`borg update` updates all appropriate files in the local folder to match the template repository, per the configuration in `.borg.template.toml`. `borg update` can be used to resolve CI/CD pipeline warnings issued by `borg compare`. 

Using the these commands helps ensure that best practice updates made to a template repository consistently reach project repositories.

[gittemp]: https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-template-repository

### Generate

`borg` can generate content for `.gitattributes`, based on the `files` section of the configured `.borg.template.toml`. The generated [gitattributes file][gita] indicates to GitHub that certain files are machine-generated. This causes GitHub to hide the file `diff` during a pull request.

You may want to add additional contents after regenerating `.gitattributes`,
as in the `Makefile` example below.

[gita]: https://git-scm.com/docs/gitattributes) 


```sh
borg generate .gitattributes
```

Given this `.borg.template.toml`:

```toml
[template]
# Keep these files in sync across Python repos
files = [
    ".gitignore",
    ".github/workflows/pr_reminder.yml",
    ".github/workflows/cleanup.yml",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
]

[generate.gitattributes]
files = [
    # All machine generated files
    ".gitattributes",
    "requirements*.txt",
]
# Include all template files above
include_template_files = true
```

will generate this `.gitattributes` file:

```sh
# Ignore files managed by borg in Github PR reviews
.gitattributes linguist-generated
requiements*.txt linguist-generated
.gitignore linguist-generated
.github/workflows/pr_reminder.yml linguist-generated
.github/workflows/cleanup.yml linguist-generated
CODE_OF_CONDUCT.md linguist-generated
SECURITY.md linguist-generated
```

And here is a `Makefile` example, where we append additional data to the `.gitattributes` file after generating it with `borg generate`.

```makefile
.gitattributes: .borg.toml
	borg generate $^
	echo 'requirements*.txt linguist-generated' >> $^  # Add additional files to .gitattributes
```

## Configuration

### Local configuration

A file named `.borg.toml` should exist in the directory where `borg` is run.
This configuration file tells `borg` where to find the templates to compare
the local directory to.

See `.borg.toml` in this directory for an example.

`url` should point to a web directory containing a `.borg.template.toml` file and all expected files specified in that file.

An expected use case is using `raw.githubusercontent` URLs for public GitHub repositories.

A good way to find this `url` is to navigate to raw file view of `.borg.template.toml`.

For example, on GitHub, the raw version of `.borg.template.toml` is at `https://raw.githubusercontent.com/techservicesillinois/secdev-template-repository/refs/heads/main/.borg.template.toml`
```

And so the `.borg.toml` file should contain:

```
[source]
url = 'https://raw.githubusercontent.com/techservicesillinois/secdev-template-repository/refs/heads/main/'
```

It is also possible to use other GitHub branches for comparison, using a `refs/heads` URL:

```
[source]
# To compare to an un-merged `doc/python` branch:
url = 'https://raw.githubusercontent.com/techservicesillinois/secdev-template-python/refs/heads/doc/python/'
```

> Note: Our typical use case is public templates. But a private repository can be used, by first cloning the private repository, and then calling `borg` with `--source-dir` pointed to the local folder of the clone.

When using `--source-dir`, any `.borg.toml` file is ignored. Template configuration is loaded as usual from the `.borg.template.toml` file in the template repository directory specified by `--source-dir`.

### Template configuration 

The remote `url` should contain a file named `.borg.template.toml`.
This file specifies which of the files available at the remote URL
should be treated as templates for comparison.

Example `.borg.template.toml`:

```
[template]
files = [
    ".gitattributes",
    ".github/workflows/deploy.yml",
    ".gitignore",
    "CODE_OF_CONDUCT.md",
    "Makefile",
    "SECURITY.md",
    "mypy.ini",
    "pyproject.toml",
    "tests/test_python_version.py",
]
```

### Overriding `.borg.template.toml` with `.borg.toml`

If a file specified by `.borg.template.toml` in the template repository should
not be synced; it can be added to `skip_files` in the `template` section of
the local `.borg.toml` file.

With the following in `.borg.toml`, `.gitignore` will not be compared or updated,
even if specified in the template repository `.borg.template.toml`:

```toml
[template]
skip_files = [
    ".gitignore",
]
```

## Data Sources

|Data Store|Data Type|Sensitivity|Notes|
|----------|---------|-----------|-----|
| A remote template URL | Text | Public | This URL is specified in `.borg.toml` |

## Endpoint Connections

No endpoints. The outputs of this this tool are managed through a separate dedicated tool, such as `git`.

