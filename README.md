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

## Arguments

```text
usage: nvidialog.py [-h] [--interval INTERVAL] [--log_cmdline] [--output_file OUTPUT_FILE]

options:
  -h, --help            show this help message and exit
  --interval INTERVAL   Interval log in seconds
  --log_cmdline         Enable command-line logging
  --output_file OUTPUT_FILE
                        Output file, default is standard output
```

Command line is logged only if enabled using the `--log_cmdline` argument.

The `--interval` sets the logging interval in seconds.

By default, the log is printed on the standard output, use the `--output_file` to write to a file.
