# NVIDIALog

Logger of NVIDIA GPU use, based on nvidia-smi and the wrapper package [nvsmi](https://pypi.org/project/nvsmi/).

```commandline
python nvidialog.py
```

The script logs every minute the processes using the GPUs on the system.
The format of each row is:

```text
time, interval_duration_secs, gpu_id, gpu_utilization_precent, gpu_used_memory, process_pid, process_owner, command_line
```
e.g.:
```text
1715344059,60,0,100,17936,130204,esuli,NOT_LOGGED
1715344120,60,0,100,17936,130204,esuli,NOT_LOGGED
```

If multiple process are running at the same moments, multiple lines will be printed.
If no process is using a GPU, nothing will be printed.
Utilization percentage is relative to the whole GPU, not to the single process using it.

## Report

`nvidialog-report.py` prints a markdown-formatted report from the log. See the [example report](example_report.md).

### Arguments
```text
usage: nvidialog-report.py [-h] [--input_file INPUT_FILE]
                           [--num_gpus NUM_GPUS]

options:
  -h, --help            show this help message and exit
  --input_file INPUT_FILE
                        Input file, default is standard input
  --num_gpus NUM_GPUS   Number of GPUs. Optional, by default it is inferred
                        from log.
```

Command line is logged only if enabled using the `--log_cmdline` argument.

The `--interval` sets the logging interval in seconds.

By default, the log is printed on the standard output, use the `--output_file` to write to a file.

The number of GPUs is inferred from the log. Set a different number with the `--num_gpus` argument.
