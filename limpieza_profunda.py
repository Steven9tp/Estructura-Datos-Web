import os
import shutil

print("="*50)
print(" LIMPIEZA PROFUNDA DE U-RIDE (Módulos no relacionados)")
print("="*50)

carpetas_a_borrar = [
    "app/api",
    "app/admin",
    "app/seguridad",
    "frontend/templates/seguridad",
    "frontend/templates/viajes",
    "frontend/templates/admin"
]

for carpeta in carpetas_a_borrar:
    if os.path.exists(carpeta):
        try:
            shutil.rmtree(carpeta)
            print(f" [ELIMINADO] {carpeta}")
        except Exception as e:
            print(f" [ERROR] No se pudo eliminar {carpeta}: {e}")
    else:
        print(f" [OMITIDO] {carpeta} ya no existe.")

print("\n¡Limpieza completada! El proyecto ahora solo tiene código de SmartCampus.")
