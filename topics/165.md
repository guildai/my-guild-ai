<!-- -*- eval:(visual-line-mode 1) -*- -->

<div data-theme-toc="true"></div>
<div data-guild-docs="true"></div>

## Overview

A *queue* is a long-running runs implemented by the built-in `queue` operation. A queue is used to start staged runs.

Queues can be used to:

- Schedule runs
- Run operations in parallel
- Assign runs to GPUs

To start a queue, run:

``` command
guild run queue
```

Once running, a queue looks for a staged run and starts it when the all of the following are true:

- If started with `wait-for-running` and the queue is not waiting for a run to complete
- The staged run is compatible with the queue GPU affinity

A queue waits for a run to finish if any of the following conditions are true:

- The queue starts the run
- The queue is started with the `wait-for-running`

A run matches a queue GPU affinity when:

- The queue is started with an undefined `gpu` flag (default) *and* the staged run does specify a GPU affinity
- The queue `gpu` flag value matches the staged run GPU affinity

Queues coordinate among themselves when starting runs so you can start multiple queues as needed.

## Schedule Staged Runs

Use a queue to start staged runs in the order staged. This is useful when you want to run several operations back-to-back without attending them.

To use a queue to stage runs, first start a queue in the background:

``` command
guild run queue --background
```

Check status of the operation as needed using `guild runs`.

To list running runs, use:

``` command
guild runs --running
```

You can stop runs using [`guild stop`](/commands/stop).

Stage a run by specifying the `--stage` option. For example, to stage an run for `train`, run:

```
guild run train --stage
```

Guild initializes the run but does not start it. Instead, the queue, running in the background, starts the queue and waits for it to finish. You can continue staging runs as needed.

Staged runs have a status of `staged`, which you can filter by running:

``` command
guild runs --staged
```

## Run Operations in Parallel

You can use multiple queues to run operations in parallel. Use GPU affinity to assign runs to a particular queue and GPU.

> <span data-guild-class="callout tip">Tip</span> While you can use queues to run operations in parallel, it is often easier to start runs in the background using `--background` with [`guild run`](/commands/run). In this case, all runs proceed in parallel without the need for queues.

## Run Once

You can run a queue once to start all staged runs. Use the flag `run-once=yes`:

``` command
guild run queue run-once=yes
```

In this case, the queue exits once it has started the applicable staged runs. It does not continue running, waiting for new staged runs.

If runs are staged while the queue is running, the queue starts them whether running with `run-once` or not.
