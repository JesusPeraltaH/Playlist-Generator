import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import spotipy
from spotipy.oauth2 import SpotifyOAuth

class MusicRecommender:
    def __init__(self, sp):
        self.sp = sp
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=5, random_state=42)
        
    def get_audio_features(self, track_uris):
        """Obtiene las características de audio para una lista de tracks."""
        features = []
        print(f"Intentando obtener características para {len(track_uris)} canciones...")
        
        # Verificar que las URIs son válidas
        valid_uris = []
        for uri in track_uris:
            if ':' in uri:
                track_id = uri.split(':')[-1]
                valid_uris.append(track_id)
            else:
                print(f"URI inválida: {uri}")
        
        if not valid_uris:
            print("No hay URIs válidas para procesar")
            return []
            
        print(f"URIs válidas encontradas: {len(valid_uris)}")
        
        # Procesar en lotes de 100 (límite de Spotify)
        for i in range(0, len(valid_uris), 100):
            batch = valid_uris[i:i + 100]
            try:
                print(f"Obteniendo características para lote de {len(batch)} canciones...")
                audio_features = self.sp.audio_features(batch)
                if audio_features:
                    features.extend([f for f in audio_features if f is not None])
                    print(f"Características obtenidas para {len(audio_features)} canciones en este lote")
                else:
                    print("No se obtuvieron características para este lote")
            except Exception as e:
                print(f"Error al obtener características de audio para el lote: {str(e)}")
                continue
        
        print(f"Total de características obtenidas: {len(features)}")
        return features

    def prepare_features(self, features):
        """Prepara las características para el modelo."""
        # Seleccionar características relevantes
        feature_keys = ['danceability', 'energy', 'valence', 'tempo', 
                       'instrumentalness', 'acousticness', 'loudness', 'mode']
        
        # Convertir a array numpy
        X = np.array([[f[k] for k in feature_keys] for f in features if f is not None])
        
        # Escalar características
        X_scaled = self.scaler.fit_transform(X)
        return X_scaled

    def get_similar_songs(self, track_uris, limit=20):
        """Obtiene canciones similares basadas en las características de audio."""
        try:
            # Extraer IDs de las URIs
            track_ids = []
            for uri in track_uris:
                if ':' in uri:
                    track_id = uri.split(':')[-1]
                    track_ids.append(track_id)
                else:
                    track_ids.append(uri)
            
            print(f"Obteniendo características de audio para {len(track_ids)} canciones...")
            # Obtener características de audio de las canciones de referencia
            features = self.get_audio_features(track_ids)
            if not features:
                print("No se pudieron obtener características de audio.")
                # Intentar obtener recomendaciones sin características específicas
                print("Intentando obtener recomendaciones sin características específicas...")
                recommendations = self.sp.recommendations(
                    seed_tracks=track_ids[:5],
                    limit=limit
                )
                if recommendations and 'tracks' in recommendations:
                    print(f"Se obtuvieron {len(recommendations['tracks'])} recomendaciones sin características específicas.")
                    return recommendations['tracks']
                return []

            print(f"Características obtenidas para {len(features)} canciones.")
            # Calcular características promedio
            avg_features = {
                'danceability': np.mean([f['danceability'] for f in features]),
                'energy': np.mean([f['energy'] for f in features]),
                'valence': np.mean([f['valence'] for f in features]),
                'tempo': np.mean([f['tempo'] for f in features]),
                'instrumentalness': np.mean([f['instrumentalness'] for f in features]),
                'acousticness': np.mean([f['acousticness'] for f in features]),
                'loudness': np.mean([f['loudness'] for f in features])
            }

            print("Obteniendo recomendaciones de Spotify...")
            # Obtener recomendaciones de Spotify
            seed_tracks = track_ids[:5]  # Usar hasta 5 tracks como semilla
            print(f"Usando {len(seed_tracks)} canciones como semilla.")
            
            recommendations = self.sp.recommendations(
                seed_tracks=seed_tracks,
                limit=limit,
                target_danceability=avg_features['danceability'],
                target_energy=avg_features['energy'],
                target_valence=avg_features['valence'],
                target_tempo=avg_features['tempo'],
                target_instrumentalness=avg_features['instrumentalness'],
                target_acousticness=avg_features['acousticness'],
                target_loudness=avg_features['loudness']
            )
            
            if not recommendations or 'tracks' not in recommendations:
                print("No se obtuvieron recomendaciones de Spotify.")
                return []
                
            print(f"Se obtuvieron {len(recommendations['tracks'])} recomendaciones.")
            return recommendations['tracks']
            
        except Exception as e:
            print(f"Error al obtener canciones similares: {str(e)}")
            raise  # Re-lanzar la excepción para que pueda ser manejada por el GUI

    def get_track_preview_url(self, track_uri):
        """Obtiene la URL de vista previa de una canción."""
        try:
            track_id = track_uri.split(':')[-1]
            track = self.sp.track(track_id)
            return track.get('preview_url')
        except Exception as e:
            print(f"Error al obtener URL de vista previa: {e}")
            return None 