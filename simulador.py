import csv

class Proceso:
    def __init__(self, id_proc, tamano, tiempo_arribo, tiempo_irrupcion):
        # guardamos la info básica del proceso
        self.id = id_proc
        self.tamano = tamano
        self.tiempo_arribo = tiempo_arribo
        self.tiempo_irrupcion = tiempo_irrupcion
        
        # vamos a sar tiempo_restante para ir descontando lo que falta.
        # no tocamos tiempo_irrupcion nporque lo vamos a usar  para las estadísticas.
        self.tiempo_restante = tiempo_irrupcion
        self.estado = "Nuevo"
        self.id_particion = None
        
        # variables para las estadísticas  
        self.tiempo_finalizacion = 0
        self.tiempo_espera = 0
        self.tiempo_retorno = 0
        self.tiempo_ingreso_memoria = None # guardamos el momento en que entra a la cola de Listos 

    def __repr__(self):
        return f"P{self.id}({self.estado}, TR:{self.tiempo_restante})"

class Particion:
    def __init__(self, id_part, tamano, dir_inicio):
        self.id = id_part
        self.tamano = tamano
        self.dir_inicio = dir_inicio
        self.id_proceso = None # guardamos el ID del proceso que la ocupa, es none si está libre
        self.fragmentacion = 0 

    def esta_libre(self):
        return self.id_proceso is None

    def asignar(self, proceso):
        self.id_proceso = proceso.id
        # calculams de la frang interna
        self.fragmentacion = self.tamano - proceso.tamano
        proceso.id_particion = self.id

    def liberar(self):
        self.id_proceso = None
        self.fragmentacion = 0

class Memoria:
    def __init__(self):
        # definimos las particiones fijas 
        self.particiones = [
            Particion(1, 100, 0), # partición para el SO
            Particion(2, 50, 100),
            Particion(3, 150, 150),
            Particion(4, 250, 300)
        ]
        # Dejamos fija la partición 1 para el SO
        self.particiones[0].id_proceso = "SO"

    def best_fit(self, proceso):

        candidata = None
        min_desperdicio = float('inf')

        for part in self.particiones:
            # Solo miramos las libres y donde el proceso entre
            if part.esta_libre() and part.tamano >= proceso.tamano:
                desperdicio = part.tamano - proceso.tamano
                # Si esta partición desperdicia menos que la mejor que teníamos hasta ahora la guardamos
                if desperdicio < min_desperdicio:
                    min_desperdicio = desperdicio
                    candidata = part
        
        # si encontramos una candidata ideal, la asignamos
        if candidata:
            candidata.asignar(proceso)
            return True
        return False

    def liberar_particion(self, id_particion):
        # Buscamos la partición por el ID y la liberamos
        for part in self.particiones:
            if part.id == id_particion:
                part.liberar()
                return

class Simulador:
    def __init__(self):
        self.reloj = 0
        self.procesos = []
        self.memoria = Memoria()
        
        # definimos las colas que vamos a usar
        self.cola_nuevos = []
        self.cola_listos = []
        self.cola_suspendidos = [] # Listo/Suspendido 
        self.cola_terminados = []
        
        self.proceso_ejecutando = None
        self.log = [] # para ir mostrando cuando se hacen cambios

    def cargar_procesos(self, ruta_archivo):
        try:
            nuevos_procesos = []
            with open(ruta_archivo, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 4:
                        # Leemos el CSV con el formato: ID, T_Arribo, Tamaño, T_Irrupción
                        try:
                            pid = row[0] 
                            ta = int(row[1])
                            tam = int(row[2])
                            ti = int(row[3])
                            nuevos_procesos.append(Proceso(pid, tam, ta, ti))
                        except ValueError:
                            continue
            
            # verificamos que no sean más de 10 procesos los que vienen en el arch de entrada
            if len(nuevos_procesos) > 10:
                self.log.append(f"AVISO: Se excedió el límite de 10 procesos. Se descartaron {len(nuevos_procesos) - 10} procesos.")
                self.procesos = nuevos_procesos[:10]
            else:
                self.log.append("Carga exitosa: No se eliminó ningún proceso.")
                self.procesos = nuevos_procesos

            # aca le ordenamos por llegada para que sea más fácil simular
            self.procesos.sort(key=lambda p: p.tiempo_arribo)
            
            self.log.append(f"Cargados {len(self.procesos)} procesos en total.")
            return True
        except Exception as e:
            self.log.append(f"Error al cargar archivo: {e}")
            return False

    def grado_multiprogramacion(self):
        # calculamos cuántos procesos hay activos en el sistema Listo, Listo/susp y ejecuc
        count = len(self.cola_listos) + len(self.cola_suspendidos)
        if self.proceso_ejecutando:
            count += 1
        return count

    def paso(self):
        # Esta función es el manejador principal del simulador aca ejecutamos un ciclo de reloj
        
        # verificamos que procesos llegan en el instante actual de reloj
        llegadas = [p for p in self.procesos if p.tiempo_arribo == self.reloj and p.estado == "Nuevo"]
        for p in llegadas:
            # pregintamos por el tamaño del proceso si es mayor que 250k no lo admitimos en el sistema
            if p.tamano > 250:
                self.log.append(f"AVISO: Proceso {p.id} eliminado por exceder tamaño máximo 250k")
                self.procesos.remove(p) 
            else:
                self.cola_nuevos.append(p)
                self.log.append(f"Proceso {p.id} arribó.")

        # para pasar dee Nuevos a Listos o listo/suspendidos
        # Solo dejamos entrar si no superamos el grado de multiprogramación de 5
        while self.cola_nuevos and self.grado_multiprogramacion() < 5:
            proc = self.cola_nuevos.pop(0)
            
            # Intentamos meterlo en memria con Best-Fit
            if self.memoria.best_fit(proc):
                proc.estado = "Listo"
                proc.tiempo_ingreso_memoria = self.reloj # guardamos el tiempo en que ingresa, para calcular la estadistica
                #  despues con este valor, por que el tiempo de arribo que usamos es el tiempo cuando ingresa a la Listos
                self.cola_listos.append(proc)
                self.log.append(f"Proceso {proc.id} admitido a Listo (Memoria).")
            else:
                # sino entra, va a listo/Suspendido
                proc.estado = "ListoSuspendido"
                self.cola_suspendidos.append(proc)
                self.log.append(f"Proceso {proc.id} admitido a ListoSuspendido (Disco).")

        # hacemos el swap-in De Suspendidos a Listos
        # ordenamos los suspendidos por el que tenga menor  TI
        self.cola_suspendidos.sort(key=lambda p: p.tiempo_irrupcion)
        
        # intentamos traerlos a memoria si se liberó espacio
        for proc in list(self.cola_suspendidos):
            if self.memoria.best_fit(proc):
                self.cola_suspendidos.remove(proc)
                proc.estado = "Listo"
                proc.tiempo_ingreso_memoria = self.reloj
                self.cola_listos.append(proc)
                self.log.append(f"Proceso {proc.id} recuperado de Disco a Memoria.")

        # planificador de cpu
        # Ccomparamos al que está ejecutando con los que están esperando
        candidato = self.proceso_ejecutando
        # candidato llamaos al que se está ejecutamdo porque es el candidato a salir de la CCPU
        # Si el que estaba ejecutando terminó o no había nadie lo dejamos none para despues preguntar por el
        if candidato is None or candidato.estado == "Terminado":
            candidato = None

        # Buscamos al proceso con menor tiempo de irrupcion restante en la cola de listos
        mejor_listo = None
        if self.cola_listos:
            mejor_listo = min(self.cola_listos, key=lambda p: p.tiempo_restante)
        
        # nuevo_ejecutando es el que se va a ejecutar
        nuevo_ejecutando = candidato
        
        if candidato is None:
            # Si no hay nadie en la CCPU, el mejor_listo es el nuevo ejecutando
            if mejor_listo:
                nuevo_ejecutando = mejor_listo
        else:
            # aca hacemoos la expropiacion Si el de la cola es más corto que el actual, lo sacamos
            if mejor_listo and mejor_listo.tiempo_restante < candidato.tiempo_restante:
                nuevo_ejecutando = mejor_listo
                self.log.append(f"Proceso {candidato.id} expropiado por {mejor_listo.id}.")
        
        # le hacemos el cambio de contexto si cambió el proceso
        if nuevo_ejecutando != self.proceso_ejecutando:
            if self.proceso_ejecutando and self.proceso_ejecutando.estado == "Ejecutando":
                self.proceso_ejecutando.estado = "Listo"
                self.cola_listos.append(self.proceso_ejecutando)
            
            # le cambiamos el proceso a la CPU
            self.proceso_ejecutando = nuevo_ejecutando
            if self.proceso_ejecutando in self.cola_listos:
                self.cola_listos.remove(self.proceso_ejecutando)
            self.proceso_ejecutando.estado = "Ejecutando"
            self.log.append(f"Proceso {self.proceso_ejecutando.id} comienza ejecución.")

       # esta es la parte de la ejecucion
        if self.proceso_ejecutando:
            self.proceso_ejecutando.tiempo_restante -= 1
            
            # preguntamossi un proceso termina
            if self.proceso_ejecutando.tiempo_restante == 0:
                proc = self.proceso_ejecutando
                proc.estado = "Terminado"
                proc.tiempo_finalizacion = self.reloj + 1 # termina justo al final de este ciclo
                
                # Calculamos estadísticas 
                # TR = Tiempo de Retorno, desde que entró a memoria hasta que terminó
                # TE = Tiempo de Espera, lo que acumulamos
                proc.tiempo_retorno = proc.tiempo_espera + proc.tiempo_irrupcion
                
                self.memoria.liberar_particion(proc.id_particion)
                self.cola_terminados.append(proc)
                self.log.append(f"Proceso {proc.id} terminó.")
        # actualizamos el Tiempo de Espera para todos los que están esperando en Listos
        for p in self.cola_listos:
            p.tiempo_espera += 1

        self.reloj += 1
        return True

    def simulacion_terminada(self):
        # verificamps si ya tratamos todos los procesos
        total_procesos = len(self.procesos)
        return len(self.cola_terminados) == total_procesos and total_procesos > 0

    def obtener_estadisticas(self):
        if not self.cola_terminados:
            return None
            
        prom_retorno = sum(p.tiempo_retorno for p in self.cola_terminados) / len(self.cola_terminados)
        prom_espera = sum(p.tiempo_espera for p in self.cola_terminados) / len(self.cola_terminados)
        rendimiento = len(self.cola_terminados) / self.reloj if self.reloj > 0 else 0
        
        return {
            "prom_retorno": prom_retorno,
            "prom_espera": prom_espera,
            "rendimiento": rendimiento,
            "procesos": sorted(self.cola_terminados, key=lambda p: p.id)
        }
