# -*- coding: utf-8 -*-
import os
import platform
import re
import shutil
import subprocess
import time
import zipfile

import requests


def download_file(url, filename):

    if os.path.isfile(filename):
        return

    r = requests.get(url, stream=True)
    total_size = int(r.headers.get('content-length', 0))
    bytes_downloaded = 0
    previows_progress = 0
    start_time = time.time()

    if total_size >= 1024 * 1024:
        total_txt = f"{total_size / (1024 * 1024):.2f} MB"
    else:
        total_txt = f"{total_size / 1024:.2f} KB"

    with open(f"{filename}.tmp", 'wb') as f:

        for data in r.iter_content(chunk_size=2500*1024):
            f.write(data)
            bytes_downloaded += len(data)
            try:
                current_progress = int((bytes_downloaded / total_size) * 100)
            except ZeroDivisionError:
                current_progress = 0

            if current_progress != previows_progress:
                previows_progress = current_progress
                time_elapsed = time.time() - start_time
                try:
                    download_speed = bytes_downloaded / time_elapsed / 1024
                    if download_speed >= 1:
                        download_speed = (download_speed or 1) / 1024
                        speed_txt = "MB/s"
                    else:
                        speed_txt = "KB/s"
                    print(f"Download do arquivo {filename} {current_progress}% concluído ({download_speed:.2f} {speed_txt} / {total_txt})")
                except:
                    print(f"Download do arquivo {filename} {current_progress}% concluído")

    r.close()

    os.rename(f"{filename}.tmp", filename)

    return True

def validate_java(cmd: str, debug: bool = False):
    try:
        java_info = subprocess.check_output(f'{cmd} -version', shell=True, stderr=subprocess.STDOUT)
        java_version = re.search(r'\d+', java_info.decode().split("\r")[0]).group().replace('"', '')
        if int(java_version.split('.')[0]) >= 17:
            return cmd
    except Exception as e:
        if debug:
            print(f"\nFalha ao obter versão do java...\n"
                  f"Path: {cmd} | Erro: {repr(e)}\n")

def run_lavalink(
        lavalink_file_url: str = None,
        lavalink_initial_ram: int = 30,
        lavalink_ram_limit: int = 100,
        lavalink_additional_sleep: int = 0,
        lavalink_cpu_cores: int = 1,
        use_jabba: bool = False,
        yt_oauth_refresh_token: str = "",
):
    arch = platform.machine().lower()
    if arch in ("x86_64", "amd64"):
        jdk_arch = "amd64"
    elif arch in ("aarch64", "arm64"):
        jdk_arch = "aarch64"
    elif arch in ("i386", "i686", "x86"):
        jdk_arch = "i586"
    else:
        jdk_arch = "amd64"
    osname = platform.system()
    jdk_platform = f"{osname}-{arch}"

    if not (java_cmd := validate_java("java")):

        dirs = []

        try:
            dirs.append(os.path.join(os.environ["JAVA_HOME"] + "bin/java"))
        except KeyError:
            pass

        if os.name == "nt":
            dirs.append(os.path.realpath(f"./.java/{jdk_platform}/bin/java"))
            try:
                shutil.rmtree("./.jabba")
            except:
                pass

        else:
            if use_jabba:
                dirs.extend(
                    [
                        os.path.realpath("./.jabba/jdk/zulu@1.17.0-0/bin/java"),
                        os.path.expanduser("./.jabba/jdk/zulu@1.17.0-0/bin/java")
                    ]
                )
                try:
                    shutil.rmtree("./.java")
                except:
                    pass

            else:
                dirs.append(os.path.realpath(f"./.java/{jdk_platform}/bin/java"))
                try:
                    shutil.rmtree("./.jabba")
                except:
                    pass

        for cmd in dirs:
            if validate_java(cmd):
                java_cmd = cmd
                break

        if not java_cmd:

            if os.name == "nt":

                try:
                    shutil.rmtree("./.java")
                except:
                    pass

                jdk_url = f"https://download.bell-sw.com/java/21.0.3+12/bellsoft-jdk21.0.3+12-windows-{jdk_arch}-lite.zip"

                jdk_filename = "java.zip"

                download_file(jdk_url, jdk_filename)

                with zipfile.ZipFile(jdk_filename, 'r') as zip_ref:
                    zip_ref.extractall(f"./.java/{jdk_platform}")

                extracted_folder = os.path.join(f"./.java/{jdk_platform}", os.listdir(f"./.java/{jdk_platform}")[0])

                for item in os.listdir(extracted_folder):
                    item_path = os.path.join(extracted_folder, item)
                    dest_path = os.path.join(f"./.java/{jdk_platform}", item)
                    os.rename(item_path, dest_path)

                os.remove(jdk_filename)

                java_cmd = os.path.realpath(f"./.java/{jdk_platform}/bin/java")

            elif use_jabba:

                try:
                    shutil.rmtree("./.jabba/jdk/zulu@1.17.0-0")
                except:
                    pass

                download_file("https://raw.githubusercontent.com/shyiko/jabba/master/install.sh", "install_jabba.sh")
                subprocess.call("bash install_jabba.sh", shell=True)
                subprocess.call("./.jabba/bin/jabba install zulu@1.17.0-0", shell=True)
                os.remove("install_jabba.sh")

                java_cmd = os.path.expanduser("./.jabba/jdk/zulu@1.17.0-0/bin/java")

            else:
                if not os.path.isdir(f"./.java/{jdk_platform}"):

                    try:
                        shutil.rmtree("./.java")
                    except:
                        pass

                    jdk_url = f"https://download.bell-sw.com/java/21.0.3+12/bellsoft-jdk21.0.3+12-linux-{jdk_arch}-lite.tar.gz"

                    java_cmd = os.path.realpath(f"./.java/{jdk_platform}/bin/java")

                    jdk_filename = "java.tar.gz"

                    download_file(jdk_url, jdk_filename)

                    try:
                        shutil.rmtree("./.java")
                    except:
                        pass

                    os.makedirs(f"./.java/{jdk_platform}")

                    p = subprocess.Popen(["tar", "--strip-components=1", "-zxvf", "java.tar.gz", "-C", f"./.java/{jdk_platform}"])
                    p.wait()
                    os.remove(f"./{jdk_filename}")

                else:
                    java_cmd = os.path.realpath(f"./.java/{jdk_platform}/bin/java")

    for filename, url in (
        ("Lavalink.jar", lavalink_file_url),
        ("application.yml", "https://github.com/zRitsu/LL-binaries/releases/download/0.0.1/application.yml"),
    ):
        download_file(url, filename)

    if not os.path.isfile("application.yml"):
        if os.path.isfile("application.template.yml"):
            import shutil as _su
            _su.copy2("application.template.yml", "application.yml")
            print("application.yml copiado do template local (fallback)")

    if yt_oauth_refresh_token and os.path.isfile("application.yml"):
        try:
            with open("application.yml", "r", encoding="utf-8") as f:
                content = f.read()

            # Enable OAuth and set token - handle both possible field names
            for old_line in ('refreshToken: ""', 'token: ""'):
                if old_line in content:
                    new_line = old_line.replace('""', f'"{yt_oauth_refresh_token}"')
                    content = content.replace(old_line, new_line)
                    break

            # Also ensure oauth is enabled
            content = content.replace('enabled: false', 'enabled: true', 1)

            with open("application.yml", "w", encoding="utf-8") as f:
                f.write(content)
            print("OAuth2 configurado com token no application.yml")
        except Exception as e:
            print(f"AVISO: Erro ao configurar OAuth2 no application.yml: {e}")

    if lavalink_cpu_cores >= 1:
        java_cmd += f" -XX:ActiveProcessorCount={lavalink_cpu_cores}"

    if lavalink_ram_limit > 10:
        java_cmd += f" -Xmx{lavalink_ram_limit}m"

    if 0 < lavalink_initial_ram < lavalink_ram_limit:
        java_cmd += f" -Xms{lavalink_ram_limit}m"

    if os.name != "nt":
        if os.path.isdir("./.tempjar"):
            shutil.rmtree("./.tempjar")
        os.makedirs("./.tempjar/undertow-docbase.80.2258596138812103750")
        java_cmd += f" -Djava.io.tmpdir={os.getcwd()}/.tempjar"

    if not os.path.isdir("./plugins"):
        os.makedirs("./plugins", exist_ok=True)

    java_cmd += " -jar Lavalink.jar"

    print("🌋 - Iniciando o servidor Lavalink (dependendo da hospedagem o lavalink pode demorar iniciar, "
          "o que pode ocorrer falhas em algumas tentativas de conexão até ele iniciar totalmente).")

    lavalink_process = subprocess.Popen(
        java_cmd.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
    )

    def _forward_lavalink_output():
        for line in iter(lavalink_process.stdout.readline, ""):
            if line:
                print(f"[Lavalink] {line}", end="")
                if "user_code" in line.lower() or "please authenticate" in line.lower() or "device?user_code" in line.lower():
                    print("\n⚠️  URL OAuth2 do YouTube detectada! Acesse o link acima para autenticar no Lavalink.\n")

    import threading
    _forward_thread = threading.Thread(target=_forward_lavalink_output, daemon=True)
    _forward_thread.start()

    if lavalink_additional_sleep:
        print(f"🕙 - Aguarde {lavalink_additional_sleep} segundos...")
        time.sleep(lavalink_additional_sleep)

    return lavalink_process
