<!-- -*- eval: (visual-line-mode 1) -*- -->

<div data-theme-toc="true"></div>
<div data-guild-docs="true"></div>

<!-- TODO

Sections on:

- Comparing runs
- Viewing run info
- Viewing run files
- Viewing and filtering run output
- Using TensorBoard

-->

## Overview

Guild View is a web based application that lets you view runs and compare results.

Guild View supports these features:

- Compare run results in a table, similar to the information provided by [Guild Compare](/docs/compare)
- View run metadata, similar to the information provided by [`guild runs info`](/commands/runs-info)
- View run files
- View run output
- View runs in TensorBoard

## Start Guild View

To start Guild Run, run [`guild view`](/commands/view) from a command line terminal.

``` command
guild view
```

Guild starts the application and opens it in a web browser.

![view-start|685x500](upload://1j2gFVZeJ89JGiqgCa6yviRlK9K.png)

You can filter the runs displayed by Guild View using command options. Refer to [`guild view`](/commands/view) for a list of supported filter options.

## Stop Guild View

To stop Guild View, in the command line terminal where you start Guild, press **Ctrl-C**.

Close any browser tabs that use Guild View to save memory.

> <span data-guild-class="callout important">Important</span> Guild View tabs in your browser will no longer work properly after you stop Guild View in the command line terminal. To restart Guild View, close the tabs and re-run [`guild view`](/commands/view) from the command line. Guild will open a new tab in your browser.

## Run Guild View Remotely

To access Guild View from a remote server, your local browser must have network connectivity to the remote server. This typically requires that specific ports be made available through a firewall or network router.

To specify a port when running Guild View, use the `--port` option. For example, if port `8080` is open on the remote server, run:

``` command
guild view --port 8080
```

``` output
Running Guild View at http://hostname:8080 (Type Ctrl-C to quit)
```

> <span data-guild-class="callout important">Important</span> Guild will not automatically open Guild View in your browser when you run `guild view` remotely. You must open the URL show in the console terminal.
