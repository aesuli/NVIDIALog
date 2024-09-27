import argparse
import csv
import pwd
import sys
import time
import socket

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
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind('\0NVL_single_process_lock')
    except socket.error:
        print('Process already running')
        exit(0)

    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int, default=60, help='Interval log in seconds')
    parser.add_argument('--log_cmdline', action='store_true', help='Enable command-line logging')
    parser.add_argument('--output_file', type=argparse.FileType('wt', encoding='utf-8'), default=sys.stdout,
                        help='Output file, default is standard output')
    args = parser.parse_args()

    interval = args.interval
    log_cmdline = args.log_cmdline
    output_file = args.output_file

    to_csv = csv.writer(output_file)
    while True:
        gpus = list(nvsmi.get_gpus())
        gpus = {gpu.id: gpu for gpu in gpus}
        processes = nvsmi.get_gpu_processes()
        now = time.time()
        for process in processes:
            to_csv.writerow(
                [int(now), interval, process.gpu_id, int(gpus[process.gpu_id].gpu_util), int(process.used_memory),
                 process.pid, owner(process.pid), cmdline(process.pid) if log_cmdline else "NOT_LOGGED"])
        output_file.flush()
        time.sleep(interval)
