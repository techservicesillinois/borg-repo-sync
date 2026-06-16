## Commands

### Compare and Update

`borg` can compare or update a local folder to match a template repository.

An expected use case is keeping a code repository in sync with a [GitHub Template Repository][gittemp].
Any web URL containing example files may be used.

## Configuration

`.borg.toml` tells `borg` how to find your template repository and which files should be kept in sync.
See `Configuration` for more details on configurating `borg`.

`borg compare` may be used during a CI/CD pipeline to issue a warning if files differ from the template repository. The command `borg compare` will have no output if all specified files match the template repository. If any files differ, they will be listed in the output of `borg compare`, and `borg` will exit with a non-zero exit code.

`borg update` updates all appropriate files in the local folder to match the template repository, per the configuration in `.borg.toml`. `borg update` can be used to resolve CI/CD pipeline warnings issued by `borg compare`. 

Using the these commands helps ensure that best practice updates made to a template repository consistently reach project repositories.

[gittemp]: https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-template-repository

## Configuration

### Local configuration

`borg` will look for `.borg.toml` in the following places:

- From a local `.borg.toml` file, if present
- At the file provided by `--config`, if specified
- At the URL provided by `--config-url`, if specified
- From `default.borg.toml` in this repository, if no other configuration is specified


The `[template]` section of `.borg.toml` tells `borg` where to find the templates to compare the local directory to. 

`files_url` can be any valid HTTPS hosted folder. Authentication is not supported.
An expected use case is using `raw.githubusercontent` URLs for public GitHub repositories.

```yaml
[template]
files_url = "https://raw.githubusercontent.com/techservicesillinois/secdev-template-repository/refs/heads/main/"
files = [
    ".github/workflows/pr_reminder.yml",
    ".github/workflows/cleanup.yml",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
]
```

A good way to find a valid `files_url` is to navigate to a raw file view in GitHub.
For example, on GitHub, the raw version of `default.borg.toml` is at `https://raw.githubusercontent.com/techservicesillinois/borg-repo-sync/refs/heads/main/default.borg.toml`.

It is also possible to use other GitHub branches for comparison, using a `refs/heads` URL:

```
[template]
# To compare to an unmerged `doc/python` branch:
files_url = 'https://raw.githubusercontent.com/techservicesillinois/secdev-template-python/refs/heads/doc/python/'
```

> Note: Our typical use case is public templates. But a private repository can be used, by first cloning the private repository, and then calling `borg` with `--source-dir` pointed to the local folder of the clone.

When using `--source-dir`, `files_url` in `.borg.toml` is ignored, and the local folder is used, instead.

### Updating a template repository

When updating a template repository, `borg` can complain about unmerged changes, because `.borg.toml` usually points to the `main` branch of that same repository.

In these cases, it can be useful to override with the `--source-dir` option to point back at the current files.

For example, regenerate `.gitattributes` from the current local files, with:

```
rm .gitattributes
borg -s . gen .gitattributes
```

### Generate

`borg` can generate content for `.gitattributes`, based on the `files` section of the configured `.borg.toml`. The generated [gitattributes file][gita] indicates to GitHub that certain files are machine-generated. This causes GitHub to hide the file `diff` during a pull request.

You may want to add additional contents after regenerating `.gitattributes`,
as in the `Makefile` example below.

[gita]: https://git-scm.com/docs/gitattributes) 


```sh
borg generate .gitattributes
```

Given this `.borg.toml`:

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


## Data Sources

|Data Store|Data Type|Sensitivity|Notes|
|----------|---------|-----------|-----|
| A remote template URL | Text | Public | This URL is specified in `.borg.toml` |

## Endpoint Connections

No endpoints. The outputs of this this tool are managed through a separate dedicated tool, such as `git`.

