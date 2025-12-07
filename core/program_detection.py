import os
import glob
import subprocess
import winreg

def get_installed_programs_via_start_menu():
    # Search Start Menu for all .lnk shortcuts (indexed by Windows Search)
    start_menu_dirs = [
        os.path.expandvars(r'%APPDATA%\Microsoft\Windows\Start Menu\Programs'),
        os.path.expandvars(r'%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs')
    ]
    found = {}
    for base in start_menu_dirs:
        for lnk in glob.glob(os.path.join(base, '**', '*.lnk'), recursive=True):
            name = os.path.splitext(os.path.basename(lnk))[0]
            found[name] = lnk
    return found

def get_installed_programs_via_registry():
    # Query uninstall keys for installed programs
    uninstall_keys = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]
    found = {}
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for key_path in uninstall_keys:
            try:
                with winreg.OpenKey(root, key_path) as key:
                    for i in range(0, winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                found[display_name] = subkey_name
                        except Exception:
                            continue
            except Exception:
                continue
    return found

def detect_programs_by_name(program_names):
    # Returns dict: {name: found_path or None}
    import shutil
    import subprocess
    found = {}
    start_menu = get_installed_programs_via_start_menu()
    registry = get_installed_programs_via_registry()
    # Scan Program Files and Program Files (x86) for installed programs
    program_dirs = [
        os.environ.get('ProgramFiles', r'C:\Program Files'),
        os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'),
        os.environ.get('PROGRAMDATA', r'C:\ProgramData'),
        os.path.expandvars(r'%ALLUSERSPROFILE%'),
        os.path.expandvars(r'%APPDATA%'),
        os.path.expandvars(r'%LOCALAPPDATA%'),
    ]
    exe_hints = {
        '7-Zip': ['7zFM.exe', '7z.exe'],
        'FFmpeg': ['ffmpeg.exe'],
        'Everything': ['Everything.exe'],
        'VLC': ['vlc.exe'],
        'Roblox': ['RobloxPlayerBeta.exe'],
        'Roblox Studio': ['RobloxStudioBeta.exe'],
        'Roblox Player': ['RobloxPlayerBeta.exe'],
        'Cheat Engine': ['cheatengine-x86_64.exe', 'cheatengine.exe'],
        'Discord': ['Discord.exe'],
        'Reg Organizer': ['RegOrganizer.exe'],
        'WizTree': ['WizTree64.exe', 'WizTree.exe'],
        'Prism Launcher': ['PrismLauncher.exe'],
        'IntelliJ IDEA': ['idea64.exe', 'idea.exe'],
        'Visual Studio Code': ['Code.exe'],
        'Visual Studio': ['devenv.exe', 'vswhere.exe', 'vs.exe', 'VisualStudio.exe', 'visual studio 2022.exe'],
        'SkyClient': ['SkyClient.exe'],
        'WinSCP': ['WinSCP.exe'],
        'K-Lite Codec Pack Mega': ['klcp_mega.exe', 'CodecTweakTool.exe'],
        'Phone Link': ['PhoneExperienceHost.exe'],
        'Python': ['python.exe', 'python3.exe'],
        'Eclipse Temurin JDK 8': ['java.exe'],
        'Eclipse Temurin JDK 11': ['java.exe'],
        'Eclipse Temurin JDK 17': ['java.exe'],
        'Eclipse Temurin JDK 21': ['java.exe'],
    }
    folder_hints = {
        '7-Zip': ['7-Zip'],
        'FFmpeg': ['ffmpeg', 'FFmpeg'],
        'Everything': ['Everything'],
        'VLC': ['VideoLAN', 'VLC'],
        'Roblox': ['Roblox'],
        'Roblox Studio': ['Roblox'],
        'Roblox Player': ['Roblox'],
        'Cheat Engine': ['Cheat Engine'],
        'Discord': ['Discord'],
        'Reg Organizer': ['Reg Organizer', 'RegOrganizer'],
        'WizTree': ['WizTree'],
        'WinSCP': ['WinSCP'],
        'Prism Launcher': ['PrismLauncher', 'Prism Launcher'],
        'IntelliJ IDEA': ['JetBrains', 'IntelliJ IDEA Community Edition', 'IntelliJ IDEA'],
        'Visual Studio Code': ['Microsoft VS Code', 'VSCode', 'Visual Studio Code'],
        'Visual Studio': ['Microsoft Visual Studio', 'Visual Studio', 'Visual Studio 2022', '2022'],
        'SkyClient': ['SkyClient'],
        'K-Lite Codec Pack Mega': ['K-Lite Codec Pack'],
        'Phone Link': ['PhoneExperienceHost', 'Phone Link'],
        'Python': ['Python', 'Python3'],
        'Eclipse Temurin JDK 8': ['Eclipse Foundation', 'Eclipse Adoptium', 'Adoptium', 'Java', 'jdk-8'],
        'Eclipse Temurin JDK 11': ['Eclipse Foundation', 'Eclipse Adoptium', 'Adoptium', 'Java', 'jdk-11'],
        'Eclipse Temurin JDK 17': ['Eclipse Foundation', 'Eclipse Adoptium', 'Adoptium', 'Java', 'jdk-17'],
        'Eclipse Temurin JDK 21': ['Eclipse Foundation', 'Eclipse Adoptium', 'Adoptium', 'Java', 'jdk-21'],
    }
    for name in program_names:
        exe_path = None
        # 1. Try PATH (for common exe names)
        for exe in exe_hints.get(name, []):
            exe_path = shutil.which(exe)
            # For 7-Zip, ignore system32
            if exe_path and name == '7-Zip' and exe_path.lower().startswith(os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'system32').lower()):
                exe_path = None
            # For Visual Studio, prefer devenv.exe in a path containing 'Visual Studio'
            if exe_path and name == 'Visual Studio' and 'devenv.exe' in exe_path.lower() and 'visual studio' not in exe_path.lower():
                exe_path = None
            # For JDKs, check version in path
            if exe_path and name.startswith('Eclipse Temurin JDK'):
                # Extract version from name
                import re
                jdk_version = re.search(r'JDK (\d+)', name)
                if jdk_version:
                    jdk_version = jdk_version.group(1)
                    # Try to find version in path (e.g. zulu\\21 or jdk-21)
                    if not (f"zulu{jdk_version}" in exe_path or f"jdk-{jdk_version}" in exe_path or f"\\{jdk_version}\\" in exe_path or f"-{jdk_version}\\" in exe_path):
                        exe_path = None
            if exe_path:
                break
        # 2. Try searching PATH env for java/python (all JDKs, Python)
        if not exe_path and name in [
            'Python', 'Eclipse Temurin JDK 8', 'Eclipse Temurin JDK 11', 'Eclipse Temurin JDK 17', 'Eclipse Temurin JDK 21', 'IntelliJ IDEA', 'Visual Studio Code']:
            try:
                path_env = os.environ.get('PATH', '')
                for exe in exe_hints.get(name, []):
                    for p in path_env.split(os.pathsep):
                        candidate = os.path.join(p, exe)
                        if os.path.exists(candidate):
                            # For JDKs, check version in path
                            if name.startswith('Eclipse Temurin JDK'):
                                import re
                                jdk_version = re.search(r'JDK (\d+)', name)
                                if jdk_version:
                                    jdk_version = jdk_version.group(1)
                                    if not (f"zulu{jdk_version}" in candidate or f"jdk-{jdk_version}" in candidate or f"\\{jdk_version}\\" in candidate or f"-{jdk_version}\\" in candidate):
                                        continue
                            exe_path = candidate
                            break
                    if exe_path:
                        break
            except Exception:
                pass
        # 3. Try only specific folders in Program Files, ProgramData, AppData
        if not exe_path:
            for exe in exe_hints.get(name, []):
                for base_dir in program_dirs:
                    if not base_dir or not os.path.exists(base_dir):
                        continue
                    for folder_hint in folder_hints.get(name, []):
                        folder_path = os.path.join(base_dir, folder_hint)
                        if os.path.exists(folder_path):
                            candidate = os.path.join(folder_path, exe)
                            if os.path.exists(candidate):
                                # For 7-Zip, ignore system32
                                if name == '7-Zip' and candidate.lower().startswith(os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'system32').lower()):
                                    continue
                                exe_path = candidate
                                break
                    if exe_path:
                        break
                if exe_path:
                    break
        # 4. Special case for VSCode: check AppData/Local/Programs/Microsoft VS Code
        if not exe_path and name == 'Visual Studio Code':
            local_vscode = os.path.expandvars(r'%LOCALAPPDATA%\\Programs\\Microsoft VS Code\\Code.exe')
            if os.path.exists(local_vscode):
                exe_path = local_vscode
        # 4b. Special case for Visual Studio 2022: check default install path
        if not exe_path and name == 'Visual Studio':
            vs2022_path = r'C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\Common7\\IDE\\devenv.exe'
            if os.path.exists(vs2022_path):
                exe_path = vs2022_path
        # 5. Try registry
        if not exe_path:
            match = next((prog for prog in registry if name.lower() in prog.lower()), None)
            if match:
                # Special case: Visual Studio registry returns subkey, not exe path
                if name == 'Visual Studio':
                    vs2022_path = r'C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\Common7\\IDE\\devenv.exe'
                    if os.path.exists(vs2022_path):
                        exe_path = vs2022_path
                    else:
                        vs_lnk = os.path.expandvars(r'%PROGRAMDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Visual Studio 2022.lnk')
                        if os.path.exists(vs_lnk):
                            exe_path = vs_lnk
                        else:
                            exe_path = None
                # Special case: WinSCP registry returns subkey, not exe path
                elif name == 'WinSCP':
                    # Try known install path
                    winscp_path = r'C:\\Program Files (x86)\\WinSCP\\WinSCP.exe'
                    if os.path.exists(winscp_path):
                        exe_path = winscp_path
                    else:
                        winscp_path2 = r'C:\\Program Files\\WinSCP\\WinSCP.exe'
                        if os.path.exists(winscp_path2):
                            exe_path = winscp_path2
                        else:
                            exe_path = None
                else:
                    exe_path = registry[match]
        # 6. Try start menu shortcut (especially for VSCode)
        if not exe_path:
            match = next((lnk for prog, lnk in start_menu.items() if name.lower() in prog.lower()), None)
            if match:
                exe_path = match
        found[name] = exe_path if exe_path else None
    return found

def uninstall_program_by_registry_key(reg_key):
    # Try to run the uninstall string from registry
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\\" + reg_key
        ) as subkey:
            uninstall_str, _ = winreg.QueryValueEx(subkey, "UninstallString")
            subprocess.Popen(uninstall_str, shell=True)
            return True
    except Exception:
        pass
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\\" + reg_key
        ) as subkey:
            uninstall_str, _ = winreg.QueryValueEx(subkey, "UninstallString")
            subprocess.Popen(uninstall_str, shell=True)
            return True
    except Exception:
        pass
    return False
