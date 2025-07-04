import os
import subprocess
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
import re
import ctypes


# Inicializar CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class VideoConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Video Converter Pro")

        # --- Set Taskbar Icon (Windows specific) ---
        if os.name == 'nt':
            myappid = 'Infor-Mayo.VideoConverter.1.0' 
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.geometry("700x750")
        self.minsize(550, 500) # Establecer tamaño mínimo

        # Set App Icon
        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base_path, "img", "app_icon.ico")
            if os.path.exists(icon_path):
                self.wm_iconbitmap(icon_path)
                self.iconbitmap(icon_path) # Set icon for taskbar
            else:
                # This is just a fallback in case the .ico is missing
                print(f"Icon file 'app_icon.ico' not found.")
        except Exception as e:
            print(f"Error setting icon: {e}")

        self.files_info = [] # Lista de dicts: {'path': str, 'status': str}
        self.file_widgets = {} # Dict para almacenar los widgets de estado por ruta
        self.output_formats = ["auto", "mp4", "avi", "mkv", "mov", "flv", "wmv", "webm", "3gp", "mpg", "mpeg", "m4v", "ts", "personalizado"]
        self.is_compact = None
        self.file_list_visible = True
        self.config_visible = False
        self.advanced_visible = False

        # --- FUENTES ---
        self.font_title = ctk.CTkFont(family="Roboto", size=24, weight="bold")
        self.font_label = ctk.CTkFont(family="Roboto", size=14)
        self.font_button = ctk.CTkFont(family="Roboto", size=12, weight="bold")

        # --- CONTENEDOR PRINCIPAL ---
        self.container = ctk.CTkScrollableFrame(self, label_text=None)
        self.container.pack(padx=10, pady=10, fill="both", expand=True)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(2, weight=1) # Permitir que la lista de archivos se expanda

        # --- TÍTULO ---
        self.title_label = ctk.CTkLabel(self.container, text="Video Converter Pro", font=self.font_title)
        self.title_label.grid(row=0, column=0, padx=10, pady=(10, 20), sticky="ew")

        # --- CONTENEDOR DE LA LISTA DE ARCHIVOS (CON INTERRUPTOR) ---
        self.file_list_container = ctk.CTkFrame(self.container, fg_color="transparent")
        self.file_list_container.grid_columnconfigure(0, weight=1)
        self.file_list_container.grid_rowconfigure(1, weight=1)

        self.file_list_switch = ctk.CTkSwitch(self.file_list_container, text="Archivos en cola", command=self.toggle_file_list, font=self.font_label)
        self.file_list_switch.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 5))

        self.file_list_frame = ctk.CTkScrollableFrame(self.file_list_container, label_text="")
        self.file_list_frame.grid(row=1, column=0, sticky="nsew")

        # --- MARCO DE CONFIGURACIÓN DE SALIDA ---
        self.config_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.config_frame.grid_columnconfigure(0, weight=1)
        self.config_frame.grid_columnconfigure(1, weight=0)

        self.output_format_label = ctk.CTkLabel(self.config_frame, text="Formato de salida:", font=self.font_label)
        self.output_format_label.grid(row=0, column=0, padx=(0,5), pady=5, sticky="w")

        self.output_format_combobox = ctk.CTkComboBox(self.config_frame, values=self.output_formats, font=self.font_label, command=self.on_format_selected)
        self.output_format_combobox.grid(row=0, column=0, padx=(120,0), pady=5, sticky="ew")

        self.add_format_entry = ctk.CTkEntry(self.config_frame, placeholder_text="Añadir formato", font=self.font_label)
        self.add_format_entry.grid(row=1, column=0, padx=0, pady=(5,0), sticky="ew")

        self.add_format_button = ctk.CTkButton(self.config_frame, text="Añadir", command=self.add_new_format, font=self.font_button, width=60)
        self.add_format_button.grid(row=1, column=1, padx=(5,0), pady=(5,0), sticky="e")

        # Ocultar widgets de formato personalizado inicialmente
        self.add_format_entry.grid_forget()
        self.add_format_button.grid_forget()

        # --- OPCIONES AVANZADAS ---
        self.advanced_toggle = ctk.CTkCheckBox(self.container, text="Opciones avanzadas", command=self.toggle_advanced, font=self.font_label)
        self.advanced_frame = ctk.CTkFrame(self.container)
        self.advanced_frame.grid_columnconfigure(1, weight=1)

        self.output_dir_label = ctk.CTkLabel(self.advanced_frame, text="Carpeta de salida:", font=self.font_label)
        self.output_dir_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.output_dir_entry = ctk.CTkEntry(self.advanced_frame, font=self.font_label)
        self.output_dir_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.browse_output_button = ctk.CTkButton(self.advanced_frame, text="...", command=self.select_output_folder, width=30)
        self.browse_output_button.grid(row=0, column=2, padx=5, pady=5)

        # --- BOTÓN DE CONVERSIÓN ---
        self.convert_button = ctk.CTkButton(self.container, text="Convertir Videos", command=self.start_conversion_thread, font=self.font_button, height=40)

        # --- BARRAS DE PROGRESO ---
        self.progress_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.progress_frame.grid_columnconfigure(0, weight=1)
        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Archivo actual:", font=self.font_label)
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.percent_label = ctk.CTkLabel(self.progress_frame, text="0%", font=self.font_label)
        self.total_progress_label = ctk.CTkLabel(self.progress_frame, text="Progreso total:", font=self.font_label)
        self.total_progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.total_percent = ctk.CTkLabel(self.progress_frame, text="0%", font=self.font_label)

        # --- ESTADO INICIAL Y RESPONSIVIDAD ---
        self.update_file_list_ui() # Mostrar la lista vacía al inicio

        # --- Botón Flotante de Acción (FAB) ---
        # Clic izquierdo para archivos, clic derecho para carpetas
        self.fab_button = ctk.CTkButton(self, text="+", width=50, height=50, corner_radius=25, font=ctk.CTkFont(size=24, weight="bold"), fg_color="#2FA572", hover_color="#237A54", text_color="#FFFFFF")
        self.fab_button.place(relx=1.0, rely=1.0, x=-20, y=-20, anchor="se")
        self.fab_button.bind("<Button-1>", lambda e: self.select_files())
        self.fab_button.bind("<Button-3>", lambda e: self.select_folder())

        # Bind resize event
        self.bind("<Configure>", self.on_resize)
        self.on_resize() # Llamada inicial para establecer el layout correcto

    def toggle_file_list(self):
        self.file_list_visible = self.file_list_switch.get()
        if self.file_list_visible:
            self.file_list_frame.grid(row=1, column=0, sticky="nsew")
        else:
            self.file_list_frame.grid_forget()

    def toggle_advanced(self):
        self.advanced_visible = not self.advanced_visible
        if self.advanced_visible:
            self.advanced_frame.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
        else:
            self.advanced_frame.grid_forget()

    def add_new_format(self):
        new_format = self.add_format_entry.get().strip().lower()
        if new_format and new_format not in self.output_formats:
            self.output_formats.append(new_format)
            self.output_format_combobox.configure(values=self.output_formats)
            self.add_format_entry.delete(0, ctk.END)

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_dir_entry.delete(0, ctk.END)
            self.output_dir_entry.insert(0, folder)

    def get_status_icon(self, status):
        icons = {
            "queue": "⏳",
            "processing": "⚙️",
            "done": "✅",
            "error": "❌"
        }
        return icons.get(status, "")

    def update_file_status(self, file_path, new_status):
        for info in self.files_info:
            if info['path'] == file_path:
                info['status'] = new_status
                break
        if file_path in self.file_widgets:
            self.file_widgets[file_path].configure(text=self.get_status_icon(new_status))
            self.update_idletasks()

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Video files", "*.*")])
        if not files: return
        for f in files:
            self.files_info.append({'path': f, 'status': 'queue'})
        self.update_file_list_ui()
        self.show_config_if_needed()

    def select_folder(self):
        folder = filedialog.askdirectory()
        if not folder: return
        added_files = []
        for root, _, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv')):
                    added_files.append(os.path.join(root, file))
        if added_files:
            for f in added_files:
                self.files_info.append({'path': f, 'status': 'queue'})
            self.update_file_list_ui()
            self.show_config_if_needed()

    def update_file_list_ui(self):
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()
        self.file_widgets = {}

        if not self.files_info:
            label = ctk.CTkLabel(self.file_list_frame, text="No hay archivos seleccionados", font=self.font_label, text_color="gray")
            label.pack(pady=10)
        else:
            for info in self.files_info:
                file_path = info['path']
                item_frame = ctk.CTkFrame(self.file_list_frame, fg_color="transparent")
                item_frame.pack(fill="x", padx=5, pady=2)

                status_label = ctk.CTkLabel(item_frame, text=self.get_status_icon(info['status']), font=self.font_label, width=25)
                status_label.pack(side="left", padx=(0, 5))

                filename_label = ctk.CTkLabel(item_frame, text=os.path.basename(file_path), font=self.font_label, anchor="w")
                filename_label.pack(side="left", fill="x", expand=True)

                self.file_widgets[file_path] = status_label

    def show_config_if_needed(self):
        if self.files_info and not self.config_visible:
            self.file_list_container.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
            self.config_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
            self.advanced_toggle.grid(row=4, column=0, padx=10, pady=(10,0), sticky="w")
            self.convert_button.grid(row=6, column=0, padx=10, pady=20, sticky="ew")
            self.config_visible = True

    def set_controls_state(self, state):
        for control in [self.fab_button, self.output_format_combobox, self.add_format_entry, self.add_format_button, self.advanced_toggle, self.convert_button]:
            control.configure(state=state)
        if self.advanced_visible:
            self.browse_output_button.configure(state=state)
            self.output_dir_entry.configure(state=state)



    def on_format_selected(self, selected_format):
        if selected_format == "personalizado":
            self.add_format_entry.grid(row=1, column=0, padx=0, pady=(5,0), sticky="ew")
            self.add_format_button.grid(row=1, column=1, padx=(5,0), pady=(5,0), sticky="e")
        else:
            self.add_format_entry.grid_forget()
            self.add_format_button.grid_forget()

    def on_resize(self, event=None):
        width = self.winfo_width()
        if width < 100: return
        is_compact_now = width < 600
        if self.is_compact == is_compact_now: return
        self.is_compact = is_compact_now
        
        # La lógica de redimensionamiento para el marco de formato personalizado ya no es necesaria aquí.

    def reset_ui_to_initial_state(self):
        self.files_info = []
        self.file_widgets = {}
        self.update_file_list_ui()

        self.file_list_container.grid_forget()
        self.config_frame.grid_forget()
        self.advanced_toggle.grid_forget()
        if self.advanced_visible:
            self.advanced_frame.grid_forget()
            self.advanced_visible = False
            self.advanced_toggle.deselect()

        self.convert_button.grid_forget()
        self.config_visible = False
        self.add_format_entry.grid_forget()
        self.add_format_button.grid_forget()
        self.output_format_combobox.set("auto")

        self.progress_frame.grid_forget()
        
        self.file_list_visible = True
        self.file_list_switch.select()
        self.toggle_file_list()
        
        self.set_controls_state("normal")

    def start_conversion_thread(self):
        thread = threading.Thread(target=self.convert_videos)
        thread.daemon = True
        thread.start()

    def convert_videos(self):
        if not self.files_info:
            messagebox.showwarning("Sin archivos", "Por favor, selecciona al menos un archivo.")
            return

        self.set_controls_state("disabled")
        self.progress_frame.grid(row=7, column=0, padx=10, pady=10, sticky="ew")
        self.progress_label.grid(row=0, column=0, sticky="w")
        self.progress_bar.grid(row=1, column=0, sticky="ew")
        self.percent_label.grid(row=1, column=1, padx=5)
        self.total_progress_label.grid(row=2, column=0, sticky="w")
        self.total_progress_bar.grid(row=3, column=0, sticky="ew")
        self.total_percent.grid(row=3, column=1, padx=5)

        try:
            output_format = self.output_format_combobox.get().strip().lower()
            output_dir = self.output_dir_entry.get().strip()
            total_files = len(self.files_info)
            self.total_progress_bar.set(0)

            for i, info in enumerate(self.files_info):
                file_path = info['path']
                self.update_file_status(file_path, "processing")

                self.progress_bar.set(0)
                self.percent_label.configure(text="0%")
                self.progress_label.configure(text=f"Archivo: {os.path.basename(file_path)}")
                self.update_idletasks()

                out_ext = f".{output_format}" if output_format != "auto" else os.path.splitext(file_path)[1] or ".mp4"
                output_file = os.path.join(output_dir or os.path.dirname(file_path), os.path.splitext(os.path.basename(file_path))[0] + out_ext)

                try:
                    startupinfo = subprocess.STARTUPINFO() if os.name == 'nt' else None
                    if os.name == 'nt':
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                    duration_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
                    duration_process = subprocess.run(duration_cmd, capture_output=True, text=True, startupinfo=startupinfo)
                    if duration_process.returncode != 0:
                        raise Exception(f"FFprobe error: {duration_process.stderr}")
                    duration = float(duration_process.stdout.strip())

                    command = ['ffmpeg', '-i', file_path, '-y', output_file]
                    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8', startupinfo=startupinfo)

                    for line in process.stdout:
                        match = re.search(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})", line)
                        if match:
                            h, m, s, ms = map(int, match.groups())
                            progress = ((h * 3600 + m * 60 + s + ms / 100) / duration)
                            self.progress_bar.set(progress)
                            self.percent_label.configure(text=f"{int(progress*100)}%")

                            # Actualizar progreso total en tiempo real
                            total_progress = (i + progress) / total_files
                            self.total_progress_bar.set(total_progress)
                            self.total_percent.configure(text=f"{int(total_progress * 100)}%")
                            
                            self.update_idletasks()
                    process.wait()
                    if process.returncode != 0:
                        raise Exception(f"FFmpeg exited with code {process.returncode}")
                    
                    self.update_file_status(file_path, "done")

                except Exception as e:
                    self.update_file_status(file_path, "error")
                    messagebox.showerror("Error de conversión", f"No se pudo convertir {os.path.basename(file_path)}\nError: {e}")
                    return

                total_progress = (i + 1) / total_files
                self.total_progress_bar.set(total_progress)
                self.total_percent.configure(text=f"{int(total_progress * 100)}%")
                self.update_idletasks()

            messagebox.showinfo("Conversión completada", "Todos los videos han sido convertidos exitosamente.")

        finally:
            self.reset_ui_to_initial_state()

if __name__ == "__main__":
    app = VideoConverterApp()
    app.mainloop()
