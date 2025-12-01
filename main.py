import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import simulador

class AplicacionPrincipal:
    def __init__(self, raiz):
        self.raiz = raiz
        # titulo principal
        self.raiz.title("Simulador SO: Grupo Cache me if you can - Particiones Fijas Best Fit & SRTF")
        self.raiz.geometry("1200x700")
        
        # instanciamos el simulardor
        self.simulador = simulador.Simulador()
        self.ejecucion_automatica = False
        self.retraso = 1000 # ms que es1 segundo entre pasos
        
        # metodo para la construcción de la ventana principal
        self._configurar_interfaz()
        
    def _configurar_interfaz(self):
        # marco Superior, aca van los bbotones nomas 
        marco_controles = ttk.LabelFrame(self.raiz, text="Controles", padding=10)
        marco_controles.pack(fill="x", padx=10, pady=5)
        #el boton para cargar el arch
        ttk.Button(marco_controles, text="Cargar CSV", command=self.cargar_csv).pack(side="left", padx=5)
        self.lbl_archivo = ttk.Label(marco_controles, text="Ningún archivo cargado")
        self.lbl_archivo.pack(side="left", padx=5)
        
        ttk.Separator(marco_controles, orient="vertical").pack(side="left", fill="y", padx=10)
        #boton para avanzar el ciclo de reloh
        self.btn_siguiente = ttk.Button(marco_controles, text="Siguiente Paso (Reloj)", command=self.siguiente_paso, state="disabled")
        self.btn_siguiente.pack(side="left", padx=5)
        
        self.btn_automatico = ttk.Button(marco_controles, text="Auto-Ejecutar", command=self.alternar_automatico, state="disabled")
        self.btn_automatico.pack(side="left", padx=5)
        
        ttk.Button(marco_controles, text="Reiniciar", command=self.reiniciar).pack(side="left", padx=5)
        
        # ccontenido Principal, aca van los cuadros que muestra la memoria, cpu y las colas
        marco_contenido = ttk.Frame(self.raiz)
        marco_contenido.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Parte de la Izquierda acá ponemos la memoriaa
        # Usamos una tabla con Treeview porque es la forma más clara de ver las particiones
        marco_memoria = ttk.LabelFrame(marco_contenido, text="Memoria Principal (Particiones Fijas)", padding=5)
        marco_memoria.pack(side="left", fill="both", expand=True, padx=5)
        
        columnas = ("ID Part", "Inicio", "Tamaño", "Proceso", "Frag. Interna")
        self.tabla_memoria = ttk.Treeview(marco_memoria, columns=columnas, show="headings", height=10)
        for col in columnas:
            self.tabla_memoria.heading(col, text=col)
            self.tabla_memoria.column(col, width=80, anchor="center")
        self.tabla_memoria.pack(fill="both", expand=True)
        
        #en ek centro va la CPU e Info
        marco_central = ttk.Frame(marco_contenido)
        marco_central.pack(side="left", fill="both", expand=True, padx=5)
        
        # caja que contiene roda la info de la cpu
        marco_cpu = ttk.LabelFrame(marco_central, text="CPU - Ejecución", padding=10)
        marco_cpu.pack(fill="x", pady=5)
        
        self.lbl_reloj = ttk.Label(marco_cpu, text="Reloj: 0", font=("Arial", 14, "bold"))
        self.lbl_reloj.pack()

        self.lbl_multiprog = ttk.Label(marco_cpu, text="Grado Multiprog: 0/5", font=("Arial", 10))
        self.lbl_multiprog.pack()
        
        self.lbl_proc_cpu = ttk.Label(marco_cpu, text="Proceso: Ninguno", font=("Arial", 12), foreground="blue")
        self.lbl_proc_cpu.pack(pady=5)
        
        # Log de Eventos esta debajo del cpu
        # usamos un cuadro de texto para mostrar los cambios cuando pasa algo nomás
        marco_log = ttk.LabelFrame(marco_central, text="Log de Eventos", padding=5)
        marco_log.pack(fill="both", expand=True, pady=5)
        
        self.txt_log = tk.Text(marco_log, height=10, width=40, state="disabled", font=("Consolas", 9))
        self.txt_log.pack(fill="both", expand=True)
        
        # a la derecha ponemos los cuadritos para mostrar el cont de las colas
        # mostramos todas las listas de procesos para ver dónde está cada proceso
        marco_colas = ttk.Frame(marco_contenido)
        marco_colas.pack(side="right", fill="both", expand=True, padx=5)
        
        self.lst_nuevos = self._crear_cuadro_cola(marco_colas, "Cola de Nuevos")
        self.lst_listos = self._crear_cuadro_cola(marco_colas, "Cola de Listos (Memoria)")
        self.lst_suspendidos = self._crear_cuadro_cola(marco_colas, "Cola de Listos/Suspendidos (Disco)")
        self.lst_terminados = self._crear_cuadro_cola(marco_colas, "Cola de Terminados")
        self.lst_espera = self._crear_cuadro_cola(marco_colas, "Tiempos de Espera (en  Listos)")

    def _crear_cuadro_cola(self, padre, titulo):
        # definimos eeste mtodo para no repetir código al crear las cajitas de las colas
        marco = ttk.LabelFrame(padre, text=titulo, padding=5)
        marco.pack(fill="both", expand=True, pady=2)
        lista = tk.Listbox(marco, height=5)
        lista.pack(fill="both", expand=True)
        return lista

    def cargar_csv(self):
        # el metodo para cargar el archivo
        ruta_archivo = filedialog.askopenfilename(filetypes=[("Archivos CSV", "*.csv")])
        if not ruta_archivo:
            return
            
        self.reiniciar() # limpiamos toda la interfaz antes de cargar
 
        if self.simulador.cargar_procesos(ruta_archivo):
            self.lbl_archivo.config(text=ruta_archivo.split("/")[-1])
            self.btn_siguiente.config(state="normal")
            self.btn_automatico.config(state="normal")
            self.actualizar_interfaz()
            #self.registrar_mensaje(f"Archivo cargado: {ruta_archivo}")
            #muestra la ruta desde la que se cargó nomás, ver si queda
        else:
            messagebox.showerror("Error", "No se pudo cargar el archivo.")

    def siguiente_paso(self):
        # preguntamos s ya terminó y mostramos el resumen final
        if self.simulador.simulacion_terminada():
            self.finalizar_simulacion()
            return

        # le decimos al simulador que avance 1 ciclo de reloj
        self.simulador.paso()
        # y después actualizamos toda la pantalla para que myuestre los cambios
        self.actualizar_interfaz()
        
        # preguntamos de nuevo por si justo terminó en este paso
        if self.simulador.simulacion_terminada():
            self.finalizar_simulacion()

    def alternar_automatico(self):
        # botón para pausar o arrancar el modo automático
        if self.ejecucion_automatica:
            self.ejecucion_automatica = False
            self.btn_automatico.config(text="Auto-Ejecutar")
            self.btn_siguiente.config(state="normal")
        else:
            self.ejecucion_automatica = True
            self.btn_automatico.config(text="Pausar")
            self.btn_siguiente.config(state="disabled")
            self.ejecutar_automatico()

    def ejecutar_automatico(self):
        # acá en lugar de un bucle while, usamos el metodo de pyrhon after
        # para que el simulador haga un paso y la ventana espera los 1000ms que de definimos, 
        # sino hacemos estp intenta actualizar todo junto y se congela la ventana lo alcanza a renderizar los cambios
        if self.ejecucion_automatica and not self.simulador.simulacion_terminada():
            self.siguiente_paso()
            self.raiz.after(self.retraso, self.ejecutar_automatico)

    def reiniciar(self):
        # con este boton para reiniciar todo el simulador, hay que cargar el archivo de nuevo
        self.ejecucion_automatica = False
        self.simulador = simulador.Simulador()
        self.lbl_archivo.config(text="Ningún archivo cargado")
        self.btn_siguiente.config(state="disabled")
        self.btn_automatico.config(state="disabled", text="Auto-Ejecutar")
        self.txt_log.config(state="normal")
        self.txt_log.delete(1.0, tk.END)
        self.txt_log.config(state="disabled")
        self.actualizar_interfaz()

    def actualizar_interfaz(self):
        # Este metodo toma el estado del simulador y lo renderiza en la ventana
        
        #primero actualizamos el reloj
        self.lbl_reloj.config(text=f"Reloj: {self.simulador.reloj}")
        
        # y actualizamos el grado de multiprogramación
        grado = self.simulador.grado_multiprogramacion()
        self.lbl_multiprog.config(text=f"Grado Multiprog: {grado}/5")
        
        #para mostrar la mem, borramos todo y la creamos de nuevo
        #porque no sé como buscar lina por linea
        for item in self.tabla_memoria.get_children():
            self.tabla_memoria.delete(item)
            
        for p in self.simulador.memoria.particiones:
            txt_proc = f"P{p.id_proceso}" if p.id_proceso is not None else "Libre"
            txt_frag = f"{p.fragmentacion} KB" if p.id_proceso is not None else "-"
            self.tabla_memoria.insert("", "end", values=(p.id, p.dir_inicio, f"{p.tamano} KB", txt_proc, txt_frag))
            
        #mostramos quien esta usando la Cpu
        if self.simulador.proceso_ejecutando:
            p = self.simulador.proceso_ejecutando
            texto_estado = f"Proceso: {p.id}"
            if p.estado == "Terminado":
                texto_estado += " (Terminando...)"
                self.lbl_proc_cpu.config(foreground="red")
            else:
                texto_estado += f" (Restante: {p.tiempo_restante})"
                self.lbl_proc_cpu.config(foreground="blue")
            
            self.lbl_proc_cpu.config(text=texto_estado)
        else:
            self.lbl_proc_cpu.config(text="Proceso: Ninguno", foreground="black")
        
        #renderizamos los cuadritos en donde estan las colas
        self._actualizar_lista(self.lst_nuevos, self.simulador.cola_nuevos)
        self._actualizar_lista(self.lst_listos, self.simulador.cola_listos)
        self._actualizar_lista(self.lst_suspendidos, self.simulador.cola_suspendidos)
        self._actualizar_lista(self.lst_terminados, self.simulador.cola_terminados)
        
        #solo para debug sacar despues, 
        # este está para controlar el TE, el tiempo que está en Listo de cada proceso
        self.lst_espera.delete(0, tk.END)
        for p in self.simulador.procesos:
            if p.estado not in ["Nuevo"]:
                self.lst_espera.insert(tk.END, f"P{p.id}: {p.tiempo_espera}s")
        
        # mostramos lo que paso en este ciclo de reloj todo el log del simulador al cuadro de texto
        self.txt_log.config(state="normal")
        self.txt_log.delete(1.0, tk.END)
        for linea in self.simulador.log:
            self.txt_log.insert(tk.END, linea + "\n")
        self.txt_log.see(tk.END) # Hacemos scroll hasta el final
        self.txt_log.config(state="disabled")

    def _actualizar_lista(self, lista, cola):
        # usamos esto para limpiar y llenar una lista
        lista.delete(0, tk.END)
        for p in cola:
            lista.insert(tk.END, f"ID:{p.id} | Tam:{p.tamano} | TR:{p.tiempo_restante}")

    def registrar_mensaje(self, msg):
        self.txt_log.config(state="normal")
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state="disabled")

    def finalizar_simulacion(self):
        self.ejecucion_automatica = False
        self.btn_automatico.config(text="Auto-Ejecutar")
        self.btn_siguiente.config(state="disabled")
        
        # llamamos al metodo para las estadísticas finales al simulador
        stats = self.simulador.obtener_estadisticas()
        if stats:
            # Creamos una ventana nueva  con eñ Toplevel para mostrar los resultados
            ventana_top = tk.Toplevel(self.raiz)
            ventana_top.title("Resultados Finales")
            ventana_top.geometry("600x400")
            
            lbl_titulo = ttk.Label(ventana_top, text="Estadísticas por Proceso", font=("Arial", 12, "bold"))
            lbl_titulo.pack(pady=10)
            
            # mostramos la tabla de resultados
            columnas = ("Proceso", "T. Arribo (Sist)", "T. Ingreso (Listos)", "T. Irrupción", "T. Retorno", "T. Espera")
            arbol = ttk.Treeview(ventana_top, columns=columnas, show="headings", height=10)
            for col in columnas:
                arbol.heading(col, text=col)
                arbol.column(col, width=90, anchor="center")
            arbol.pack(fill="both", expand=True, padx=10)
            
            for p in stats['procesos']:
                t_ingreso = p.tiempo_ingreso_memoria if p.tiempo_ingreso_memoria is not None else "-"
                arbol.insert("", "end", values=(p.id, p.tiempo_arribo, t_ingreso, p.tiempo_irrupcion, p.tiempo_retorno, p.tiempo_espera))
            
            # mostramos los promedios abajo de la tabla
            marco_prom = ttk.Frame(ventana_top, padding=10)
            marco_prom.pack(fill="x")
            
            ttk.Label(marco_prom, text=f"Promedio Retorno: {stats['prom_retorno']:.2f}").pack(anchor="w")
            ttk.Label(marco_prom, text=f"Promedio Espera: {stats['prom_espera']:.2f}").pack(anchor="w")
            ttk.Label(marco_prom, text=f"Rendimiento: {stats['rendimiento']:.4f} trabajos/t").pack(anchor="w")
            
            ttk.Button(ventana_top, text="Cerrar", command=ventana_top.destroy).pack(pady=10)

if __name__ == "__main__":
    raiz = tk.Tk()
    app = AplicacionPrincipal(raiz)
    raiz.mainloop()
