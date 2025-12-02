# Trabajo Practico Simudor S.O. con Best-Fit & SRTF
## Grupo: Cache me if you can
### Integrantes
- Alvaredo Nicolas
- Di rado Luciano
- Kowtun Andrea
- Nuñez Esteban
- Pozzer Maurizio# TP-Simulador-SO

## Objetivo
Crear una aplicación de escritorio para simular la Planificación a Corto Plazo (SRTF) y la Gestión de Memoria (Particiones Fijas con Best-Fit) de un Sistema Operativo.

## Requerimientos
> **Grado de Multiprogramación**: El sistema limitará el número de procesos activos (Listo + Listo/Suspendido + Ejecutando) a **5**.
> **Memoria**: Particiones fijas de **50K, 150K, 250K** (más 100K reservados para el SO).
> **Entrada**: Archivo CSV con columnas: `ID, Tam, TA, TI`. Máximo 10 procesos.
> **Salida**: Actualizaciones en eventos específicos (Arribo, Finalización) y visualización paso a paso.

# Ejecutar usando la consola de comandos (Desarrollo)
Requerimiento: Tenes que tener instalado el interprete de python
1. Clonar el repositorio
```bash
git clone https://github.com/EstebanFRRe/tp-simulador-SO.git
```

2. Ingresar al directorio
```bash
cd tp-simulador-SO
```

3. Ejecutar el simulador
```bash
python main.py
```

# Compilar el codigo para obtener un ejecutable
1. Clonar el repositorio
```bash
git clone https://github.com/EstebanFRRe/tp-simulador-SO.git
```

2. Ingresar al directorio
```bash
cd tp-simulador-SO
```

3. Crear un entorno vitual 
```bash
python -m venv simulador
```

4. Activar el entorno vitual 
- Linux/MacOS
```bash
source simulador/Scripts/activate
```
- Windows
```powershell
.\simulador\Scripts\activate
```
Si te da un error por permisos de ejecución de sctips ejecutá el siguiente comando para dar permisos:
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Luego ejecutá el comando de activación de nuevo

5. Instalar la libreria pyinstaller (verificar estar dentro del entorno virtual 'simulador') ejecutá
```bash
pip install pyinstaller
```
6. Compilar
```bash
pyinstaller --noconsole --onefile --name "SimuladorSO" main.py
```
Cuando termine de compilar se creará en el directorio actual, un directorio llamado dist dentro de este directorio se encontrará el archivo ejecutable con el nombre SimuladorSO

7. Ejecutar el simulador compilado
Hacé doble click sobre el archivo "SimuladorSO"

# 1. Arquitectura General: Modelo Vista Controlador MVC
Separamos el código en `main.py` para la Vista y `simulador.py` para el Controlador.
El sistema está diseñado modularmente. La clase `Simulador` encapsula toda la complejidad de las reglas de negocio (SRTF, Best-Fit, Multiprogramación), mientras que la interfaz gráfica solo se encarga de mostrar el estado actual. Esto asegura que la lógica sea robusta y verificable independientemente de la visualización.

## 2. Controlador `simulador.py` 
La parte lógica del simulador
### Clase `Proceso`
*   **Atributos**: Guardamos `tiempo_restante` separado de `tiempo_irrupcion`.
    *   **¿Por qué?**: `tiempo_irrupcion` es el dato original (para calcular estadísticas al final), pero `tiempo_restante` es el que se va consumiendo ciclo a ciclo. Necesitamos ambos.
*   **Estado**: Usamos un string ("Nuevo", "Listo", etc.).
    *   **¿Por qué?**: Simple y legible. Podríamos haber usado Enums, pero en Python un string es suficiente para este alcance y facilita la depuración (print).

### Clase `Particion`
*   **Atributo `id_proceso`**: Es `None` si está libre, o el ID si está ocupada.
    *   **¿Por qué?**: En particiones fijas, una partición solo puede tener **UN** proceso a la vez. No hace falta una lista de procesos aquí.

### Clase `Memoria`
*   **Método `best_fit(proceso)`**:
    *   **Lógica**: Recorre *todas* las particiones libres, calcula el `desperdicio` (Tamaño Partición - Tamaño Proceso) y se queda con la que tenga el **menor desperdicio positivo**.
    *   **Defensa**: "Best-Fit requiere evaluar todo el espacio disponible para encontrar el ajuste más ajustado y minimizar la fragmentación interna, a diferencia de First-Fit que agarra lo primero que ve."

### Clase `Simulador`
La vista, su método principal es `paso()`.

#### El Ciclo `paso()` (El corazón del TP)
El orden de las acciones NO es aleatorio. Sigue el ciclo de vida real de un SO:

1.  **Arribos (`Nuevos`)**: Primero vemos quién llega a la puerta.
2.  **Admisión (Long-Term Scheduler)**:
    *   Intentamos pasar de `Nuevos` a `Listos`.
    *   **Restricción**: `grado_multiprogramacion < 5`.
    *   **Decisión**: Si hay cupo (grado < 5) pero NO hay memoria RAM, el proceso entra igual pero va a **Disco (Suspendido)**. Esto es clave para mantener la multiprogramación alta sin depender solo de la RAM.
3.  **Swapping (Medium-Term Scheduler)**:
    *   Si se liberó RAM en el ciclo anterior, traemos a alguien de `Suspendidos` a `Listos`.
    *   **¿Por qué aquí?**: Antes de planificar CPU, queremos tener a todos los candidatos posibles en RAM.
4.  **Planificación (Short-Term Scheduler - SRTF)**:
    *   **Lógica**: Comparamos el `tiempo_restante` del que está ejecutando vs. el menor de la cola de listos.
    *   **Expropiación**: Si el de la cola es menor, sacamos al actual (`Ejecutando` -> `Listo`) y ponemos al nuevo.
    *   **Defensa**: "SRTF es un algoritmo expropiativo. Debo re-evaluar la decisión en cada ciclo de reloj porque puede haber llegado un proceso nuevo más corto o el actual puede haber dejado de ser el más corto."
5.  **Ejecución**:
    *   Simplemente restamos 1 al `tiempo_restante`.
6.  **Terminación**:
    *   Si `tiempo_restante == 0`, liberamos la partición y guardamos estadísticas.

---

## 3. Acerca de `main.py`

### Librería `tkinter`
*   Es la librería estándar de Python para GUIs. No requiere instalar nada extra (`pip install`), lo que garantiza que funcione en las máquinas de la facultad sin problemas de dependencias."
* **Diseño**:
    - **Superior**: Controles (Cargar CSV, Iniciar, Siguiente Paso, Auto-Ejecutar, Reiniciar).
    - **Izquierda**: Tabla de Memoria (Treeview). Columnas: ID, Inicio, Tamaño, Proceso, Frag.
    - **Centro**: Info CPU (Proceso Actual, Reloj).
    - **Derecha**: Colas (Nuevos, Listos, Listos/Suspendidos, Terminados).
    - **Inferior**: Log/Mensajes.
* **Funcionalidades**:
    - Diálogo de archivo para seleccionar CSV.
    - Indicadores visuales para estados de procesos.
    - Ventana emergente para Estadísticas Finales (Tabla + Promedios + Rendimiento).

### El Loop de Simulación (`run_auto`)
*   **Uso de `root.after(1000, self.run_auto)`**:
    *   **¿Por qué no un `while True`?**: "Si uso un `while` infinito, la interfaz gráfica se congela (no responde a clics). En cambio con `after` programamos la siguiente ejecución para dentro de 1 segundo, permitiendo que la ventana siga respondiendo entre pasos."

### Treeview (Tabla de Memoria)
*   **¿Por qué borrar y re-insertar todo (`delete`, `insert`)?**:
    *   "Para 3 particiones es instantáneo y mucho más fácil de programar que buscar y actualizar filas específicas. Mantiene la vista siempre sincronizada con el modelo."