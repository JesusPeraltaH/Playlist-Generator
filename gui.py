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
from music_ai import MusicRecommender
import pygame
import time



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
        self.similar_images_cache = {}  # Cache for similar suggestions images
        self.recommender = None
        self.current_preview = None
        self.setup_credentials()
        self.setup_ui()
        self.setup_environment()
        self.setup_audio()
        self.image_cache = {}

    def setup_credentials(self):
        # Load credentials (you might want to handle this more securely)
        import os
        from dotenv import load_dotenv, find_dotenv
        load_dotenv(find_dotenv())
        self.client_id = os.getenv('SPOTIPY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')

    def setup_audio(self):
        """Inicializa el sistema de audio."""
        pygame.mixer.init()

    def setup_ui(self):
        # Artist input
        self.artist_frame = ttk.Frame(self.root)
        self.artist_frame.pack(padx=10, pady=5, fill=tk.X)
        ttk.Label(self.artist_frame, text="Artist:").pack(side=tk.LEFT)
        self.artist_entry = ttk.Entry(self.artist_frame)
        self.artist_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.add_button = ttk.Button(self.artist_frame, text="Add Artist", command=self.add_artist)
        self.add_button.pack(side=tk.LEFT)

        # Menú contextual para las sugerencias
        self.track_info_menu = tk.Menu(self.root, tearoff=0)
        self.track_info_menu.add_command(label="Ver Detalles", command=self._show_track_details_from_list)
        
        # Artist list
        self.artist_list_widget = tk.Listbox(self.root, height=5, width=50)
        self.artist_list_widget.pack(padx=10, pady=5, fill=tk.X)
        
        # Añadir scrollbar para la lista de artistas
        artist_scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.artist_list_widget.yview)
        artist_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.artist_list_widget.configure(yscrollcommand=artist_scrollbar.set)

        # Bind doble clic en la lista de artistas
        self.artist_list_widget.bind("<Double-Button-1>", self.get_suggestions_for_artist)

        # Frame principal para sugerencias
        suggestions_main_frame = ttk.Frame(self.root)
        suggestions_main_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Frame para las sugerencias normales
        self.suggestions_frame = ttk.LabelFrame(suggestions_main_frame, text="Suggested Tracks")
        self.suggestions_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

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
        self.suggestions_tree.bind("<<TreeviewSelect>>", self.update_selected_image)

        # Frame para sugerencias similares
        self.similar_suggestions_frame = ttk.LabelFrame(suggestions_main_frame, text="Sugerencias Similares")
        self.similar_suggestions_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Frame para el Treeview de sugerencias similares
        similar_tree_frame = ttk.Frame(self.similar_suggestions_frame)
        similar_tree_frame.pack(fill=tk.BOTH, expand=True)

        # Crear el Treeview con scrollbar para sugerencias similares
        self.similar_suggestions_tree = ttk.Treeview(similar_tree_frame, columns=('name', 'artist', 'album'), selectmode="extended")
        self.similar_suggestions_scrollbar = ttk.Scrollbar(similar_tree_frame, orient="vertical", command=self.similar_suggestions_tree.yview)
        self.similar_suggestions_tree.configure(yscrollcommand=self.similar_suggestions_scrollbar.set)

        # Configurar las columnas
        self.similar_suggestions_tree.heading('#0', text='Imagen', anchor=tk.CENTER)
        self.similar_suggestions_tree.heading('name', text='Canción', anchor=tk.W)
        self.similar_suggestions_tree.heading('artist', text='Artista', anchor=tk.W)
        self.similar_suggestions_tree.heading('album', text='Álbum', anchor=tk.W)

        # Configurar el ancho de las columnas
        self.similar_suggestions_tree.column('#0', width=100, minwidth=100)
        self.similar_suggestions_tree.column('name', width=200, minwidth=150)
        self.similar_suggestions_tree.column('artist', width=150, minwidth=100)
        self.similar_suggestions_tree.column('album', width=200, minwidth=150)

        # Empaquetar el Treeview y el scrollbar
        self.similar_suggestions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.similar_suggestions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Frame para los botones de sugerencias
        suggestions_buttons_frame = ttk.Frame(self.root)
        suggestions_buttons_frame.pack(padx=10, pady=5, fill=tk.X)

        # Botones para sugerencias normales
        self.suggest_button = ttk.Button(suggestions_buttons_frame, text="Get Suggestions", command=self.get_suggestions)
        self.suggest_button.pack(side=tk.LEFT, padx=5)
        
        # Botones para sugerencias similares
        self.similar_songs_button = ttk.Button(suggestions_buttons_frame, text="Canciones Similares", command=self.get_similar_songs)
        self.similar_songs_button.pack(side=tk.LEFT, padx=5)

        # Frame para botones de playlist
        playlist_buttons_frame = ttk.Frame(self.root)
        playlist_buttons_frame.pack(padx=10, pady=5, fill=tk.X)

        self.create_button = ttk.Button(playlist_buttons_frame, text="Create Playlist", command=self.create_playlist)
        self.create_button.pack(side=tk.LEFT, padx=5)
        
        self.reconnect_button = ttk.Button(playlist_buttons_frame, text="Reconnect Spotify", command=self.reconnect_spotify)
        self.reconnect_button.pack(side=tk.LEFT, padx=5)
        
        self.view_playlist_btn = ttk.Button(playlist_buttons_frame, text="Ver Playlist", command=self.prompt_playlist_id)
        self.view_playlist_btn.pack(side=tk.LEFT, padx=5)

        # Frame para controles de reproducción
        self.playback_frame = ttk.LabelFrame(self.root, text="Reproducción")
        self.playback_frame.pack(padx=10, pady=5, fill=tk.X)
        
        self.play_button = ttk.Button(self.playback_frame, text="▶️ Reproducir", command=self.play_preview)
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(self.playback_frame, text="⏹️ Detener", command=self.stop_preview)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Frame para la lista de canciones confirmadas
        self.tracks_frame = ttk.LabelFrame(self.root, text="Canciones Confirmadas")
        self.tracks_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Frame para los botones de gestión
        btn_frame = ttk.Frame(self.tracks_frame)
        btn_frame.pack(side=tk.TOP, pady=5)

        ttk.Button(btn_frame, text="Quitar Selección", command=self.remove_selected_tracks).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Actualizar Vista", command=self.refresh_tracks_view).pack(side=tk.LEFT, padx=5)

        # Crear Treeview para canciones confirmadas
        self.confirmed_tracks_tree = ttk.Treeview(self.tracks_frame, columns=('name', 'artist'), selectmode='extended')
        self.confirmed_tracks_tree.heading('#0', text='Imagen')
        self.confirmed_tracks_tree.heading('name', text='Canción')
        self.confirmed_tracks_tree.heading('artist', text='Artista')

        # Configurar columnas
        self.confirmed_tracks_tree.column('#0', width=100, minwidth=100)
        self.confirmed_tracks_tree.column('name', width=200, minwidth=150)
        self.confirmed_tracks_tree.column('artist', width=150, minwidth=100)

        # Scrollbar para el Treeview
        confirmed_scrollbar = ttk.Scrollbar(self.tracks_frame, orient="vertical", command=self.confirmed_tracks_tree.yview)
        self.confirmed_tracks_tree.configure(yscrollcommand=confirmed_scrollbar.set)

        # Empaquetar Treeview y scrollbar
        self.confirmed_tracks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        confirmed_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind eventos
        self.confirmed_tracks_tree.bind("<Double-1>", self.play_selected_confirmed_track)
        self.confirmed_tracks_tree.bind("<Button-3>", self.show_confirmed_track_menu)
        self.confirmed_tracks_tree.bind("<<TreeviewSelect>>", self.on_confirmed_track_select)

        # Menú contextual para canciones confirmadas
        self.confirmed_track_menu = tk.Menu(self.root, tearoff=0)
        self.confirmed_track_menu.add_command(label="Reproducir Vista Previa", command=self.play_selected_confirmed_track)
        self.confirmed_track_menu.add_command(label="Ver Detalles", command=self.show_selected_confirmed_track_details)

        # Log area
        self.log_area = scrolledtext.ScrolledText(self.root, height=5, width=50)
        self.log_area.pack(padx=10, pady=5, fill=tk.X)
        self.log_area.config(state=tk.DISABLED)

        # Configurar estilos para frames seleccionados
        style = ttk.Style()
        style.configure('Selected.TFrame', background='#e0e0e0')
        style.configure('TFrame', background='white')

        # Frame para mostrar la imagen de la canción seleccionada
        self.image_frame = ttk.Frame(self.suggestions_frame)
        self.image_frame.pack(side=tk.RIGHT, padx=10, pady=5)
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.pack()

        # Frame para mostrar la imagen de la sugerencia seleccionada
        self.similar_image_frame = ttk.Frame(self.similar_suggestions_frame)
        self.similar_image_frame.pack(side=tk.RIGHT, padx=10, pady=5)
        self.similar_image_label = ttk.Label(self.similar_image_frame)
        self.similar_image_label.pack()

        # Bind eventos para el Treeview de sugerencias similares
        self.similar_suggestions_tree.bind("<Double-1>", lambda e: self.play_similar_suggestion())
        self.similar_suggestions_tree.bind("<<TreeviewSelect>>", self.update_similar_selected_image)

        # Frame para controles de reproducción de sugerencias similares
        similar_playback_frame = ttk.Frame(self.similar_suggestions_frame)
        similar_playback_frame.pack(padx=5, pady=5, fill=tk.X)
        
        self.similar_play_button = ttk.Button(similar_playback_frame, text="▶️ Reproducir", command=self.play_similar_suggestion)
        self.similar_play_button.pack(side=tk.LEFT, padx=5)
        
        self.similar_stop_button = ttk.Button(similar_playback_frame, text="⏹️ Detener", command=self.stop_similar_preview)
        self.similar_stop_button.pack(side=tk.LEFT, padx=5)
        
        self.similar_add_button = ttk.Button(similar_playback_frame, text="➕ Añadir a Playlist", command=self.add_similar_to_playlist)
        self.similar_add_button.pack(side=tk.LEFT, padx=5)

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
        """Inicializa el entorno de la aplicación."""
        threading.Thread(target=connect_to_spotify, args=(self,), daemon=True).start()
        # Inicializar el recomendador cuando se conecte a Spotify
        if self.sp:
            self.recommender = MusicRecommender(self.sp)

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

    def update_similar_suggestions_ui(self, suggestions):
        """Callback function to update the similar suggestions tree."""
        # Limpiar el Treeview de sugerencias similares
        for item in self.similar_suggestions_tree.get_children():
            self.similar_suggestions_tree.delete(item)
        
        # Limpiar caché de imágenes
        self.similar_images_cache.clear()

        # Actualizar el Treeview con las nuevas sugerencias
        for track in suggestions:
            try:
                # Crear un placeholder para la imagen
                image_placeholder = "🖼️"
                
                # Insertar el track en el Treeview de sugerencias similares
                item_id = self.similar_suggestions_tree.insert('', 'end', text=image_placeholder,
                                                    values=(track['name'], track['artist'], track['album']),
                                                    tags=(track['uri'],))
                
                # Cargar la imagen en segundo plano
                if track.get('image_url'):
                    try:
                        response = requests.get(track['image_url'], stream=True)
                        response.raise_for_status()
                        img = Image.open(BytesIO(response.content))
                        img = img.resize((50, 50), Image.Resampling.LANCZOS)
                        image_tk = ImageTk.PhotoImage(img)
                        # Guardar referencia
                        self.similar_images_cache[item_id] = image_tk
                        # Actualizar la imagen en el Treeview
                        self.similar_suggestions_tree.item(item_id, image=image_tk)
                    except Exception as e:
                        self.log(f"Error al cargar imagen: {e}")

            except Exception as e:
                self.log(f"Error al mostrar track en la interfaz: {e}")
                continue

        self.log(f"Se mostraron {len(suggestions)} sugerencias similares en la tabla")

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
        """Inserta un track en el Treeview de canciones confirmadas."""
        try:
            # Crear un placeholder para la imagen
            image_placeholder = "🖼️"
            
            # Insertar el track en el Treeview
            item_id = self.confirmed_tracks_tree.insert('', 'end', text=image_placeholder,
                                                      values=(track['name'], track['artist']))
            
            # Cargar la imagen en segundo plano
            if track.get('image_url'):
                try:
                    response = requests.get(track['image_url'], stream=True)
                    response.raise_for_status()
                    img = Image.open(BytesIO(response.content))
                    img = img.resize((50, 50), Image.Resampling.LANCZOS)
                    image_tk = ImageTk.PhotoImage(img)
                    # Guardar referencia
                    if not hasattr(self, 'confirmed_images_cache'):
                        self.confirmed_images_cache = {}
                    self.confirmed_images_cache[item_id] = image_tk
                    # Actualizar la imagen en el Treeview
                    self.confirmed_tracks_tree.item(item_id, image=image_tk)
                except Exception as e:
                    self.log(f"Error al cargar imagen: {e}")
            
            # Guardar referencia al track en el item
            self.confirmed_tracks_tree.item(item_id, tags=(track['uri'],))
            
        except Exception as e:
            self.log(f"Error al insertar track en Treeview: {e}")

    def remove_selected_tracks(self):
        """Elimina los tracks seleccionados de la lista confirmada."""
        selection = self.confirmed_tracks_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "No hay canciones seleccionadas para quitar.")
            return

        # Obtener los tracks seleccionados
        tracks_to_remove = []
        for item_id in selection:
            track_uri = self.confirmed_tracks_tree.item(item_id)['tags'][0]
            for track in self.confirmed_tracks:
                if track['uri'] == track_uri:
                    tracks_to_remove.append(track)
                    break
        
        # Eliminar los tracks de la lista confirmada
        for track in tracks_to_remove:
            if track in self.confirmed_tracks:
                self.confirmed_tracks.remove(track)
        
        # Actualizar la vista
        self.refresh_tracks_view()
        self.log(f"Se eliminaron {len(tracks_to_remove)} canciones.")

    def refresh_tracks_view(self):
        """Refresca la vista del Treeview de canciones confirmadas."""
        # Limpiar el Treeview
        for item in self.confirmed_tracks_tree.get_children():
            self.confirmed_tracks_tree.delete(item)
        
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
                    self.log(f"Intentando añadir canción: {track['name']} - {track['artist']}")
                    self.log(f"URI de la canción: {track['uri']}")
                    
                    # Verificar que la canción existe en Spotify
                    try:
                        track_info = self.sp.track(track['uri'])
                        if track_info:
                            self.log(f"Canción encontrada en Spotify: {track_info['name']}")
                            if track not in self.confirmed_tracks:
                                self.confirmed_tracks.append(track)
                                self.insert_track_in_treeview(track)
                                self.log(f"Canción añadida a la playlist: {track['name']} - {track['artist']}")
                            else:
                                messagebox.showinfo("Info", "Esta canción ya está en la playlist")
                        else:
                            self.log("No se pudo encontrar la canción en Spotify")
                    except Exception as e:
                        self.log(f"Error al verificar la canción en Spotify: {str(e)}")
                        messagebox.showerror("Error", f"Error al verificar la canción: {str(e)}")
        except Exception as e:
            self.log(f"Error al añadir canción a la playlist: {e}")

    def get_similar_songs(self):
        """Obtiene canciones similares a las de la playlist actual."""
        if not self.confirmed_tracks:
            messagebox.showwarning("Sin canciones", "Por favor, añade canciones a la playlist primero.")
            return
            
        if not self.sp:
            messagebox.showerror("Error", "No hay conexión con Spotify.")
            return
            
        # Obtener URIs de las canciones confirmadas (máximo 5 para las semillas)
        track_uris = [track['uri'] for track in self.confirmed_tracks[:5]]
        
        # Mostrar mensaje de carga
        self.log("Buscando canciones similares...")
        
        # Obtener sugerencias en un hilo separado
        threading.Thread(target=self._get_similar_songs_thread, args=(track_uris,), daemon=True).start()

    def _get_similar_songs_thread(self, track_uris):
        """Thread para obtener canciones similares."""
        try:
            # Obtener géneros de los artistas en la lista
            genres = set()
            for track in self.confirmed_tracks:
                self.log(f"Procesando canción: {track['name']} - {track['artist']}")
                try:
                    # Obtener información del track
                    track_info = self.sp.track(track['uri'])
                    if track_info and track_info['artists']:
                        artist = track_info['artists'][0]
                        artist_id = artist['id']
                        # Obtener información del artista
                        artist_info = self.sp.artist(artist_id)
                        if artist_info and artist_info['genres']:
                            genres.update(artist_info['genres'])
                            self.log(f"Géneros encontrados para {artist['name']}: {artist_info['genres']}")
                except Exception as e:
                    self.log(f"Error al procesar el track {track['uri']}: {str(e)}")
            
            if not genres:
                self.log("No se encontraron géneros para obtener recomendaciones.")
                return
                
            self.log(f"Géneros encontrados: {genres}")
            
            # Buscar artistas populares en estos géneros
            suggestions = []
            for genre in list(genres)[:3]:  # Usar hasta 3 géneros
                try:
                    # Buscar artistas populares en este género
                    results = self.sp.search(q=f'genre:{genre}', type='artist', limit=10)
                    if results and results['artists']['items']:
                        for artist in results['artists']['items']:
                            # Obtener las canciones más populares del artista
                            top_tracks = self.sp.artist_top_tracks(artist['id'])
                            if top_tracks and top_tracks['tracks']:
                                for track in top_tracks['tracks'][:2]:  # Tomar las 2 canciones más populares
                                    # Verificar que la canción no esté ya en la lista confirmada
                                    if track['uri'] not in [t['uri'] for t in self.confirmed_tracks]:
                                        track_data = {
                                            'name': track['name'],
                                            'artist': track['artists'][0]['name'],
                                            'album': track['album']['name'],
                                            'uri': track['uri'],
                                            'image_url': track['album']['images'][-1]['url'] if track['album']['images'] else None,
                                            'preview_url': track.get('preview_url')
                                        }
                                        suggestions.append(track_data)
                                        self.log(f"Sugerencia encontrada: {track_data['name']} - {track_data['artist']} (Género: {genre})")
                except Exception as e:
                    self.log(f"Error al buscar artistas en el género {genre}: {str(e)}")
            
            if not suggestions:
                self.log("No se encontraron nuevas sugerencias.")
                return
            
            # Actualizar la interfaz
            self.root.after(0, lambda: self.update_similar_suggestions_ui(suggestions))
            self.log(f"Se encontraron {len(suggestions)} canciones similares.")
            
        except Exception as e:
            error_msg = f"Error al obtener canciones similares: {str(e)}"
            self.log(error_msg)
            messagebox.showerror("Error", error_msg)

    def play_preview(self):
        """Reproduce la vista previa de la canción seleccionada."""
        try:
            # Primero intentar reproducir una canción confirmada seleccionada
            selection = self.confirmed_tracks_tree.selection()
            if selection:
                self.play_selected_confirmed_track()
                return
                
            # Si no hay canción confirmada seleccionada, intentar con las sugerencias
            selection = self.suggestions_tree.selection()
            if not selection:
                messagebox.showwarning("Sin selección", "Por favor, selecciona una canción para reproducir.")
                return
                
            item_id = selection[0]
            index = self.suggestions_tree.index(item_id)
            if 0 <= index < len(self.track_suggestions):
                track = self.track_suggestions[index]
                
                # Detener reproducción actual si existe
                self.stop_preview()
                
                # Obtener URL de vista previa directamente de Spotify
                if not self.sp:
                    messagebox.showerror("Error", "No hay conexión con Spotify.")
                    return
                    
                track_info = self.sp.track(track['uri'])
                preview_url = track_info.get('preview_url')
                
                if not preview_url:
                    messagebox.showinfo("Info", "No hay vista previa disponible para esta canción.")
                    return
                
                # Descargar y reproducir
                response = requests.get(preview_url)
                with open("temp_preview.mp3", "wb") as f:
                    f.write(response.content)
                
                pygame.mixer.music.load("temp_preview.mp3")
                pygame.mixer.music.play()
                self.current_preview = "temp_preview.mp3"
                
                self.log(f"Reproduciendo: {track['name']} - {track['artist']}")
                
        except Exception as e:
            self.log(f"Error al reproducir vista previa: {e}")

    def stop_preview(self):
        """Detiene la reproducción actual."""
        try:
            pygame.mixer.music.stop()
            if self.current_preview:
                import os
                if os.path.exists(self.current_preview):
                    os.remove(self.current_preview)
                self.current_preview = None
        except Exception as e:
            self.log(f"Error al detener reproducción: {e}")

    def show_confirmed_track_menu(self, event):
        """Muestra el menú contextual para una canción confirmada."""
        item = self.confirmed_tracks_tree.identify_row(event.y)
        if item:
            self.confirmed_tracks_tree.selection_set(item)
            self.confirmed_track_menu.post(event.x_root, event.y_root)

    def play_selected_confirmed_track(self):
        """Reproduce la vista previa de la canción confirmada seleccionada o abre en Spotify."""
        selection = self.confirmed_tracks_tree.selection()
        if not selection:
            messagebox.showwarning("Sin selección", "Por favor, selecciona una canción para reproducir.")
            return
            
        item_id = selection[0]
        track_uri = self.confirmed_tracks_tree.item(item_id)['tags'][0]
        for track in self.confirmed_tracks:
            if track['uri'] == track_uri:
                try:
                    # Detener reproducción actual si existe
                    self.stop_preview()
                    
                    # Obtener información del track
                    if not self.sp:
                        messagebox.showerror("Error", "No hay conexión con Spotify.")
                        return
                        
                    track_info = self.sp.track(track_uri)
                    preview_url = track_info.get('preview_url')
                    
                    if preview_url:
                        # Descargar y reproducir vista previa
                        response = requests.get(preview_url)
                        with open("temp_preview.mp3", "wb") as f:
                            f.write(response.content)
                        
                        pygame.mixer.music.load("temp_preview.mp3")
                        pygame.mixer.music.play()
                        self.current_preview = "temp_preview.mp3"
                        
                        self.log(f"Reproduciendo vista previa: {track['name']} - {track['artist']}")
                    else:
                        # Si no hay vista previa, abrir en Spotify
                        spotify_url = track_info['external_urls']['spotify']
                        self.log(f"No hay vista previa disponible. Abriendo en Spotify: {track['name']} - {track['artist']}")
                        webbrowser.open(spotify_url)
                    break
                except Exception as e:
                    self.log(f"Error al reproducir canción: {e}")
                    messagebox.showerror("Error", f"Error al reproducir canción: {e}")

    def show_selected_confirmed_track_details(self):
        """Muestra los detalles de la canción confirmada seleccionada."""
        selection = self.confirmed_tracks_tree.selection()
        if not selection:
            messagebox.showwarning("Sin selección", "Por favor, selecciona una canción para ver sus detalles.")
            return
            
        item_id = selection[0]
        track_uri = self.confirmed_tracks_tree.item(item_id)['tags'][0]
        threading.Thread(target=self.show_track_info, args=(track_uri,), daemon=True).start()

    def on_confirmed_track_select(self, event):
        """Maneja la selección de tracks en el Treeview de canciones confirmadas."""
        selection = self.confirmed_tracks_tree.selection()
        if selection:
            item_id = selection[0]
            track_uri = self.confirmed_tracks_tree.item(item_id)['tags'][0]
            for track in self.confirmed_tracks:
                if track['uri'] == track_uri:
                    self.log(f"Canción seleccionada: {track['name']} - {track['artist']}")
                    break

    def play_similar_suggestion(self):
        """Reproduce la vista previa de la sugerencia seleccionada."""
        try:
            selection = self.similar_suggestions_tree.selection()
            if not selection:
                messagebox.showwarning("Sin selección", "Por favor, selecciona una canción para reproducir.")
                return
                
            item_id = selection[0]
            track_uri = self.similar_suggestions_tree.item(item_id)['tags'][0]
            
            # Detener reproducción actual si existe
            self.stop_similar_preview()
            
            # Obtener información del track
            if not self.sp:
                messagebox.showerror("Error", "No hay conexión con Spotify.")
                return
                
            track_info = self.sp.track(track_uri)
            preview_url = track_info.get('preview_url')
            
            if preview_url:
                # Descargar y reproducir vista previa
                response = requests.get(preview_url)
                with open("temp_similar_preview.mp3", "wb") as f:
                    f.write(response.content)
                
                pygame.mixer.music.load("temp_similar_preview.mp3")
                pygame.mixer.music.play()
                self.current_similar_preview = "temp_similar_preview.mp3"
                
                self.log(f"Reproduciendo sugerencia: {track_info['name']} - {track_info['artists'][0]['name']}")
            else:
                # Si no hay vista previa, abrir en Spotify
                spotify_url = track_info['external_urls']['spotify']
                self.log(f"No hay vista previa disponible. Abriendo en Spotify: {track_info['name']}")
                webbrowser.open(spotify_url)
                
        except Exception as e:
            self.log(f"Error al reproducir sugerencia: {e}")
            messagebox.showerror("Error", f"Error al reproducir sugerencia: {e}")

    def stop_similar_preview(self):
        """Detiene la reproducción de la sugerencia actual."""
        try:
            pygame.mixer.music.stop()
            if hasattr(self, 'current_similar_preview') and self.current_similar_preview:
                import os
                if os.path.exists(self.current_similar_preview):
                    os.remove(self.current_similar_preview)
                self.current_similar_preview = None
        except Exception as e:
            self.log(f"Error al detener reproducción: {e}")

    def add_similar_to_playlist(self):
        """Añade la sugerencia seleccionada a la playlist."""
        try:
            selection = self.similar_suggestions_tree.selection()
            if not selection:
                messagebox.showwarning("Sin selección", "Por favor, selecciona una canción para añadir.")
                return
                
            item_id = selection[0]
            track_uri = self.similar_suggestions_tree.item(item_id)['tags'][0]
            
            # Obtener información del track
            track_info = self.sp.track(track_uri)
            track_data = {
                'name': track_info['name'],
                'artist': track_info['artists'][0]['name'],
                'album': track_info['album']['name'],
                'uri': track_info['uri'],
                'image_url': track_info['album']['images'][-1]['url'] if track_info['album']['images'] else None,
                'preview_url': track_info.get('preview_url')
            }
            
            if track_data not in self.confirmed_tracks:
                self.confirmed_tracks.append(track_data)
                self.insert_track_in_treeview(track_data)
                self.log(f"Canción añadida a la playlist: {track_data['name']} - {track_data['artist']}")
            else:
                messagebox.showinfo("Info", "Esta canción ya está en la playlist")
                
        except Exception as e:
            self.log(f"Error al añadir sugerencia a la playlist: {e}")
            messagebox.showerror("Error", f"Error al añadir sugerencia: {e}")

    def update_similar_selected_image(self, event):
        """Actualiza la imagen mostrada cuando se selecciona una sugerencia."""
        try:
            selection = self.similar_suggestions_tree.selection()
            if selection:
                item_id = selection[0]
                if hasattr(self, 'similar_images_cache') and item_id in self.similar_images_cache:
                    self.similar_image_label.configure(image=self.similar_images_cache[item_id])
                    self.similar_image_label.image = self.similar_images_cache[item_id]
                else:
                    self.similar_image_label.configure(image='')
                    self.similar_image_label.image = None
        except Exception as e:
            self.log(f"Error al actualizar la imagen seleccionada: {e}")

    def __del__(self):
        """Limpieza al cerrar la aplicación."""
        self.stop_preview()
        pygame.mixer.quit()