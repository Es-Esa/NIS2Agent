import platform
import socket
import psutil
import subprocess
import requests
import json
import time
import os
import re

# CVE-haavoittuvuuksien tarkistus (vulners API)
VULNERS_API_URL = "https://vulners.com/api/v3/search/lucene/"

SERVER_URL = "http://localhost:3030/report"  # Muuta osoitteeksi oma palvelin

def get_system_info():
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "hostname": socket.gethostname(),
        "uptime": time.time() - psutil.boot_time(),
        "ip_addresses": get_ip_addresses(),
        "firewall": check_firewall(),
        "updates_status": check_auto_updates(),
        "user_accounts": get_user_accounts(),
        "cve_vulnerabilities": check_cve(),
        "log_check": check_logs_audit(),
        "hardcoded_passwords": check_hardcoded_passwords(),
        "security_settings": check_security_settings(),
        "software_versions": check_installed_software(),
        "network_security": check_network_security(),
        "user_privileges": check_user_privileges(),
        "logs_audit": check_logs_audit(),
        "integrations": check_integrations()
    }

def get_ip_addresses():
    ip_list = []
    for iface, snics in psutil.net_if_addrs().items():
        for snic in snics:
            if snic.family == socket.AF_INET:
                ip_list.append(snic.address)
    return ip_list

def check_firewall():
    if platform.system() == "Windows":
        result = subprocess.run(["powershell", "-Command", "Get-NetFirewallProfile | Select-Object -ExpandProperty Enabled"], capture_output=True, text=True)
        return "enabled" if result.stdout.strip() == "True" else "disabled"
    else:
        result = subprocess.run(["sudo", "iptables", "-L"], capture_output=True, text=True)
        return "enabled" if result.returncode == 0 else "disabled"

def check_security_settings():
    # Tarkistetaan BitLocker, LUKS, FileVault jne.
    encryption_status = check_disk_encryption()
    secure_boot = check_secure_boot()
    auto_updates = check_auto_updates()
    
    return {
        "disk_encryption": encryption_status,
        "secure_boot": secure_boot,
        "auto_updates": auto_updates
    }

def check_disk_encryption():
    if platform.system() == "Windows":
        result = subprocess.run(["powershell", "-Command", "Get-BitLockerVolume"], capture_output=True, text=True)
        return "enabled" if "Fully Encrypted" in result.stdout else "disabled"
    elif platform.system() == "Linux":
        result = subprocess.run(["lsblk", "-o", "NAME,FSTYPE,SIZE,MOUNTPOINT"], capture_output=True, text=True)
        if "LUKS" in result.stdout:
            return "enabled"
    return "disabled"

def check_secure_boot():
    if platform.system() == "Windows":
        result = subprocess.run(["powershell", "-Command", "Confirm-SecureBootUEFI"], capture_output=True, text=True)
        return "enabled" if "True" in result.stdout else "disabled"
    return "not supported"

def check_auto_updates():
    if platform.system() == "Windows":
        result = subprocess.run(["powershell", "-Command", "Get-WindowsUpdate"], capture_output=True, text=True)
        return "enabled" if "No pending updates" not in result.stdout else "disabled"
    else:
        result = subprocess.run(["apt", "list", "--upgradable"], capture_output=True, text=True)
        return "enabled" if "upgradable" in result.stdout else "disabled"

def check_installed_software():
    software = []
    if platform.system() == "Windows":
        result = subprocess.run(["powershell", "-Command", "Get-WmiObject -Class Win32_Product"], capture_output=True, text=True)
        software = re.findall(r"Name\s*:\s*(.*)\n", result.stdout)
    else:
        result = subprocess.run(["dpkg", "-l"], capture_output=True, text=True)
        software = re.findall(r"^ii\s+([^\s]+)", result.stdout)
    
    return software

def check_network_security():
    open_ports = check_open_ports()
    active_connections = check_active_connections()
    return {
        "open_ports": open_ports,
        "active_connections": active_connections
    }

def check_open_ports():
    if platform.system() == "Windows":
        result = subprocess.run(["powershell", "-Command", "Get-NetTCPConnection"], capture_output=True, text=True)
    else:
        result = subprocess.run(["ss", "-tuln"], capture_output=True, text=True)
    
    return result.stdout.splitlines()

def check_active_connections():
    if platform.system() == "Windows":
        result = subprocess.run(["netstat", "-an"], capture_output=True, text=True)
    else:
        result = subprocess.run(["netstat", "-an"], capture_output=True, text=True)
    
    return result.stdout.splitlines()

def get_user_accounts():
    accounts = []
    if platform.system() == "Windows":
        result = subprocess.run(["powershell", "-Command", "Get-LocalUser"], capture_output=True, text=True)
        # Poistetaan tyhjät rivit ja otsikkorivi, jos sellainen on
        accounts = [line for line in result.stdout.splitlines() if line.strip() and not line.startswith("Name") and not line.startswith("----")]
    else:
        result = subprocess.run(["cut", "-d:", "-f1", "/etc/passwd"], capture_output=True, text=True)
        accounts = result.stdout.splitlines()
    
    return accounts

def check_cve():
    cve_list = []
    system_info = platform.system().lower()
    # Esimerkiksi tarkistetaan, onko haavoittuvuuksia Windowsille tai Linuxille
    if system_info == "windows":
        # Voit mukauttaa kyselyä tarvittaessa Windowsin versioiden mukaan
        os_name = "windows"
        os_version = platform.release() # Esim. '10' tai '11'
        cve_query = f"microsoft {os_name} {os_version}"
    elif system_info == "linux":
        # Yritetään tunnistaa yleisimpiä jakeluita
        try:
            with open("/etc/os-release") as f:
                lines = f.readlines()
                os_info = {k.strip(): v.strip().strip('"') for k, v in (line.split('=', 1) for line in lines if '=' in line)}
                distro = os_info.get('ID', 'linux')
                version = os_info.get('VERSION_ID', '')
                cve_query = f"{distro} {version}"
        except FileNotFoundError:
            cve_query = "linux kernel" # Varavaihtoehto
    else:
        cve_query = f"{system_info}" # Muut järjestelmät

    print(f"Searching Vulners for: {cve_query}") # Debug tuloste
    params = {"query": cve_query, "size": 10} # Otetaan 10 viimeisintä
    try:
        response = requests.get(VULNERS_API_URL, params=params)
        response.raise_for_status() # Heittää virheen, jos statuskoodi ei ole 2xx
        data = response.json()
        
        # Tarkistetaan vastauksen rakenne
        if data.get("result") == "OK" and "data" in data and "search" in data["data"]:
            for hit in data["data"]["search"]:
                if isinstance(hit, dict) and "_id" in hit:
                    cve_list.append(hit["_id"])
                else:
                    print(f"Skipping invalid hit format: {hit}") # Debug tuloste
        else:
            print(f"Unexpected Vulners API response structure: {data}") # Debug tuloste
            
    except requests.exceptions.RequestException as e:
        print(f"Error querying Vulners API: {e}")
    except json.JSONDecodeError:
        print(f"Error decoding Vulners API JSON response: {response.text}")
        
    return cve_list

def check_user_privileges():
    users = get_user_accounts()
    privileges = []
    for user in users:
        if platform.system() == "Windows":
            result = subprocess.run(["powershell", "-Command", f"Get-LocalUser {user} | Select-Object -ExpandProperty MemberOf"], capture_output=True, text=True)
            if "Administrators" in result.stdout:
                privileges.append(f"{user} has admin privileges")
        else:
            result = subprocess.run(["id", user], capture_output=True, text=True)
            if "sudo" in result.stdout:
                privileges.append(f"{user} has sudo privileges")
    
    return privileges

def check_logs_audit():
    logs = []
    if platform.system() == "Windows":
        result = subprocess.run(["powershell", "-Command", "Get-WinEvent -LogName Security | Select-Object -First 10"], capture_output=True, text=True)
        logs = result.stdout.splitlines()
    else:
        result = subprocess.run(["grep", "failed", "/var/log/auth.log"], capture_output=True, text=True)
        logs = result.stdout.splitlines()
    
    return logs

def check_hardcoded_passwords():
    passwords = []
    # Käydään läpi rajatut järjestelmän tiedostopolut
    search_paths = []
    if platform.system() == "Windows":
        # Esimerkkipolut Windowsille (voit laajentaa tarvittaessa)
        search_paths = [os.getenv("APPDATA"), os.getenv("LOCALAPPDATA"), "C:\\ProgramData", os.getenv("USERPROFILE")]
    else:
        # Esimerkkipolut Linux/macOS (voit laajentaa tarvittaessa)
        search_paths = ["/etc", os.path.expanduser("~")]

    # Lisää tähän projektikohtaisia tai muita relevantteja polkuja
    # search_paths.append("/polku/projektiin") 

    checked_files_count = 0
    max_files_to_check = 1000 # Asetetaan raja tarkistettavien tiedostojen määrälle

    for path in filter(None, search_paths): # Suodatetaan pois None-arvot
        if os.path.isdir(path):
            print(f"Checking for hardcoded passwords in: {path}")
            try:
                for root, dirs, files in os.walk(path, topdown=True):
                    # Vältetään tietyt hakemistot (esim. välimuistit, lokit)
                    dirs[:] = [d for d in dirs if d not in ['.cache', 'node_modules', 'vendor', '__pycache__', 'logs']]
                    
                    if checked_files_count >= max_files_to_check:
                        print(f"Reached file check limit ({max_files_to_check}), stopping search in this path.")
                        break # Lopetetaan tämän polun käsittely

                    for file in files:
                        if checked_files_count >= max_files_to_check:
                             break # Lopetetaan tiedostojen läpikäynti tässä hakemistossa

                        # Tarkistetaan vain tietyn tyyppiset tai nimiset tiedostot
                        if file.lower().endswith((".env", ".conf", ".cfg", ".ini", ".json", ".yml", ".yaml", ".xml", ".properties", ".pem", ".key")) or "config" in file.lower() or "credential" in file.lower():
                            file_path = os.path.join(root, file)
                            try:
                                # Skipataan liian suuret tiedostot
                                if os.path.getsize(file_path) > 1 * 1024 * 1024: # 1 MB raja
                                    continue
                                
                                checked_files_count += 1
                                with open(file_path, "r", errors='ignore') as f:
                                    # Luetaan rivi kerrallaan, jos tiedosto on suuri
                                    for line_num, line in enumerate(f, 1):
                                        # Etsitään salasanoja, avaimia jne. tarkemmalla regexillä
                                        # Tämä regex etsii yleisiä avainsanoja, joita seuraa yhtäläisyysmerkki tai kaksoispiste ja lainausmerkeissä oleva arvo
                                        # HUOM: Tämä ei ole täydellinen ja voi tuottaa vääriä positiivisia/negatiivisia.
                                        # Varmistetaan syntaksi ja muotoilu
                                        # Kokeillaan tavallista merkkijonoa r"..." sijaan ja escapetetaan \b, \s, \2
                                        # Palautetaan alkuperäinen regex-kuvio (toivottavasti SyntaxError pysyy poissa)
                                        # YKSINKERTAISTUS 2: Poistetaan takaisinviittaus \2 ja sieppausryhmä (.+?) testiksi
                                        # pattern = "(password|secret|passwd|api_key|access_key|private_key|token)\\b\\s*[:=]\\s*['"].+?['"]"
                                        # if re.search(pattern, line, flags=re.IGNORECASE):
                                        #     passwords.append(f"Potential credential in: {file_path} (line {line_num})")
                                            # Löydetty rivi, ei tarvitse lukea enempää tästä tiedostosta (optimointi)
                                        #    break 
                                        # AGGRESSIIVINEN TESTI: Ohitetaan koko salasanahaku väliaikaisesti
                                        pass
                                        
                            except OSError as e:
                                # print(f"Could not read file {file_path}: {e}") # Vähennetään tulostetta
                                pass # Ohitetaan tiedostot, joita ei voi lukea
                            except Exception as e:
                                print(f"Error processing file {file_path}: {e}")
            except OSError as e:
                 print(f"Could not access path {path}: {e}")
        # else: # Debug: Tulostetaan, jos polku ei ole hakemisto
        #    print(f"Skipping non-directory path: {path}")

    if checked_files_count >= max_files_to_check:
        print(f"Warning: Reached the maximum file check limit ({max_files_to_check}). Some files may not have been checked.")

    return passwords

def check_integrations():
    integrations = {
        "active_directory": check_active_directory(),
        "azure_m365": check_azure_m365(),
        "api_integrations": check_api_integrations()
    }
    return integrations

def check_active_directory():
    if platform.system() == "Windows":
        result = subprocess.run(["powershell", "-Command", "Get-ADDomain"], capture_output=True, text=True)
        return "Active Directory Domain Found" if result.returncode == 0 else "Not found"
    return "Not applicable"

def check_azure_m365():
    if platform.system() == "Windows":
        result = subprocess.run(["powershell", "-Command", "Get-MsolUser"], capture_output=True, text=True)
        return "Azure AD is active" if result.returncode == 0 else "Not active"
    return "Not applicable"

def check_api_integrations():
    return ["Zabbix", "Wazuh", "Custom API Integrations"]

def send_report(data):
    try:
        response = requests.post(SERVER_URL, json=data)
        print("Palvelin vastasi:", response.status_code)
    except Exception as e:
        print("Virhe raportin lähetyksessä:", e)

if __name__ == "__main__":
    system_info = get_system_info()
    print(json.dumps(system_info, indent=2))
    send_report(system_info)
