<!-- -*- eval:(visual-line-mode 1) -*- -->

<div data-theme-toc="true"></div>
<div data-guild-docs="true"></div>

## Overview

Guild lets you package and distribute your work to make deployment and reuse easier for others.

To see how Guild packages work, you can experiment with a pre-packaged Guild package [`gpkg.hello`](https://pypi.org/project/gpkg.hello/).

Install a sample package:

``` command
pip install gpkg.hello
```

List available operations:

``` command
guild ops gpkg.hello
```

``` output
gpkg.hello/hello:default           Print a default message
gpkg.hello/hello:from-file         Print a message from a file
gpkg.hello/hello:from-file-output  Print output from last file-output operation
gpkg.hello/hello:from-flag         Print a message
```

Run an operation:

``` command
guild run gpkg.hello/hello:default -y
```

``` output
Hello Guild!
```

Uninstall the package.

``` command
pip uninstall gpkg.hello
```

This is a simple "hello world" operation. You can deploy and use your own packages just as easily.

> <span data-guild-class="callout note">Note</span> Guild packages are standard Python [wheel distributions](https://packaging.python.org/guides/distributing-packages-using-setuptools/#wheels). They are deployed using any of the supported methods for deploying Python packages, including installation with `pip` from [PyPI](https://pypi.org/).

Use Guild packages to:

- Delpoy models for production
- Let others easily use your work (e.g. for reproducibility)
- Release your work as an installable program, using Guild as the CLI

## Build a Package

Build a package for your project by running [`guild package`](/commands/package). The project must contain a [Guild file](/docs/guildfiles) to run this command.

``` command
guild package
```

If the project does not contain a top-level `package` object, Guild uses a number of default values when generating a package.

If you intend to distribute the package, define a `package` object using a [full format](/reference/guildfile#full-format) Guild file.

``` yaml
- package: gpkg.my-model
  version: 0.0.1

- model: model-1
  ...

- model: model-2
  ...
```

> <span data-guild-class="callout note">Note</span> To avoid name collisions with other packages in PyPI, prefix the package name with `gpkg.` or another namespace.

This minimal configuration lets you name and version the package. For a full list of supported package attributes, see [*Guild File Reference*](/reference/guildfile#package-attributes).

To upload a package to PyPI use the `--upload` option. Specify your PyPI user name and password using the `--user` and `--password` options respectively. Refer to [`package`](/commands/package) command help for more information.

> <span data-guild-class="callout note">Note</span> To upload packages, you need the [`twine`](https://pypi.org/project/twine/) package. Install it using `pip install twine`.

## Install a Package

If you upload the package to PyPI, you can install it using pip and the package name.

``` command
pip install gpkg.my-model
```

To install the wheel directly, use pip to install the applicable file created in the `dist` project subdirectory.

|||
|-|-|
| <span data-guild-class="ls-dir-open">Project</span> | |
| <span data-guild-class="ls-file ls-1">guild.yml</span> | |
| <span data-guild-class="ls-dir ls-1">build</span> | <span data-guild-class="dim">Temporary directory containing package build artifacts</span> |
| <span data-guild-class="ls-file ls-1">*.egg-info</span> | <span data-guild-class="dim">Temporary egg info directories |
| <span data-guild-class="ls-dir-open ls-1">dist</span> | <span data-guild-class="dim">Directory containing generated wheels</span> |
| <span data-guild-class="ls-file ls-2">*.whl</span> | <span data-guild-class="dim">Generated wheels --- install using `pip install dist/*.whl`</span> |

> <span data-guild-class="callout tip">Tip</span> Avoid storing package related files your git repository by adding the following items to the `.gitignore` file:
>
> ```
> build
> dist
> *.egg-info
> ```

## Use Installed Packages

Installed Guild packages provide models and operations that you can run from any directory on your system. Think of these like programs that you install and interact with using Guild commands.

List installed packages:

``` command
guild packages
```

Show help for an installed package:

``` command
guild help PACKAGE
```

List installed models:

``` command
guild models -i
```

List installed operations:

``` command
guild operations -i
```

> <span data-guild-class="callout tip">Tip</span> You can omit the `-i` when running either of the above commands from outside a project directory. The `-i` option is required when running witint a project directory to include installed models and operations, which are otherwie omitted.

## Packages and Remote Operations

Guild uses the packaging facility when running [remote operations](/docs/runs#run-on-a-remote-system). Generally the `package` object is not necessary to support remote runs. Guild's default packaging support is sufficient to package and install a project on a remote system.

In cases where the default packaging support is not sufficient, you can create a `package` object as described above.

### Data Files

If an operation [requires project files](/docs/dependencies#project-files), those files must be included in a package for remote runs.

Use the [`data-files`](/reference/guildfile#package-data-files) package attribute to list files for inclusion in the package.

The `hello-package` example illustrates how this works:

<div data-guild-github-select="4-5">

https://github.com/guildai/guildai/blob/master/examples/hello-package/guild.yml#L5
</div>

Refer to [this example](https://github.com/guildai/guildai/tree/master/examples/hello-package-2) to include a directory of files in the generated package.

> <span data-guild-class="callout tip">Tip</span> You can list files in a Python wheel using any zip-compatible tool. To view package files using the `unzip` command, run `unzip -l dist/*.whl`. Use this to verify that the package contains the expected source code and data files.
