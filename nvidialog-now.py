import os
import nvsmi
import pandas as pd

from nvidialog import cmdline, owner

if __name__ == '__main__':
    gpus = list(nvsmi.get_gpus())
    gpus = {gpu.id: gpu for gpu in gpus}
    processes = nvsmi.get_gpu_processes()
    data = []
    for process in processes:
        data.append([process.gpu_id, int(process.used_memory), process.pid, owner(process.pid), cmdline(process.pid)])
    df = pd.DataFrame(data, columns=['GPU', 'Mem (MB)', 'PID', 'User', 'Command'])
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    width = os.get_terminal_size().columns
    pd.set_option('display.width', width)
    if width > 50:
        pd.set_option('display.max_colwidth', width-50)
    else:
        pd.set_option('display.max_colwidth', None)
    df.index = ['']*len(df)
    print(df)
