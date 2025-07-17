import os
import sys
from pathlib import Path
import subprocess # subprocess modülü buraya eklendi!

# Projenizin ana dizini
basedir = Path(__file__).parent 

# Sanal ortamın Python yorumlayıcısının yolu
python_executable = Path(sys.executable) # python_executable doğru tanımlandı!


def run_babel_command_via_pybabel(subcommand):
    """
    Doğrudan 'pybabel' komutunu subprocess ile çalıştırır.
    """

    # pybabel komutu ve alt komutu
    command = [str(python_executable), '-m', 'babel.messages.frontend']

    if subcommand == 'extract':
        command.extend(['extract', '-F', str(basedir / 'babel.cfg'), '-o', str(basedir / 'messages.pot'), str(basedir)])
    elif subcommand == 'update':
        command.extend(['update', '-i', str(basedir / 'messages.pot'), '-d', str(basedir / 'translations')])
    elif subcommand == 'compile':
        command.extend(['compile', '-d', str(basedir / 'translations')])
    else:
        raise ValueError(f"Bilinmeyen alt komut: {subcommand}")

    print(f"\nÇalıştırılıyor: {' '.join(command)}")

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("STDOUT:\n", result.stdout)
        if result.stderr:
            print("STDERR:\n", result.stderr)
        print(f"Komut 'pybabel {subcommand}' başarıyla tamamlandı.")
    except subprocess.CalledProcessError as e:
        print(f"Hata oluştu 'pybabel {subcommand}' komutu çalışırken:")
        print("STDOUT:\n", e.stdout)
        print("STDERR:\n", e.stderr)
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("Hata: 'python' veya 'pybabel' komutu bulunamadı. Sanal ortamınızın etkin olduğundan ve Babel'in kurulu olduğundan emin olun.")
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Kullanım: python run_babel.py [extract|update|compile]")
        sys.exit(1)

    command = sys.argv[1]

    run_babel_command_via_pybabel(command)