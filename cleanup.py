import os

archivos_a_borrar = [
    "debug_smtp.py",
    "test_email.py",
    "get_git_log.py"
]

for archivo in archivos_a_borrar:
    try:
        if os.path.exists(archivo):
            os.remove(archivo)
            print(f"Eliminado: {archivo}")
    except Exception as e:
        print(f"Error al eliminar {archivo}: {e}")
