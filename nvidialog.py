import csv
import pwd
import sys
import time

import nvsmi

ERROR_STR = "ERROR"


def owner(pid):
    try:
        with open(f'/proc/{pid}/status') as proc_file:
            for line in proc_file:
                if line.startswith('Uid:'):
                    uid = int(line.split()[1])
                    return pwd.getpwuid(uid).pw_name
    except:
        ERROR_STR


def cmdline(pid):
    try:
        with open(f'/proc/{pid}/cmdline') as proc_file:
            return proc_file.read().replace('\0', ' ')[:-1]
    except:
        return ERROR_STR


if __name__ == '__main__':
    interval = 60
    tocsv = csv.writer(sys.stdout)

    while True:
        gpus = list(nvsmi.get_gpus())
        gpus = {gpu.id: gpu for gpu in gpus}
        processes = nvsmi.get_gpu_processes()
        now = time.time()
        for process in processes:
            tocsv.writerow(
                [int(now), process.gpu_id, gpus[process.gpu_id].gpu_util, process.used_memory, process.pid,
                 owner(process.pid),
                 cmdline(process.pid)])
        time.sleep(interval)
