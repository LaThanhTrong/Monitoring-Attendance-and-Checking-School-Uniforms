import psutil
import subprocess
import os

def getCPU():
    return psutil.cpu_percent(interval=1)

def getRAM():
    return psutil.virtual_memory()

def getGPU():
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        gpu_utilization = float(result.stdout.strip())
        return gpu_utilization
    except FileNotFoundError:
        return None  # NVIDIA GPU drivers or nvidia-smi not found
    except subprocess.CalledProcessError:
        return None  # nvidia-smi command failed


