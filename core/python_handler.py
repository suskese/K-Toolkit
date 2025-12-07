import subprocess
import re

def ensure_python_and_uv(min_version="3.13.4"):
    import shutil
    import sys
    import tempfile
    import urllib.request
    import os
    # 1. Check for python >= min_version
    def version_tuple(v):
        return tuple(map(int, (v.split("."))))
    py_exec = shutil.which("python") or shutil.which("python3")
    found_version = None
    if py_exec:
        try:
            out = subprocess.check_output([py_exec, "--version"], text=True).strip()
            found_version = re.search(r"(\d+\.\d+\.\d+)", out)
            if found_version:
                found_version = found_version.group(1)
        except Exception:
            pass
    if not py_exec or not found_version or version_tuple(found_version) < version_tuple(min_version):
        # Use winget to install Python 3.13 if available (as in the module)
        print("Installing Python 3.13.4 via winget...")
        try:
            subprocess.run(["winget", "install", "Python.Python.3.13"], check=True)
        except Exception as e:
            raise RuntimeError(f"Failed to install Python 3.13.4 via winget: {e}")
        py_exec = shutil.which("python") or shutil.which("python3")
        # Re-check version
        out = subprocess.check_output([py_exec, "--version"], text=True).strip()
        found_version = re.search(r"(\d+\.\d+\.\d+)", out)
        if found_version:
            found_version = found_version.group(1)
        else:
            raise RuntimeError("Python 3.13.4 install failed")
    # 2. Ensure uv is installed
    try:
        subprocess.check_call(["uv", "--version"] or [py_exec, "uv", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        subprocess.check_call(["pip", "install", "uv"] or ["pip", "install", "uv"])
    return py_exec
    
def scan_and_install_missing_pkgs(modules_dir="modules"):
    """
    Scan all .py files in modules_dir for imports, try to install missing pkgs using uv pip install --system.
    """
    import ast
    import glob
    import sys
    import importlib
    py_exec = ensure_python_and_uv()
    # 1. Scan for imports
    pkgs = set()
    for pyfile in glob.glob(os.path.join(modules_dir, "*.py")):
        with open(pyfile, "r", encoding="utf-8", errors="ignore") as f:
            try:
                tree = ast.parse(f.read(), filename=pyfile)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for n in node.names:
                            pkgs.add(n.name.split(".")[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            pkgs.add(node.module.split(".")[0])
            except Exception:
                continue
    # 2. Try to import, collect missing
    missing = set()
    import_errors = {}
    for pkg in pkgs:
        try:
            importlib.import_module(pkg)
        except ImportError as e:
            missing.add(pkg)
            import_errors[pkg] = str(e)
    if not missing:
        print("All required packages are already installed.")
        return
    # Map import names to PyPI package names (shared with modules)
    install_name_map = {
        "cv2": "opencv-python",
        "PIL": "Pillow",
        "Crypto": "pycryptodome",
        "optparse": "optparse",
    }
    install_pkgs = [install_name_map.get(m, m) for m in missing]
    print(f"Missing packages: {missing}")
    print(f"Installing: {install_pkgs}")
    # 3. Try to install missing pkgs with uv pip install --system
    result = subprocess.run(["uv", "pip", "install", "--system"] + install_pkgs, capture_output=True, text=True)
    if result.returncode != 0:
        print("uv pip install failed:")
        print(result.stdout)
        print(result.stderr)
    # 4. Try to import again, print errors if still missing
    still_missing = set()
    for pkg in missing:
        try:
            importlib.import_module(pkg)
        except Exception as e:
            still_missing.add(pkg)
            print(f"[ERROR] After install, failed to import '{pkg}': {e}")
    if still_missing:
        print(f"[WARNING] Some packages could not be imported after install: {still_missing}")
        print("Check for system dependencies, correct wheel versions, or DLL issues.")
    # Optionally, print original import errors for context
    for pkg, err in import_errors.items():
        print(f"Original import error for {pkg}: {err}")
import sys
import os
import glob

def try_import_with_system_pip(module_name, package_hint=None):
    try:
        return __import__(module_name)
    except ImportError:
        # Try to find the package in all Python installations
        possible_dirs = []
        for path in os.environ["PATH"].split(os.pathsep):
            python_exe = os.path.join(path, "python.exe")
            if os.path.exists(python_exe):
                # Try to find site-packages
                for sp in glob.glob(os.path.join(path, "Lib", "site-packages")):
                    possible_dirs.append(sp)
        # Also try common locations
        for root in ["C:\\Python*", "C:\\Users\\*\\AppData\\Local\\Programs\\Python\\Python313"]:
            for py in glob.glob(root):
                sp = os.path.join(py, "Lib", "site-packages")
                if os.path.exists(sp):
                    possible_dirs.append(sp)
        # Try to import from those
        for sp in possible_dirs:
            if package_hint:
                if not os.path.exists(os.path.join(sp, package_hint)):
                    continue
            if sp not in sys.path:
                sys.path.insert(0, sp)
            try:
                return __import__(module_name)
            except ImportError:
                continue
        raise

