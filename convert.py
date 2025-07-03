import os
import subprocess
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Inicializar CustomTkinter
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class VideoConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Conversor de Videos - FFMPEG")
        self.geometry("700x600")

        self.file_paths = []
        self.output_formats = ["auto", "mp4", "avi", "mkv", "mov", "flv", "wmv", "webm", "3gp", "mpg", "mpeg", "m4v", "ts"]

        # Contenedor principal
        self.container = ctk.CTkFrame(self)
        self.container.pack(padx=20, pady=20, fill="both", expand=True)

        # Widgets organizados
        self.label = ctk.CTkLabel(self.container, text="Selecciona archivos o carpetas")
        self.label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        self.select_button = ctk.CTkButton(self.container, text="Seleccionar Archivos", command=self.select_files)
        self.select_button.grid(row=1, column=0, pady=5, sticky="ew")

        self.select_folder_button = ctk.CTkButton(self.container, text="Seleccionar Carpeta", command=self.select_folder)
        self.select_folder_button.grid(row=1, column=1, pady=5, sticky="ew")

        self.output_format_label = ctk.CTkLabel(self.container, text="Formato de salida")
        self.output_format_label.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky="w")

        self.output_format_combobox = ctk.CTkComboBox(self.container, values=self.output_formats)
        self.output_format_combobox.set("auto")
        self.output_format_combobox.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")

        self.add_format_entry = ctk.CTkEntry(self.container, placeholder_text="Agregar nuevo formato")
        self.add_format_entry.grid(row=4, column=0, sticky="ew")

        self.add_format_button = ctk.CTkButton(self.container, text="Agregar Formato", command=self.add_new_format)
        self.add_format_button.grid(row=4, column=1, sticky="ew")

        self.advanced_toggle = ctk.CTkButton(self.container, text="Mostrar opciones avanzadas", command=self.toggle_advanced)
        self.advanced_toggle.grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")

        # Opciones avanzadas ocultas al inicio
        self.advanced_frame = ctk.CTkFrame(self.container)
        self.advanced_visible = False

        self.output_dir_label = ctk.CTkLabel(self.advanced_frame, text="Carpeta de salida (opcional)")
        self.output_dir_label.grid(row=0, column=0, columnspan=2, sticky="w")

        self.output_dir_entry = ctk.CTkEntry(self.advanced_frame, width=400)
        self.output_dir_entry.grid(row=1, column=0, sticky="ew")

        self.browse_output_button = ctk.CTkButton(self.advanced_frame, text="Seleccionar Carpeta", command=self.select_output_folder)
        self.browse_output_button.grid(row=1, column=1, sticky="ew")

        self.convert_button = ctk.CTkButton(self.container, text="Convertir", command=self.start_conversion_thread)
        self.convert_button.grid(row=6, column=0, columnspan=2, pady=20, sticky="ew")

        self.progress_label = ctk.CTkLabel(self.container, text="Progreso del archivo")
        self.progress_label.grid(row=7, column=0, sticky="w")
        self.file_progress = ctk.CTkProgressBar(self.container, width=500)
        self.file_progress.grid(row=8, column=0, sticky="ew")
        self.file_percent = ctk.CTkLabel(self.container, text="0%")
        self.file_percent.grid(row=8, column=1, sticky="w")

        self.total_progress_label = ctk.CTkLabel(self.container, text="Progreso total")
        self.total_progress_label.grid(row=9, column=0, sticky="w")
        self.total_progress = ctk.CTkProgressBar(self.container, width=500)
        self.total_progress.grid(row=10, column=0, sticky="ew")
        self.total_percent = ctk.CTkLabel(self.container, text="0%")
        self.total_percent.grid(row=10, column=1, sticky="w")

    def toggle_advanced(self):
        if self.advanced_visible:
            self.advanced_frame.grid_forget()
            self.advanced_toggle.configure(text="Mostrar opciones avanzadas")
        else:
            self.advanced_frame.grid(row=11, column=0, columnspan=2, pady=10, sticky="ew")
            self.advanced_toggle.configure(text="Ocultar opciones avanzadas")
        self.advanced_visible = not self.advanced_visible

    def add_new_format(self):
        new_format = self.add_format_entry.get().strip().lower()
        if new_format and new_format not in self.output_formats:
            self.output_formats.append(new_format)
            self.output_format_combobox.configure(values=self.output_formats)
            self.add_format_entry.delete(0, ctk.END)

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Video files", "*.*")])
        self.file_paths.extend(files)
        messagebox.showinfo("Archivos seleccionados", f"Se agregaron {len(files)} archivos.")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith((".mp4", ".avi", ".mov", ".mkv", ".flv")):
                        self.file_paths.append(os.path.join(root, file))
            messagebox.showinfo("Carpeta seleccionada", f"Se agregaron los archivos de {folder}.")

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_dir_entry.delete(0, ctk.END)
            self.output_dir_entry.insert(0, folder)

    def start_conversion_thread(self):
        threading.Thread(target=self.convert_videos).start()

    def get_video_duration(self, filepath):
        """Obtiene la duración del video en segundos usando ffprobe."""
        try:
            cmd = [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filepath
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            duration = float(result.stdout.strip())
            return duration
        except Exception as e:
            print(f"No se pudo obtener la duración de {filepath}: {e}")
            return None

    def parse_ffmpeg_time(self, line):
        """Extrae el valor de time=HH:MM:SS.xx de la línea de ffmpeg y lo convierte a segundos."""
        import re
        match = re.search(r'time=(\d+):(\d+):(\d+\.?\d*)', line)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
        return None

    def convert_videos(self):
        output_format = self.output_format_combobox.get().strip().lower()
        output_dir = self.output_dir_entry.get().strip()
        total_files = len(self.file_paths)

        if not self.file_paths:
            messagebox.showwarning("Advertencia", "No hay archivos seleccionados.")
            return

        # Validar que el formato de salida no sea el mismo que el de entrada
        if output_format != "auto":
            input_format = os.path.splitext(self.file_paths[0])[1][1:].lower()
            if output_format == input_format:
                messagebox.showwarning("Advertencia", "El formato de salida no puede ser el mismo que el del archivo de entrada.")
                return

        self.total_progress.set(0)
        self.file_progress.set(0)
        self.file_percent.configure(text="0%")
        self.total_percent.configure(text="0%")

        for i, path in enumerate(self.file_paths):
            base_name = os.path.splitext(os.path.basename(path))[0]
            ext = os.path.splitext(path)[1]
            out_format = output_format if output_format != "auto" else ext[1:]

            output_file = f"{base_name}_converted.{out_format}"
            output_path = os.path.join(output_dir if output_dir else os.path.dirname(path), output_file)

            # Obtener duración del video
            duration = self.get_video_duration(path)
            if not duration or duration <= 0:
                duration = None  # No se puede mostrar progreso real

            command = ["ffmpeg", "-i", path, "-preset", "fast", output_path]

            try:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
                last_percent = 0
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    if "time=" in line and duration:
                        current_time = self.parse_ffmpeg_time(line)
                        if current_time is not None:
                            percent = min(current_time / duration, 1.0)
                            self.file_progress.set(percent)
                            self.file_percent.configure(text=f"{int(percent*100)}%")
                            self.container.update_idletasks() # Forzar refresco de la UI
                            last_percent = percent
                    elif ("frame=" in line or "time=" in line) and not duration:
                        # Solo si no hay duración, mostrar actividad
                        self.file_progress.set(0.5)
                        self.file_percent.configure(text="Procesando...")
                        self.container.update_idletasks() # Forzar refresco de la UI
                process.wait()
                self.file_progress.set(1)
                self.file_percent.configure(text="100% ✅")
                self.container.update_idletasks() # Forzar refresco de la UI
            except Exception as e:
                print(f"Error al convertir {path}: {e}")

            total_progress_value = (i + 1) / total_files
            self.total_progress.set(total_progress_value)
            self.total_percent.configure(text=f"{int(total_progress_value * 100)}%")
            self.file_progress.set(0)
            self.file_percent.configure(text="0%")

        messagebox.showinfo("Conversión completa", "Los videos han sido convertidos.")
        self.file_paths = []

if __name__ == "__main__":
    app = VideoConverterApp()
    app.mainloop()
