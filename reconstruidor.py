import os

def extract_number_from_filename(filename):

    try:
        return int(filename.split('_')[1].split('.')[0])
    except (ValueError, IndexError):
        return float('inf')

def reconstruir_archivo_jpg(carpeta_entrada, carpeta_salida, nombre_salida):

    if not os.path.exists(carpeta_entrada):
        print(f"La carpeta '{carpeta_entrada}' no existe.")
        return
    
    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)

    archivos_dat = [archivo for archivo in os.listdir(carpeta_entrada) if archivo.endswith('.dat')]
    if not archivos_dat:
        print(f"No se encontraron archivos .dat en '{carpeta_entrada}'.")
        return

    archivos_dat.sort(key=extract_number_from_filename)

    ruta_salida = os.path.join(carpeta_salida, nombre_salida + '.mp4')

    with open(ruta_salida, 'wb') as salida:
        for archivo_dat in archivos_dat:
            ruta_completa = os.path.join(carpeta_entrada, archivo_dat)
            with open(ruta_completa, 'rb') as entrada:
                contenido = entrada.read()
                salida.write(contenido)

    print(f"Archivos .dat en '{carpeta_entrada}' reconstruidos en '{ruta_salida}'.")

carpeta_entrada = 'video.mp4_pieces'
carpeta_salida = 'archivos'
nombre_salida = 'video'

reconstruir_archivo_jpg(carpeta_entrada, carpeta_salida, nombre_salida)
