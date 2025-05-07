from tkinter import ttk, messagebox, scrolledtext, simpledialog
import tkinter as tk
import threading
import webbrowser
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotify_api import connect_to_spotify, get_suggestions_from_api, create_spotify_playlist as create_spotify_playlist_api, reconnect_spotify_api, search_spotify_artist, get_playlist_tracks_from_api

class SpotifyPlaylistCreator:
    """A GUI application for creating Spotify playlists based on artist suggestions."""
    def __init__(self, root):
        self.root = root
        self.root.title("Spotify Playlist Creator")
        self.sp = None
        self.artist_list_names = []  # To store artist names        self.track_suggestions = [] # To store the full track suggestion data
        self.confirmed_tracks = [] # List to store confirmed tracks with metadata
        self.client_id = 'd406b45ab61149a7aca00ec8d7ee3ee7'
        self.client_secret = '873dc6688e9947f9ba16c9c77d48e9a9'
        self.redirect_uri = 'http://localhost:8888/callback' # Default redirect URI
        self.setup_credentials()
        self.setup_ui()
        self.setup_environment()

    def setup_credentials(self):
        # Load credentials (you might want to handle this more securely)
        import os
        from dotenv import load_dotenv, find_dotenv
        load_dotenv(find_dotenv())
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

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

         # Suggestions label and listbox
        ttk.Label(self.root, text="Suggested Tracks:").pack(padx=10, pady=5, anchor=tk.W)
        self.suggestions_list_widget = tk.Listbox(self.root, height=10, width=50, selectmode=tk.MULTIPLE)
        self.suggestions_list_widget.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.suggestions_list_widget.bind("<Double-Button-1>", self.confirm_track)
        self.suggestions_list_widget.bind("<Button-3>", self.show_track_context_menu) # Right-click context menu

        self.track_info_menu = tk.Menu(self.root, tearoff=0)
        self.track_info_menu.add_command(label="Ver Detalles", command=self._show_track_details)

        # Buttons
        self.button_frame = ttk.Frame(self.root)
        self.button_frame.pack(padx=10, pady=5, fill=tk.X)
        self.suggest_button = ttk.Button(self.button_frame, text="Get Suggestions", command=self.get_suggestions)
        self.suggest_button.pack(side=tk.LEFT, padx=5)
        self.create_button = ttk.Button(self.button_frame, text="Create Playlist", command=self.create_playlist)
        self.create_button.pack(side=tk.LEFT, padx=5)
        self.reconnect_button = ttk.Button(self.button_frame, text="Reconnect Spotify", command=self.reconnect_spotify)
        self.reconnect_button.pack(side=tk.LEFT, padx=5)
        self.view_playlist_btn = ttk.Button(self.button_frame, text="Ver Playlist",command=self.prompt_playlist_id)
        self.view_playlist_btn.pack(side=tk.LEFT, padx=5)

        # Log area
        self.log_area = scrolledtext.ScrolledText(self.root, height=5, width=50)
        self.log_area.pack(padx=10, pady=5, fill=tk.X)
        self.log_area.config(state=tk.DISABLED)

        # Frame para la lista de canciones confirmadas
        self.tracks_frame = ttk.LabelFrame(self.root, text="Canciones Confirmadas")
        self.tracks_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Treeview para mostrar canciones con columnas
        self.tracks_tree = ttk.Treeview(self.tracks_frame, columns=('name', 'artist', 'album'), selectmode='extended')
        self.tracks_tree.heading('#0', text='Imagen')
        self.tracks_tree.heading('name', text='Canción')
        self.tracks_tree.heading('artist', text='Artista')
        self.tracks_tree.heading('album', text='Álbum')

        # Configurar columnas
        self.tracks_tree.column('#0', width=0, stretch=tk.NO) # Ocultar la columna '#0'
        self.tracks_tree.column('name', anchor=tk.W)
        self.tracks_tree.column('artist', anchor=tk.W)
        self.tracks_tree.column('album', anchor=tk.W)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.tracks_frame, orient="vertical", command=self.tracks_tree.yview)
        self.tracks_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tracks_tree.pack(fill=tk.BOTH, expand=True)

        # Botones para gestionar la playlist
        btn_frame = ttk.Frame(self.tracks_frame)
        btn_frame.pack(pady=5)

        ttk.Button(btn_frame, text="Quitar Selección", command=self.remove_selected_tracks).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Actualizar Vista", command=self.refresh_tracks_view).pack(side=tk.LEFT, padx=5)

        # Frame para detalles del track
        self.track_details_frame = ttk.LabelFrame(self.root, text="Detalles del Track")
        self.track_details_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.track_details_text = scrolledtext.ScrolledText(self.track_details_frame, height=5, width=50)
        self.track_details_text.pack(fill=tk.BOTH, expand=True)
        self.track_details_text.config(state=tk.DISABLED)

    def log(self, message):
        """Append a message to the log area."""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

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
                self.log(f"Artista añadido: {artist_data['name']}")
            else:
                messagebox.showinfo("Artista ya añadido", f"{artist_data['name']} ya está en la lista.")
        else:
            messagebox.showwarning("Artista no encontrado", f"No se encontró al artista: {artist_name}")

    def get_suggestions(self):
        threading.Thread(target=self._get_suggestions_thread, daemon=True).start()

    def _get_suggestions_thread(self):
        self.log("Obteniendo sugerencias...")
        artists = self.artist_list_names
        if not artists:
            messagebox.showwarning("Sin artistas", "Por favor, añade al menos un artista para obtener sugerencias.")
            return
        get_suggestions_from_api(self, artists, self.update_suggestions_ui) 
        self.log("Sugerencias obtenidas y mostradas.")

    def update_suggestions_ui(self, suggestions):
        """Callback function to update the suggestions Listbox."""
        self.track_suggestions = suggestions
        self.suggestions_list_widget.delete(0, tk.END)
        for track in suggestions:
            self.suggestions_list_widget.insert(tk.END, f"{track['name']} - {track['artist']} ({track['album']})")

    def confirm_track(self, event):
        selected_index = self.suggestions_list_widget.curselection()
        if selected_index:
            track = self.track_suggestions[selected_index[0]]
            self.add_track_to_playlist(track)

    def add_track_to_playlist(self, track):
        """Añade un track a la lista confirmada"""
        if track not in self.confirmed_tracks:
            self.confirmed_tracks.append(track)
            self.insert_track_in_treeview(track)
            self.log(f"Canción añadida a la playlist: {track['name']} - {track['artist']}")
        else:
            messagebox.showinfo("Info", "Esta canción ya está en la playlist")

    def insert_track_in_treeview(self, track):
        """Inserta un track en el Treeview de canciones confirmadas"""
        self.tracks_tree.insert('', tk.END, values=(track['name'], track['artist'], track['album']))

    def remove_selected_tracks(self):
        """Elimina los tracks seleccionados de la lista confirmada"""
        selected_items = self.tracks_tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "No hay canciones seleccionadas para quitar.")
            return

        tracks_to_remove = []
        for item in selected_items:
            values = self.tracks_tree.item(item)['values']
            track_name = values[0]
            # Find the track in confirmed_tracks based on name
            for track in list(self.confirmed_tracks): # Iterate over a copy to allow removal
                if track['name'] == track_name:
                    tracks_to_remove.append(track)
                    break

        for track in tracks_to_remove:
            self.confirmed_tracks.remove(track)

        self.refresh_tracks_view()
        self.log(f"Se eliminaron {len(selected_items)} canciones.")

    def refresh_tracks_view(self):
        """Refresca la vista del Treeview de canciones confirmadas."""
        for item in self.tracks_tree.get_children():
            self.tracks_tree.delete(item)
        for track in self.confirmed_tracks:
            self.tracks_tree.insert('', tk.END, values=(track['name'], track['artist'], track['album']))

    def create_playlist(self):
        """Crea la playlist en Spotify con las canciones confirmadas"""
        if not self.confirmed_tracks:
            messagebox.showwarning("Advertencia", "No hay canciones en la playlist para crear.")
            return

        playlist_name = simpledialog.askstring("Nombre de Playlist", "Ingrese el nombre para la nueva playlist:")
        if not playlist_name:
            return

        track_uris = [track['uri'] for track in self.confirmed_tracks]
        threading.Thread(target=self._create_playlist_thread, args=(playlist_name, track_uris), daemon=True).start()

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

    def show_track_context_menu(self, event):
        """Muestra el menú contextual al hacer clic derecho en una sugerencia."""
        try:
            self.track_info_menu.post(event.x_root, event.y_root)
            self.selected_suggestion_index = self.suggestions_list_widget.nearest(event.y)
        except Exception as e:
            self.log(f"Error al mostrar el menú contextual: {e}")

    def _show_track_details(self):
        """Función interna para mostrar los detalles del track seleccionado."""
        if hasattr(self, 'selected_suggestion_index') and 0 <= self.selected_suggestion_index < len(self.track_suggestions):
            selected_track_uri = self.track_suggestions[self.selected_suggestion_index]['uri']
            threading.Thread(target=self.show_track_info, args=(selected_track_uri,), daemon=True).start()
        else:
            messagebox.showwarning("Sin selección", "Por favor, selecciona una canción para ver sus detalles.")

    def show_track_info(self, track_uri):
        """Muestra la información detallada de un track"""
        try:
            if not self.sp:
                messagebox.showerror("Error", "No se ha conectado a Spotify.")
                return

            track = self.sp.track(track_uri)
            self.display_track_details(track)

        except spotipy.exceptions.SpotifyException as e:
            messagebox.showerror("Error de Spotify", f"No se pudo obtener información del track: {e}")
            self.log(f"Error al obtener información del track: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al obtener información del track: {e}")
            self.log(f"Error inesperado al obtener información del track: {e}")

    def display_track_details(self, track):
        """Muestra los detalles del track en el área de texto."""
        self.track_details_text.config(state=tk.NORMAL)
        self.track_details_text.delete(1.0, tk.END)
        self.track_details_text.insert(tk.END, f"Nombre del track: {track['name']}\n")
        self.track_details_text.insert(tk.END, f"Artista: {track['artists'][0]['name']}\n")
        self.track_details_text.insert(tk.END, f"Álbum: {track['album']['name']}\n")
        self.track_details_text.insert(tk.END, f"Duración: {track['duration_ms']} ms\n")
        self.track_details_text.insert(tk.END, f"URL del track: {track['external_urls']['spotify']}\n")
        self.track_details_text.config(state=tk.DISABLED)