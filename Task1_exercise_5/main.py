"""
Imports
"""
import os
import socket
import argparse
import platform
import psutil
def get_distro_info():
    """
    Distro function
    """
    distro = platform.system() + " " + platform.release()
    return f"Distro: {distro}"

def get_memory_info():
    """
    Memory function
    """
    mem = psutil.virtual_memory()
    return f"Memory: Total: {mem.total / (1024**3):.2f} GB, Used: {mem.used / (1024**3):.2f} GB, Free: {mem.available / (1024**3):.2f} GB"

def get_cpu_info():
    """
    Cpu function
    """
    cpu_info = platform.processor()
    cores = psutil.cpu_count(logical=False)
    logical_cores = psutil.cpu_count(logical=True)
    freq = psutil.cpu_freq()
    return (f"CPU: Model: {cpu_info}, Physical Cores: {cores}, Logical Cores: {logical_cores}, "
            f"Max Frequency: {freq.max:.2f} MHz")

def get_user_info():
    """
    User info function
    """
    user = os.getlogin()
    return f"Current User: {user}"

def get_load_average():
    """
    Load average function
    """
    load_avg = os.getloadavg()
    return f"Load Average (1, 5, 15 min): {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}"

def get_ip_address():
    """
    Ip adress function
    """
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return f"IP Address: {ip_address}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
    "Fetch system information based on specified arguments.")
    parser.add_argument("-d", "--distro", action="store_true", help="Get distro information")
    parser.add_argument("-m", "--memory", action="store_true", help="Get memory information")
    parser.add_argument("-c", "--cpu", action="store_true", help="Get CPU information")
    parser.add_argument("-u", "--user", action="store_true", help="Get current user information")
    parser.add_argument("-l", "--load", action="store_true", help="Get system load average")
    parser.add_argument("-i", "--ip", action="store_true", help="Get IP address")

    args = parser.parse_args()

    if args.distro:
        print(get_distro_info())
    if args.memory:
        print(get_memory_info())
    if args.cpu:
        print(get_cpu_info())
    if args.user:
        print(get_user_info())
    if args.load:
        print(get_load_average())
    if args.ip:
        print(get_ip_address())

    if not any(vars(args).values()):
        parser.print_help()
