import os
import shutil
import subprocess

def ejecutar_comando(comando):
    print(f"\n> Ejecutando: {comando}")
    try:
        subprocess.run(comando, shell=True, check=True)
        print("  [OK]")
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] El comando falló con código {e.returncode}")

def aplicar_cambios():
    print("="*50)
    print(" INICIANDO ADAPTACIÓN A SMARTCAMPUS UTA WEB")
    print("="*50)

    # 1. Eliminar carpetas viejas de U-Ride
    print("\n1. Limpiando carpetas y módulos antiguos...")
    
    if os.path.exists("migrations"):
        shutil.rmtree("migrations")
        print("  - Carpeta 'migrations' eliminada.")
        
    if os.path.exists("app/viajes"):
        shutil.rmtree("app/viajes")
        print("  - Carpeta 'app/viajes' eliminada.")

    # 2. Crear nuevas carpetas para SmartCampus
    print("\n2. Creando carpetas para nuevos módulos (Capa de Aplicación)...")
    nuevos_modulos = ["app/tramites", "app/organizacion", "app/campus", "app/atencion"]
    
    for modulo in nuevos_modulos:
        os.makedirs(modulo, exist_ok=True)
        # Crear __init__.py vacio para que sean paquetes válidos
        with open(os.path.join(modulo, "__init__.py"), "w") as f:
            pass
        print(f"  - Carpeta '{modulo}' creada y preparada.")

    # 3. Inicializar Base de Datos nueva
    print("\n3. Reiniciando la Base de Datos con nuevos Modelos...")
    ejecutar_comando("python init_smartcampus_db.py")

    # 4. Configurar Flask Migrate
    print("\n4. Generando el nuevo control de versiones de Base de Datos...")
    ejecutar_comando("flask db init")
    ejecutar_comando("flask db migrate -m \"Migracion a SmartCampus\"")
    ejecutar_comando("flask db upgrade")

    print("\n" + "="*50)
    print(" ¡ADAPTACIÓN ESTRUCTURAL COMPLETADA!")
    print(" Ahora el proyecto (sólo esta carpeta copia) está listo")
    print(" para que comencemos a programar la lógica de negocio.")
    print("="*50)

if __name__ == "__main__":
    aplicar_cambios()
