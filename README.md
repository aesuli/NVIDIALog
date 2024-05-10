# NVIDIALog

Logger of NVIDIA GPU use, based on nvidia-smi and the wrapper package [nvsmi](https://pypi.org/project/nvsmi/).

```commandline
python nvidialog.py
```

The script logs every minute the processes using the GPUs on the system.
The format of each row is:

```text
time, gpu_id, gpu_utilization_precent, gpu_used_memory, process_pid, process_owner, command_line
```
e.g.:
```text
1715344059,0,100.0,17936.0,130204,esuli,python train.py openwebtext
1715344120,0,100.0,17936.0,130204,esuli,python train.py openwebtext
```

If multiple process are running at the same moments, multiple lines will be printed.
If no process is using a GPU, nothing will be printed.
Utilization percentage is relative to the whole GPU, not to the single process using it.
