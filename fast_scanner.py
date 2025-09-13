# fast_scanner.py
import socket
import ipaddress
import time
import sys
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor, as_completed

init(autoreset=True)

# --- קונפיגורציה ---
IP_RANGES = [
    "192.168.1.0/24"
]

PORTS = [80, 22, 8080]

TIMEOUT = 0.6        # זמן המתנה לחיבור (שנה בהתאם לרשת)
MAX_WORKERS = 150    # מספר ת'רדים מקבילים - התאמן עם הערך לפי משאבי המכשיר/הרשת

# batch printing כדי למנוע print לכל ניסיון (יעיל הרבה יותר)
BATCH_PRINT_SIZE = 200
BATCH_PRINT_INTERVAL = 0.5  # שניות - לגרסה שמתחשבת בזמן גם כן
# ---------------------

def check_port(ip, port, timeout=TIMEOUT):
    """
    מחזיר True אם הפורט פתוח, אחרת False.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((str(ip), port))
            return result == 0
    except Exception:
        return False

def scan_range(ip_range):
    """
    סורק את טווח ה-IP בצורה מקבילה על כל פורט ברשימת PORTS.
    מדפיס כל ניסיון (בatches) ושומר attempts.txt.
    מחזיר רשימת (ip, port) פתוחים.
    """
    open_ips = []
    network = ipaddress.ip_network(ip_range, strict=False)
    hosts = list(network.hosts())

    # ניצור futures עבור כל זוג ip+port
    tasks = []
    total_tasks = len(hosts) * len(PORTS)

    # קובץ ניסיון
    attempts_file = open("attempts.txt", "w", encoding="utf-8")
    attempts_file.write("ip:port status\n")

    buffer_lines = []
    last_flush = time.time()
    processed = 0

    def flush_buffer(final=False):
        nonlocal buffer_lines, last_flush
        if not buffer_lines:
            return
        # הדפסה מקובצת למסך (עם צבעים קטנים)
        out_lines = []
        for ip, port, ok in buffer_lines:
            if ok:
                out_lines.append(Fore.GREEN + f"testing {ip}:{port} -> open\n")
            else:
                out_lines.append(f"testing {ip}:{port} -> closed\n")
        sys.stdout.write("".join(out_lines))
        sys.stdout.flush()
        # כתיבה לקובץ attempts.txt (הגרסה הפשוטה)
        for ip, port, ok in buffer_lines:
            status = "open" if ok else "closed"
            attempts_file.write(f"{ip}:{port} {status}\n")
        attempts_file.flush()
        buffer_lines = []
        last_flush = time.time()

    # worker wrapper
    def check_pair(ip, port):
        ok = check_port(ip, port)
        return (str(ip), port, ok)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(check_pair, ip, port): (ip, port) for ip in hosts for port in PORTS}

        for fut in as_completed(futures):
            try:
                ip, port, ok = fut.result()
            except Exception:
                # במקרה של שגיאה, סמן סגור והמשך
                ip, port, ok = (futures.get(fut)[0], futures.get(fut)[1], False)

            processed += 1

            # הוספה ל-buffer (יוצג ונכתב ב-batches)
            buffer_lines.append((ip, port, ok))

            # שמירה של פתוחים ברשימת התוצאות
            if ok:
                print(Fore.GREEN + f"{ip}:{port} open")
                open_ips.append((ip, port))

            # תנאי flush: גודל או מרווח זמן
            now = time.time()
            if len(buffer_lines) >= BATCH_PRINT_SIZE or (now - last_flush) >= BATCH_PRINT_INTERVAL:
                flush_buffer()

            # הדפסת פרוגרס קל מדי פעם
            if processed % 500 == 0 or processed == total_tasks:
                elapsed = now - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                pct = (processed / total_tasks) * 100
                print(Fore.CYAN + f"[progress] {processed}/{total_tasks} ({pct:.1f}%) rate: {rate:.1f} checks/s")

    # רוקן את מה שנשאר
    flush_buffer(final=True)
    attempts_file.close()

    return open_ips

def main():
    global start_time
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
    start_time = time.time()

    for ip_range in IP_RANGES:
        print(Fore.CYAN + f"\nScanning {ip_range} ...")
        open_ips = scan_range(ip_range)
        all_open_ips.extend(open_ips)

    # שמירה לקובץ
    with open("ports.txt", "w") as f:
        for ip, port in all_open_ips:
            f.write(f"{ip}:{port}\n")

    elapsed = time.time() - start_time
    print(Fore.YELLOW + f"\nScan complete. Found {len(all_open_ips)} open ports. Elapsed: {elapsed:.2f}s")

if __name__ == "__main__":
    main()
