import nvsmi

from nvidialog import cmdline, owner

if __name__ == '__main__':
    gpus = list(nvsmi.get_gpus())
    gpus = {gpu.id: gpu for gpu in gpus}
    processes = nvsmi.get_gpu_processes()
    for process in processes:
        print(process.gpu_id, int(gpus[process.gpu_id].gpu_util), int(process.used_memory), process.pid,
              owner(process.pid), cmdline(process.pid))
