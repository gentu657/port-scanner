import socket
import ipaddress
from colorama import Fore, Style, init


init(autoreset=True)

IP_RANGES = [
    "192.168.1.0/24"
]


PORTS = [80, 22, 8080]

def check_port(ip, port=80, timeout=1):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((str(ip), port))
        sock.close()
        return result == 0
    except:
        return False


def scan_range(ip_range):
    open_ips = []
    network = ipaddress.ip_network(ip_range, strict=False)

    for ip in network.hosts():
        for port in PORTS:
            print(f"testing {ip}:{port}")
            if check_port(ip, port):
                open_ips.append((str(ip), port))
                print(Fore.GREEN + f"{ip}:{port} open")
    
    return open_ips


def main():
    
    print(Fore.BLUE + Style.BRIGHT + """
███████╗ ██████╗ █████╗ ███╗   ██╗███╗   ██╗██╗███╗   ██╗ ██████╗     
██╔════╝██╔════╝██╔══██╗████╗  ██║████╗  ██║██║████╗  ██║██╔═══██╗    
███████╗██║     ███████║██╔██╗ ██║██╔██╗ ██║██║██╔██╗ ██║██║   ██║    
╚════██║██║     ██╔══██║██║╚██╗██║██║╚██╗██║██║██║╚██╗██║██║   ██║    
███████║╚██████╗██║  ██║██║ ╚████║██║ ╚████║██║██║ ╚████║╚██████╔╝    
╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚═════╝     
                         SCANNING.VS
""")

    all_open_ips = []

    for ip_range in IP_RANGES:
        print(Fore.CYAN + f"\nScanning {ip_range}...\n")
        open_ips = scan_range(ip_range)
        all_open_ips.extend(open_ips)

    
    with open("ports.txt", "w") as f:
        for ip, port in all_open_ips:
            f.write(f"{ip}:{port}\n")
        
    print(Fore.YELLOW + f"\nScan complete. Found {len(all_open_ips)} open ports")


if __name__ == "__main__":
    main()
