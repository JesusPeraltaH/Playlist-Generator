# En gui.py
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import tkinter as tk
import threading
import webbrowser
import spotipy
from PIL import Image, ImageTk
import requests
from io import BytesIO
from spotipy.oauth2 import SpotifyOAuth
from spotify_api import connect_to_spotify, get_suggestions_from_api, create_spotify_playlist as create_spotify_playlist_api, reconnect_spotify_api, search_spotify_artist, get_playlist_tracks_from_api



class SpotifyPlaylistCreator:
    """A GUI application for creating Spotify playlists based on artist suggestions."""
    def __init__(self, root):
        self.root = root
        self.root.title("Spotify Playlist Creator")
        self.sp = None
        self.artist_list_names = []  # To store artist names
        self.track_suggestions = [] # To store the full track suggestion data
        self.confirmed_tracks = [] # List to store confirmed tracks with metadata
        self.client_id = None
        self.client_secret = None
        self.redirect_uri = 'http://localhost:8888/callback' # Default redirect URI
        self.image_cache = {}
        self.setup_credentials()
        self.setup_ui()
        self.setup_environment()
        self.image_cache = {}

    def setup_credentials(self):
        # Load credentials (you might want to handle this more securely)
        import os
        from dotenv import load_dotenv, find_dotenv
        load_dotenv(find_dotenv())
        self.client_id = os.getenv('SPOTIPY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')

    def setup_ui(self):
        # Artist input
        self.artist_frame = ttk.Frame(self.root)
        self.artist_frame.pack(padx=10, pady=5, fill=tk.X)
        ttk.Label(self.artist_frame, text="Artist:").pack(side=tk.LEFT)
        self.artist_entry = ttk.Entry(self.artist_frame)
        self.artist_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.add_button = ttk.Button(self.artist_frame, text="Add Artist", command=self.add_artist)
        self.add_button.pack(side=tk.LEFT)

        # Artist list
        self.artist_list_widget = tk.Listbox(self.root, height=5, width=50)
        self.artist_list_widget.pack(padx=10, pady=5, fill=tk.X)
        
        # Añadir scrollbar para la lista de artistas
        artist_scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.artist_list_widget.yview)
        artist_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.artist_list_widget.configure(yscrollcommand=artist_scrollbar.set)

        # Bind doble clic en la lista de artistas
        self.artist_list_widget.bind("<Double-Button-1>", self.get_suggestions_for_artist)

        # Suggestions label and Treeview
        ttk.Label(self.root, text="Suggested Tracks:").pack(padx=10, pady=5, anchor=tk.W)

        # Frame principal para sugerencias y botones
        main_content_frame = ttk.Frame(self.root)
        main_content_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Frame para las sugerencias
        self.suggestions_frame = ttk.Frame(main_content_frame)
        self.suggestions_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Frame para el Treeview de sugerencias
        tree_frame = ttk.Frame(self.suggestions_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Crear el Treeview con scrollbar
        self.suggestions_tree = ttk.Treeview(tree_frame, columns=('name', 'artist', 'album'), selectmode="extended")
        self.suggestions_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.suggestions_tree.yview)
        self.suggestions_tree.configure(yscrollcommand=self.suggestions_scrollbar.set)

        # Configurar las columnas
        self.suggestions_tree.heading('#0', text='Imagen', anchor=tk.CENTER)
        self.suggestions_tree.heading('name', text='Canción', anchor=tk.W)
        self.suggestions_tree.heading('artist', text='Artista', anchor=tk.W)
        self.suggestions_tree.heading('album', text='Álbum', anchor=tk.W)

        # Configurar el ancho de las columnas
        self.suggestions_tree.column('#0', width=100, minwidth=100)
        self.suggestions_tree.column('name', width=200, minwidth=150)
        self.suggestions_tree.column('artist', width=150, minwidth=100)
        self.suggestions_tree.column('album', width=200, minwidth=150)

        # Empaquetar el Treeview y el scrollbar
        self.suggestions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.suggestions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Añadir evento de doble clic
        self.suggestions_tree.bind("<Double-1>", self.add_selected_track_to_playlist)

        # Frame para mostrar la imagen de la canción seleccionada
        self.image_frame = ttk.Frame(self.suggestions_frame)
        self.image_frame.pack(side=tk.RIGHT, padx=10, pady=5)
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack()

        # Menú contextual para las sugerencias
        self.track_info_menu = tk.Menu(self.root, tearoff=0)
        self.track_info_menu.add_command(label="Ver Detalles", command=self._show_track_details_from_list)

        self.suggestions_tree.bind("<Button-3>", self.show_track_context_menu_list)
        self.suggestions_tree.bind("<<TreeviewSelect>>", self.update_selected_image)

        # Frame para los botones
        button_frame = ttk.Frame(main_content_frame)
        button_frame.pack(side=tk.RIGHT, padx=10, fill=tk.Y)

        self.suggest_button = ttk.Button(button_frame, text="Get Suggestions", command=self.get_suggestions)
        self.suggest_button.pack(pady=5, fill=tk.X)
        self.create_button = ttk.Button(button_frame, text="Create Playlist", command=self.create_playlist)
        self.create_button.pack(pady=5, fill=tk.X)
        self.reconnect_button = ttk.Button(button_frame, text="Reconnect Spotify", command=self.reconnect_spotify)
        self.reconnect_button.pack(pady=5, fill=tk.X)
        self.view_playlist_btn = ttk.Button(button_frame, text="Ver Playlist", command=self.prompt_playlist_id)
        self.view_playlist_btn.pack(pady=5, fill=tk.X)

        # Frame para la lista de canciones confirmadas
        self.tracks_frame = ttk.LabelFrame(self.root, text="Canciones Confirmadas")
        self.tracks_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Frame para los botones de gestión
        btn_frame = ttk.Frame(self.tracks_frame)
        btn_frame.pack(side=tk.TOP, pady=5)

        ttk.Button(btn_frame, text="Quitar Selección", command=self.remove_selected_tracks).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Actualizar Vista", command=self.refresh_tracks_view).pack(side=tk.LEFT, padx=5)

        # Canvas y scrollbar para la cuadrícula de canciones confirmadas
        self.tracks_canvas = tk.Canvas(self.tracks_frame)
        self.tracks_scrollbar = ttk.Scrollbar(self.tracks_frame, orient="vertical", command=self.tracks_canvas.yview)
        self.tracks_scrollable_frame = ttk.Frame(self.tracks_canvas)

        self.tracks_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.tracks_canvas.configure(scrollregion=self.tracks_canvas.bbox("all"))
        )

        self.tracks_canvas.create_window((0, 0), window=self.tracks_scrollable_frame, anchor="nw")
        self.tracks_canvas.configure(yscrollcommand=self.tracks_scrollbar.set)

        self.tracks_canvas.pack(side="left", fill="both", expand=True)
        self.tracks_scrollbar.pack(side="right", fill="y")

        # Log area
        self.log_area = scrolledtext.ScrolledText(self.root, height=5, width=50)
        self.log_area.pack(padx=10, pady=5, fill=tk.X)
        self.log_area.config(state=tk.DISABLED)

        # Configurar estilos para frames seleccionados
        style = ttk.Style()
        style.configure('Selected.TFrame', background='#e0e0e0')

    def log(self, message):
        """Append a message to the log area."""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
    
    def suggestions_canvas_yview(self, *args):
        """Maneja el scroll vertical de la cuadrícula de sugerencias."""
        self.suggestions_tree.yview(*args)

    def setup_environment(self):
        threading.Thread(target=connect_to_spotify, args=(self,), daemon=True).start()

    def reconnect_spotify(self):
        threading.Thread(target=reconnect_spotify_api, args=(self,), daemon=True).start()

    def add_artist(self):
        artist_name = self.artist_entry.get().strip()
        if artist_name:
            threading.Thread(target=self._add_artist_thread, args=(artist_name,), daemon=True).start()

    def _add_artist_thread(self, artist_name):
        artist_data = search_spotify_artist(self, artist_name)
        if artist_data:
            if artist_data['name'] not in self.artist_list_names:
                self.artist_list_names.append(artist_data['name'])
                self.artist_list_widget.insert(tk.END, artist_data['name'])
                self.artist_entry.delete(0, tk.END)
                # Limpiar la cuadrícula de sugerencias
                for item in self.suggestions_tree.get_children():
                    self.suggestions_tree.delete(item)
                self.image_cache.clear() # Limpiar la caché de imágenes también
                self.track_suggestions = [] # Limpiar la lista de datos de sugerencias
                self.log(f"Artista añadido: {artist_data['name']}")
            else:
                messagebox.showinfo("Artista ya añadido", f"{artist_data['name']} ya está en la lista.")
        else:
            messagebox.showwarning("Artista no encontrado", f"No se encontró al artista: {artist_name}")

    def get_suggestions_for_artist(self, event):
        """Obtiene sugerencias solo para el artista seleccionado."""
        selection = self.artist_list_widget.curselection()
        if selection:
            artist_name = self.artist_list_widget.get(selection[0])
            # Limpiar sugerencias actuales
            for item in self.suggestions_tree.get_children():
                self.suggestions_tree.delete(item)
            self.image_cache.clear()
            self.image_cache_list = []
            self.track_suggestions = []
            # Obtener sugerencias solo para este artista
            threading.Thread(target=self._get_suggestions_thread, args=([artist_name],), daemon=True).start()

    def get_suggestions(self):
        """Obtiene sugerencias para todos los artistas."""
        threading.Thread(target=self._get_suggestions_thread, args=(self.artist_list_names,), daemon=True).start()

    def _get_suggestions_thread(self, artists):
        """Thread para obtener sugerencias de manera asíncrona."""
        self.log("Obteniendo sugerencias...")
        if not artists:
            messagebox.showwarning("Sin artistas", "Por favor, añade al menos un artista para obtener sugerencias.")
            return
        get_suggestions_from_api(self, artists, self.update_suggestions_ui)
        self.log("Sugerencias obtenidas y mostradas.")

     # Para almacenar las imágenes cargadas y evitar garbage collection

    def update_suggestions_ui(self, suggestions):
        """Callback function to update the suggestions tree."""
        # Limpiar el Treeview
        for item in self.suggestions_tree.get_children():
            self.suggestions_tree.delete(item)
        self.track_suggestions = suggestions  # Guardar las sugerencias para referencia
        self.image_cache.clear()  # Limpiar caché de imágenes

        # Actualizar el Treeview con las nuevas sugerencias
        for track in suggestions:
            try:
                # Crear un placeholder para la imagen
                image_placeholder = "🖼️"
                
                # Insertar el track en el Treeview
                item_id = self.suggestions_tree.insert('', 'end', text=image_placeholder,
                                                    values=(track['name'], track['artist'], track['album']))
                
                # Cargar la imagen en segundo plano
                if track.get('image_url'):
                    try:
                        response = requests.get(track['image_url'], stream=True)
                        response.raise_for_status()
                        img = Image.open(BytesIO(response.content))
                        img = img.resize((50, 50), Image.Resampling.LANCZOS)
                        image_tk = ImageTk.PhotoImage(img)
                        # Guardar referencia
                        self.image_cache[item_id] = image_tk
                        # Actualizar la imagen en el Treeview
                        self.suggestions_tree.item(item_id, image=image_tk)
                    except Exception as e:
                        self.log(f"Error al cargar imagen: {e}")

            except Exception as e:
                self.log(f"Error al mostrar track en la interfaz: {e}")
                continue

        self.log(f"Se mostraron {len(suggestions)} sugerencias en la tabla")

    def show_track_context_menu_list(self, event):
        """Muestra el menú contextual al hacer clic derecho en una sugerencia."""
        try:
            item = self.suggestions_tree.identify_row(event.y)
            if item:
                self.suggestions_tree.selection_set(item)
                self.selected_suggestion_index = self.suggestions_tree.index(item)
                self.track_info_menu.post(event.x_root, event.y_root)
        except Exception as e:
            self.log(f"Error al mostrar el menú contextual: {e}")

    def update_selected_image(self, event):
        """Actualiza la imagen mostrada cuando se selecciona una canción."""
        try:
            selection = self.suggestions_tree.selection()
            if selection:
                item_id = selection[0]
                if item_id in self.image_cache:
                    self.image_label.configure(image=self.image_cache[item_id])
                    self.image_label.image = self.image_cache[item_id]
                else:
                    self.image_label.configure(image='')
                    self.image_label.image = None
        except Exception as e:
            self.log(f"Error al actualizar la imagen seleccionada: {e}")

    def select_suggestion_frame(self, event):
        """Maneja la selección de una sugerencia."""
        selection = self.suggestions_tree.selection()
        if selection:
            item_id = selection[0]
            index = self.suggestions_tree.index(item_id)
            if 0 <= index < len(self.track_suggestions):
                track = self.track_suggestions[index]
                if track['uri'] in self.image_cache:
                    self.image_label.configure(image=self.image_cache[track['uri']])
                    self.image_label.image = self.image_cache[track['uri']]

    def _show_track_details_from_list(self):
        """Función interna para mostrar los detalles del track seleccionado desde la lista."""
        if hasattr(self, 'selected_suggestion_index') and 0 <= self.selected_suggestion_index < len(self.track_suggestions):
            selected_track_uri = self.track_suggestions[self.selected_suggestion_index]['uri']
            threading.Thread(target=self.show_track_info, args=(selected_track_uri,), daemon=True).start()
        else:
            messagebox.showwarning("Sin selección", "Por favor, selecciona una canción para ver sus detalles.")

    
    def add_track_to_playlist(self, track):
        """Añade un track a la lista confirmada y actualiza la vista."""
        if track not in self.confirmed_tracks:
            self.confirmed_tracks.append(track)
            self.insert_track_in_treeview(track)  # Asegúrate de que esta línea esté aquí
            self.log(f"Canción añadida a la playlist: {track['name']} - {track['artist']}")
        else:
            messagebox.showinfo("Info", "Esta canción ya está en la playlist")

    def insert_track_in_treeview(self, track):
        """Inserta un track en la cuadrícula de canciones confirmadas."""
        # Contar cuántos tracks hay en la última fila
        current_row = len(self.tracks_scrollable_frame.winfo_children()) // 7
        current_col = len(self.tracks_scrollable_frame.winfo_children()) % 7

        frame = ttk.Frame(self.tracks_scrollable_frame)
        frame.grid(row=current_row, column=current_col, padx=5, pady=5)
        
        # Añadir evento de clic para selección
        frame.bind("<Button-1>", lambda e, f=frame: self.select_track_frame(f))
        
        # Guardar referencia al track en el frame
        frame.track = track

        # Cargar y mostrar la imagen primero
        if track.get('image_url'):
            try:
                response = requests.get(track['image_url'], stream=True)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
                img = img.resize((100, 100), Image.Resampling.LANCZOS)
                image_tk = ImageTk.PhotoImage(img)
                # Guardar referencia
                if not hasattr(self, 'confirmed_images_cache'):
                    self.confirmed_images_cache = {}
                self.confirmed_images_cache[track['uri']] = image_tk
                
                label = ttk.Label(frame, image=image_tk)
                label.image = image_tk  # Mantener referencia
                label.pack()
            except Exception as e:
                self.log(f"Error al cargar imagen: {e}")

        # Mostrar nombre de la canción
        ttk.Label(frame, text=track['name'], wraplength=100).pack()
        
        # Mostrar artista
        ttk.Label(frame, text=track['artist'], wraplength=100).pack()

    def select_track_frame(self, frame):
        """Maneja la selección de un frame de track."""
        if not hasattr(self, 'selected_frames'):
            self.selected_frames = set()
        
        if frame in self.selected_frames:
            # Deseleccionar
            frame.configure(style='TFrame')
            self.selected_frames.remove(frame)
        else:
            # Seleccionar
            frame.configure(style='Selected.TFrame')
            self.selected_frames.add(frame)

    def remove_selected_tracks(self):
        """Elimina los tracks seleccionados de la lista confirmada."""
        if not hasattr(self, 'selected_frames') or not self.selected_frames:
            messagebox.showwarning("Advertencia", "No hay canciones seleccionadas para quitar.")
            return

        # Obtener los tracks seleccionados
        tracks_to_remove = [frame.track for frame in self.selected_frames]
        
        # Eliminar los tracks de la lista confirmada
        for track in tracks_to_remove:
            if track in self.confirmed_tracks:
                self.confirmed_tracks.remove(track)

        # Limpiar la selección
        self.selected_frames.clear()
        
        # Actualizar la vista
        self.refresh_tracks_view()
        self.log(f"Se eliminaron {len(tracks_to_remove)} canciones.")

    def refresh_tracks_view(self):
        """Refresca la vista de la cuadrícula de canciones confirmadas."""
        # Limpiar el frame
        for widget in self.tracks_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Limpiar caché de imágenes
        if hasattr(self, 'confirmed_images_cache'):
            self.confirmed_images_cache.clear()
        
        # Reinsertar todas las canciones
        for track in self.confirmed_tracks:
            self.insert_track_in_treeview(track)

    def create_playlist(self):
        """Crea la playlist en Spotify con las canciones confirmadas."""
        if not self.confirmed_tracks:
            messagebox.showwarning("Advertencia", "No hay canciones en la playlist para crear.")
            return

        playlist_name = simpledialog.askstring("Nombre de Playlist", "Ingrese el nombre para la nueva playlist:")
        if not playlist_name:
            return

        track_uris = [track['uri'] for track in self.confirmed_tracks]
        threading.Thread(target=self._create_playlist_thread, args=(playlist_name, track_uris), daemon=True).start()

    def show_track_info(self, track_uri):
        """Muestra la información detallada de un track"""
        try:
            if not self.sp:
                messagebox.showerror("Error", "No se ha conectado a Spotify.")
                return

            track = self.sp.track(track_uri)
            # Mostrar información básica en el log
            self.log(f"Información de la canción: {track['name']} - {track['artists'][0]['name']}")

        except spotipy.exceptions.SpotifyException as e:
            messagebox.showerror("Error de Spotify", f"No se pudo obtener información del track: {e}")
            self.log(f"Error al obtener información del track: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al obtener información del track: {e}")
            self.log(f"Error inesperado al obtener información del track: {e}")

    def format_duration(self, ms):
        """Formatea la duración en milisegundos a minutos:segundos."""
        minutes = int(ms / 60000)
        seconds = int((ms % 60000) / 1000)
        return f"{minutes}:{seconds:02d}"

    def _create_playlist_thread(self, playlist_name, track_uris):
        self.log(f"Creando playlist '{playlist_name}' con {len(track_uris)} canciones...")
        try:
            if not self.sp:
                messagebox.showerror("Error", "No se ha conectado a Spotify.")
                return

            # Crear playlist
            user_id = self.sp.me()['id']
            playlist = self.sp.user_playlist_create(user_id, playlist_name, public=False)

            # Añadir tracks
            self.sp.playlist_add_items(playlist['id'], track_uris)

            messagebox.showinfo("Éxito", f"Playlist '{playlist_name}' creada con {len(track_uris)} canciones")
            webbrowser.open(playlist['external_urls']['spotify'])
            self.log(f"Playlist '{playlist_name}' creada exitosamente.")

        except spotipy.exceptions.SpotifyException as e:
            messagebox.showerror("Error de Spotify", f"No se pudo crear la playlist: {e}")
            self.log(f"Error al crear la playlist: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al crear la playlist: {e}")
            self.log(f"Error inesperado al crear la playlist: {e}")

    def prompt_playlist_id(self):
        playlist_id = simpledialog.askstring("Ver Playlist", "Ingrese el ID de la playlist de Spotify:")
        if playlist_id:
            threading.Thread(target=self._get_playlist_tracks_thread, args=(playlist_id,), daemon=True).start()

    def _get_playlist_tracks_thread(self, playlist_id):
        self.log(f"Obteniendo pistas de la playlist con ID: {playlist_id}...")
        get_playlist_tracks_from_api(self, playlist_id, self.update_confirmed_tracks_from_playlist)
        self.log(f"Pistas de la playlist obtenidas.")

    def update_confirmed_tracks_from_playlist(self, tracks):
        self.confirmed_tracks = tracks
        self.refresh_tracks_view()

    def add_selected_track_to_playlist(self, event):
        """Añade la canción seleccionada a la lista de canciones confirmadas."""
        try:
            selection = self.suggestions_tree.selection()
            if selection:
                item_id = selection[0]
                index = self.suggestions_tree.index(item_id)
                if 0 <= index < len(self.track_suggestions):
                    track = self.track_suggestions[index]
                    if track not in self.confirmed_tracks:
                        self.confirmed_tracks.append(track)
                        self.insert_track_in_treeview(track)
                        self.log(f"Canción añadida a la playlist: {track['name']} - {track['artist']}")
                    else:
                        messagebox.showinfo("Info", "Esta canción ya está en la playlist")
        except Exception as e:
            self.log(f"Error al añadir canción a la playlist: {e}")