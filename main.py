import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv, find_dotenv
import sys
import random
from tkinter import simpledialog
import webbrowser
import time

class SpotifyPlaylistCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("Spotify Playlist Creator con IA")
        self.root.geometry("800x600")
        self.root.configure(bg="#191414")  # Color de fondo de Spotify
        
        # Configurar estilo
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('TFrame', background="#191414")
        self.style.configure('TButton', background="#1DB954", foreground="black", font=('Helvetica', 10, 'bold'))
        self.style.configure('TLabel', background="#191414", foreground="white", font=('Helvetica', 11))
        self.style.configure('Header.TLabel', background="#191414", foreground="#1DB954", font=('Helvetica', 16, 'bold'))
        
        # Variables
        self.sp = None
        self.artist_list = []
        self.track_suggestions = []
        self.selected_tracks = []
        self.auth_manager = None
        
        # Crear interfaz
        self.create_widgets()
        
        # Configurar entorno
        self.setup_environment()
    
    def create_widgets(self):
        """Crear todos los widgets de la interfaz"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="Spotify Playlist Creator con IA", style='Header.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Panel izquierdo (entrada)
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

          # Nuevo panel para canciones individuales
        songs_frame = ttk.Frame(left_frame)
        songs_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(songs_frame, text="Canciones individuales:").pack(anchor=tk.W)
    
        song_input_frame = ttk.Frame(songs_frame)
        song_input_frame.pack(fill=tk.X, pady=5)
        
        self.song_entry = ttk.Entry(song_input_frame, width=30)
        self.song_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.song_entry.bind('<Return>', lambda e: self.add_song())
        
        ttk.Button(song_input_frame, text="Añadir", command=self.add_song).pack(side=tk.LEFT)

         # Nuevo panel para géneros
        genre_frame = ttk.Frame(left_frame)
        genre_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(genre_frame, text="Géneros musicales:").pack(anchor=tk.W)
        
        genre_input_frame = ttk.Frame(genre_frame)
        genre_input_frame.pack(fill=tk.X, pady=5)
        
        self.genre_combobox = ttk.Combobox(genre_input_frame, values=[
            "rock", "pop", "jazz", "electronic", "hiphop", "classical", "reggae", "metal"
        ], width=28)
        self.genre_combobox.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(genre_input_frame, text="Añadir", command=self.add_genre).pack(side=tk.LEFT)
        
        # Lista de géneros
        self.genre_list = []
        ttk.Label(genre_frame, text="Géneros seleccionados:").pack(anchor=tk.W, pady=(10, 5))
        
        self.genre_listbox = tk.Listbox(genre_frame, bg="#282828", fg="white", height=3)
        self.genre_listbox.pack(fill=tk.X)
        
        # Modificar frame de botones de sugerencias
        artists_button_frame = ttk.Frame(artists_frame)
        artists_button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(artists_button_frame, text="Eliminar seleccionado", command=self.remove_artist).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(artists_button_frame, text="Buscar sugerencias", command=self.get_suggestions).pack(side=tk.LEFT)
    
        
        # Panel para la playlist
        playlist_frame = ttk.Frame(left_frame)
        playlist_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(playlist_frame, text="Nombre de la playlist:").pack(side=tk.LEFT)
        self.playlist_name = tk.StringVar()
        ttk.Entry(playlist_frame, textvariable=self.playlist_name, width=30).pack(side=tk.LEFT, padx=5)
        
           # Panel para artistas
        artists_frame = ttk.Frame(left_frame)
        artists_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(artists_frame, text="Artistas (añade los que te gusten):").pack(anchor=tk.W)
        
        # Entrada de artista
        artist_input_frame = ttk.Frame(artists_frame)
        artist_input_frame.pack(fill=tk.X, pady=5)
        
        self.artist_entry = ttk.Entry(artist_input_frame, width=30)
        self.artist_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.artist_entry.bind('<Return>', lambda e: self.add_artist())
        
        ttk.Button(artist_input_frame, text="Añadir", command=self.add_artist).pack(side=tk.LEFT)
        
        # Lista de artistas
        ttk.Label(artists_frame, text="Artistas seleccionados:").pack(anchor=tk.W, pady=(10, 5))
        
        artists_list_frame = ttk.Frame(artists_frame)
        artists_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.artists_listbox = tk.Listbox(artists_list_frame, bg="#282828", fg="white", selectbackground="#1DB954")
        self.artists_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        artists_scrollbar = ttk.Scrollbar(artists_list_frame, orient=tk.VERTICAL, command=self.artists_listbox.yview)
        artists_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.artists_listbox.config(yscrollcommand=artists_scrollbar.set)
        
        # Mover la definición de artists_button_frame aquí
        artists_button_frame = ttk.Frame(artists_frame)
        artists_button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(artists_button_frame, text="Eliminar seleccionado", command=self.remove_artist).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(artists_button_frame, text="Buscar sugerencias", command=self.get_suggestions).pack(side=tk.LEFT)


        # Panel derecho (sugerencias y creación)
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        ttk.Label(right_frame, text="Canciones sugeridas por IA:").pack(anchor=tk.W)
        buttons_frame = ttk.Frame(right_frame)

        buttons_frame.pack(fill=tk.X)

        ttk.Button(buttons_frame, text="Seleccionar todo", command=self.select_all_suggestions).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Eliminar seleccionado", command=self.remove_selected_suggestions).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Crear playlist", command=self.create_playlist).pack(side=tk.LEFT)
        
        # Lista de sugerencias
        suggestions_frame = ttk.Frame(right_frame)
        suggestions_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        self.suggestions_listbox = tk.Listbox(suggestions_frame, bg="#282828", fg="white", selectbackground="#1DB954", selectmode=tk.MULTIPLE)
        self.suggestions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        suggestions_scrollbar = ttk.Scrollbar(suggestions_frame, orient=tk.VERTICAL, command=self.suggestions_listbox.yview)
        suggestions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.suggestions_listbox.config(yscrollcommand=suggestions_scrollbar.set)
        
        # Botones finales
        buttons_frame = ttk.Frame(right_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(buttons_frame, text="Seleccionar todo", command=self.select_all_suggestions).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Crear playlist", command=self.create_playlist).pack(side=tk.LEFT)
        
        # Botón de reconexión
        ttk.Button(buttons_frame, text="Renovar conexión", command=self.reconnect_spotify).pack(side=tk.RIGHT)
        
        # Log
        ttk.Label(main_frame, text="Estado:").pack(anchor=tk.W, pady=(10, 5))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=5, bg="#282828", fg="white")
        self.log_text.pack(fill=tk.X)
        self.log_text.config(state=tk.DISABLED)
        
        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_var.set("Esperando configuración...")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def log(self, message):
        """Añadir mensaje al log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def setup_environment(self):
        """Configurar el entorno y conectar con Spotify"""
        self.status_var.set("Configurando entorno...")
        
        # Buscar archivo .env
        env_file = find_dotenv()
        
        if not env_file:
            self.log("Archivo .env no encontrado. Creando uno nuevo...")
            
            # Crear archivo .env
            with open(".env", "w") as f:
                f.write("# Credenciales de Spotify\n")
                f.write("SPOTIFY_CLIENT_ID=\n")
                f.write("SPOTIFY_CLIENT_SECRET=\n")
                f.write("SPOTIFY_REDIRECT_URI=http://localhost:8888/callback/\n")
            
            self.log("Por favor, edita el archivo .env con tus credenciales de Spotify y reinicia la aplicación.")
            messagebox.showinfo("Configuración necesaria", 
                               "Se ha creado un archivo .env.\n\n"
                               "Por favor, edita este archivo y añade tus credenciales de Spotify:\n"
                               "1. SPOTIFY_CLIENT_ID\n"
                               "2. SPOTIFY_CLIENT_SECRET\n"
                               "3. SPOTIFY_REDIRECT_URI (mantén el valor predeterminado)\n\n"
                               "Después, reinicia esta aplicación.")
            return
        
        # Cargar variables
        load_dotenv(env_file)
        
        # Verificar credenciales
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')
        
        if not client_id or not client_secret or not redirect_uri:
            self.log("Error: Faltan credenciales en el archivo .env")
            messagebox.showerror("Error de configuración", 
                                "Faltan credenciales en el archivo .env.\n"
                                "Por favor, asegúrate de completar todos los campos.")
            return
        
        # Conectar con Spotify en un hilo separado
        threading.Thread(target=self.connect_to_spotify, args=(client_id, client_secret, redirect_uri), daemon=True).start()
    
    def reconnect_spotify(self):
        """Renovar la conexión con Spotify"""
        if not self.auth_manager:
            self.log("No hay una conexión previa para renovar. Configurando nuevo entorno...")
            self.setup_environment()
            return
            
        self.log("Renovando conexión con Spotify...")
        threading.Thread(target=self.connect_to_spotify_with_auth, daemon=True).start()
    
    def connect_to_spotify_with_auth(self):
        """Reconectar utilizando el auth_manager existente"""
        try:
            self.status_var.set("Renovando conexión...")
            
            # Crear nueva instancia con el auth_manager existente
            self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
            
            # Verificar conexión
            user = self.sp.current_user()
            self.status_var.set(f"Reconectado como: {user['display_name']}")
            self.log(f"¡Conexión renovada! Usuario: {user['display_name']}")
            
        except Exception as e:
            self.log(f"Error al renovar conexión: {str(e)}")
            self.status_var.set("Error de reconexión")
            messagebox.showerror("Error de reconexión", 
                               f"No se pudo renovar la conexión: {str(e)}\n\n"
                               "Intenta reiniciar la aplicación.")
    
    def connect_to_spotify(self, client_id, client_secret, redirect_uri):
        """Conectar con la API de Spotify"""
        try:
            self.status_var.set("Conectando con Spotify...")
            self.log("Conectando con tu cuenta de Spotify...")
            
            # Crear el auth_manager
            self.auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope="playlist-modify-public user-library-read user-top-read",
                open_browser=True,
                cache_path=".spotify_cache"
            )
            
            # Obtener token (esto abrirá el navegador si es necesario)
            token_info = self.auth_manager.get_access_token(as_dict=True)
            
            if not token_info:
                self.log("No se pudo obtener el token de acceso. Verifica tus credenciales.")
                self.status_var.set("Error de autenticación")
                return
            
            # Crear cliente de Spotify
            self.sp = spotipy.Spotify(auth_manager=self.auth_manager)
            
            # Verificar conexión
            user = self.sp.current_user()
            self.status_var.set(f"Conectado como: {user['display_name']}")
            self.log(f"¡Conexión exitosa! Bienvenido, {user['display_name']}")
            
        except Exception as e:
            self.status_var.set("Error de conexión")
            self.log(f"Error al conectar con Spotify: {str(e)}")
            messagebox.showerror("Error de conexión", 
                               f"No se pudo conectar con Spotify: {str(e)}\n\n"
                               "Verifica tus credenciales y que la URL de redirección sea correcta.")
    
    def add_artist(self):
        """Añadir un artista a la lista"""
        artist_name = self.artist_entry.get().strip()
        
        if not artist_name:
            return
        
        if not self.sp:
            messagebox.showwarning("No conectado", "Aún no se ha establecido conexión con Spotify.")
            return
        
        self.status_var.set("Buscando artista...")
        
        try:
            # Verificar que el artista existe
            results = self.sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
            
            if not results['artists']['items']:
                messagebox.showwarning("Artista no encontrado", f"No se encontró al artista: {artist_name}")
                return
            
            # Obtener nombre exacto del artista
            artist_data = results['artists']['items'][0]
            exact_name = artist_data['name']
            
            # Añadir a la lista si no está ya
            if exact_name not in self.artist_list:
                self.artist_list.append(exact_name)
                self.artists_listbox.insert(tk.END, exact_name)
                self.log(f"Artista añadido: {exact_name}")
            
            # Limpiar entrada
            self.artist_entry.delete(0, tk.END)
            
        except Exception as e:
            self.log(f"Error al buscar artista: {str(e)}")
            if "token" in str(e).lower():
                self.log("El token parece haber expirado. Intenta usar 'Renovar conexión'.")
            messagebox.showerror("Error", f"Error al buscar artista: {str(e)}")
        
        finally:
            self.status_var.set("Listo")
    
    def remove_artist(self):
        """Eliminar el artista seleccionado"""
        selection = self.artists_listbox.curselection()
        
        if not selection:
            return
        
        index = selection[0]
        artist = self.artist_list[index]
        
        # Eliminar de la lista
        self.artist_list.pop(index)
        self.artists_listbox.delete(index)
        
        self.log(f"Artista eliminado: {artist}")
    
    def get_suggestions(self):
        """Obtener sugerencias de canciones basadas en los artistas"""
        if not self.sp:
            messagebox.showwarning("No conectado", "Aún no se ha establecido conexión con Spotify.")
            return
        
        if not self.artist_list:
            messagebox.showwarning("Sin artistas", "Añade al menos un artista para obtener sugerencias.")
            return
        
        # Iniciar búsqueda en un hilo separado
        threading.Thread(target=self._get_suggestions_thread, daemon=True).start()
    
    def _get_artist_id(self, artist_name):
        """Obtener el ID de un artista de forma segura"""
        try:
            results = self.sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
            if results['artists']['items']:
                return results['artists']['items'][0]['id']
        except Exception as e:
            self.log(f"Error al buscar ID para {artist_name}: {str(e)}")
        return None
    
    def _get_suggestions_thread(self):
        """Proceso de búsqueda de sugerencias en segundo plano"""
        self.status_var.set("Generando sugerencias con IA...")
        self.log("Buscando sugerencias de canciones...")
        
        # Limpiar sugerencias anteriores
        self.track_suggestions = []
        self.suggestions_listbox.delete(0, tk.END)
        
        try:
            # 1. Búsqueda de canciones populares de cada artista
            top_tracks = []
            
            for artist in self.artist_list:
                self.log(f"Analizando música de {artist}...")
                artist_id = self._get_artist_id(artist)
                
                if artist_id:
                    try:
                        tracks = self.sp.artist_top_tracks(artist_id)
                        top_tracks.extend(tracks['tracks'][:3])  # Tomar las 3 más populares
                    except Exception as e:
                        self.log(f"Error al obtener canciones de {artist}: {str(e)}")
            
            # 2. Búsqueda de artistas relacionados (con manejo de errores mejorado)
            related_artists = set()
            for artist in self.artist_list:
                artist_id = self._get_artist_id(artist)
                
                if artist_id:
                    try:
                        related = self.sp.artist_related_artists(artist_id)
                        
                        # Tomar hasta 2 artistas relacionados
                        for rel_artist in related['artists'][:2]:
                            related_artists.add(rel_artist['id'])
                    except Exception as e:
                        self.log(f"No se pudieron encontrar artistas relacionados para {artist}: {str(e)}")
                        # Continuar con el siguiente artista
            
            # Obtener canciones de artistas relacionados
            for artist_id in related_artists:
                try:
                    tracks = self.sp.artist_top_tracks(artist_id)
                    top_tracks.extend(tracks['tracks'][:2])  # 2 canciones por artista relacionado
                except Exception as e:
                    self.log(f"Error al obtener canciones de un artista relacionado: {str(e)}")
            
            # 3. Usar el algoritmo de recomendaciones de Spotify
            if top_tracks:
                # Tomar solo IDs válidos
                valid_track_ids = [t['id'] for t in top_tracks if 'id' in t]
                
                if valid_track_ids:
                    # Limitar a máximo 5 seeds
                    seed_tracks = random.sample(valid_track_ids, min(5, len(valid_track_ids)))
                    
                    try:
                        recommendations = self.sp.recommendations(seed_tracks=seed_tracks, limit=10)
                        top_tracks.extend(recommendations['tracks'])
                    except Exception as e:
                        self.log(f"Error al obtener recomendaciones: {str(e)}")
            
            # Filtrar duplicados y añadir a sugerencias
            track_ids = set()
            for track in top_tracks:
                if 'id' not in track:
                    continue
                    
                track_id = track['id']
                if track_id not in track_ids:
                    track_ids.add(track_id)
                    
                    # Artistas del track
                    artists = ", ".join([a['name'] for a in track['artists']])
                    
                    # Info de la canción
                    track_info = {
                        'id': track['id'],
                        'name': track['name'],
                        'artists': artists,
                        'uri': track['uri']
                    }
                    
                    # Añadir a la lista
                    self.track_suggestions.append(track_info)
                    
                    # Mostrar en la interfaz
                    display_text = f"{track['name']} - {artists}"
                    self.suggestions_listbox.insert(tk.END, display_text)
            
            self.log(f"Se encontraron {len(self.track_suggestions)} sugerencias.")
            self.status_var.set(f"{len(self.track_suggestions)} sugerencias encontradas")
            
        except Exception as e:
            self.log(f"Error al buscar sugerencias: {str(e)}")
            if "token" in str(e).lower():
                self.log("El token parece haber expirado. Intenta usar 'Renovar conexión'.")
            messagebox.showerror("Error", f"Error al buscar sugerencias: {str(e)}")
            self.status_var.set("Error en sugerencias")
    
    def select_all_suggestions(self):
        """Seleccionar todas las sugerencias"""
        self.suggestions_listbox.selection_set(0, tk.END)
    
    def create_playlist(self):
        """Crear la playlist con las canciones seleccionadas"""
        if not self.sp:
            messagebox.showwarning("No conectado", "Aún no se ha establecido conexión con Spotify.")
            return
        
        # Verificar nombre de playlist
        playlist_name = self.playlist_name.get().strip()
        if not playlist_name:
            playlist_name = simpledialog.askstring("Nombre de playlist", "Ingresa un nombre para tu playlist:")
            if not playlist_name:
                return
            self.playlist_name.set(playlist_name)
        
        # Obtener selecciones
        selected = self.suggestions_listbox.curselection()
        if not selected:
            messagebox.showwarning("Sin selección", "Selecciona al menos una canción para añadir a la playlist.")
            return
        
        # Obtener URIs de canciones seleccionadas
        track_uris = [self.track_suggestions[idx]['uri'] for idx in selected]
        
        # Iniciar creación en un hilo separado
        threading.Thread(target=self._create_playlist_thread, args=(playlist_name, track_uris), daemon=True).start()
    
    def _create_playlist_thread(self, playlist_name, track_uris):
        """Proceso de creación de playlist en segundo plano"""
        self.status_var.set("Creando playlist...")
        self.log(f"Creando playlist: {playlist_name}")
        
        try:
            # Crear playlist vacía
            user_id = self.sp.me()['id']
            
            artists_text = ", ".join(self.artist_list[:3])
            if len(self.artist_list) > 3:
                artists_text += f" y {len(self.artist_list) - 3} más"
                
            description = f"Playlist de {artists_text} creada con IA"
            
            playlist = self.sp.user_playlist_create(
                user=user_id,
                name=playlist_name,
                public=True,
                description=description
            )
            
            playlist_id = playlist['id']
            
            # Añadir canciones (máximo 100 a la vez)
            for i in range(0, len(track_uris), 100):
                batch = track_uris[i:i+100]
                self.sp.playlist_add_items(playlist_id, batch)
            
            # Obtener enlace
            playlist_url = playlist['external_urls']['spotify']
            
            self.log(f"¡Playlist creada con éxito!")
            self.log(f"Enlace: {playlist_url}")
            self.status_var.set("Playlist creada")
            
            # Abrir enlace automáticamente
            open_url = messagebox.askyesno("Playlist creada", 
                               f"¡Tu playlist '{playlist_name}' ha sido creada!\n\n"
                               f"Se han añadido {len(track_uris)} canciones.\n\n"
                               f"¿Deseas abrir la playlist en tu navegador?")
            
            if open_url:
                webbrowser.open(playlist_url)
            
        except Exception as e:
            self.log(f"Error al crear playlist: {str(e)}")
            if "token" in str(e).lower():
                self.log("El token parece haber expirado. Intenta usar 'Renovar conexión'.")
            messagebox.showerror("Error", f"Error al crear playlist: {str(e)}")
            self.status_var.set("Error en playlist")

    def add_song(self):
   
        song_name = self.song_entry.get().strip()
    
        if not song_name:
            return
            
        try:
            results = self.sp.search(q=f'track:{song_name}', type='track', limit=1)
            if not results['tracks']['items']:
                messagebox.showwarning("Canción no encontrada", f"No se encontró: {song_name}")
                return
                
            track = results['tracks']['items'][0]
            track_info = f"{track['name']} - {track['artists'][0]['name']}"
            
            if track_info not in self.track_suggestions:
                self.track_suggestions.append(track['uri'])
                self.suggestions_listbox.insert(tk.END, track_info)
                self.log(f"Canción añadida: {track_info}")
                
            self.song_entry.delete(0, tk.END)
            
        except Exception as e:
            self.log(f"Error al buscar canción: {str(e)}")

    def add_genre(self):
            """Añadir un género a la lista"""
            genre = self.genre_combobox.get().strip().lower()
            
            if not genre:
                return
                
            if genre not in self.genre_list and genre in self.genre_combobox['values']:
                self.genre_list.append(genre)
                self.genre_listbox.insert(tk.END, genre.capitalize())
                self.log(f"Género añadido: {genre}")

    def remove_selected_suggestions(self):
    
        selections = self.suggestions_listbox.curselection()
        
        if not selections:
            return
            
        # Eliminar en orden inverso para mantener los índices correctos
        for index in reversed(selections):
            self.suggestions_listbox.delete(index)
            del self.track_suggestions[index]
        
        self.log(f"Eliminadas {len(selections)} canciones de las sugerencias")

def main():
    # Crear ventana principal
    root = tk.Tk()
    app = SpotifyPlaylistCreator(root)
    
    # Iniciar bucle de eventos
    root.mainloop()

if __name__ == "__main__":
    main()