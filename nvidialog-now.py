import nvsmi
import tabulate

from nvidialog import cmdline, owner

if __name__ == '__main__':
    gpus = list(nvsmi.get_gpus())
    gpus = {gpu.id: gpu for gpu in gpus}
    processes = nvsmi.get_gpu_processes()
    data = [['GPU', 'Memory', 'PID', 'User', 'Command']]
    for process in processes:
        data.append([process.gpu_id, int(process.used_memory), process.pid, owner(process.pid), cmdline(process.pid)])
    print(tabulate.tabulate(data))
