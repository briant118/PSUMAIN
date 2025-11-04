import subprocess
import platform


def ping(ip_address):
    # Use correct param for Windows (-n) or Linux/Mac (-c)
    param = "-n" if platform.system().lower() == "windows" else "-c"

    result = subprocess.run(
        ["ping", param, "1", ip_address],
        capture_output=True,
        text=True
    )

    output = result.stdout.lower()

    # On Windows: success contains "reply from" without "unreachable"
    # On Linux/Mac: success contains "bytes from"
    if ("reply from" in output and "unreachable" not in output) or ("bytes from" in output):
        return True
    return False
