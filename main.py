import tkinter as tk
from gui import SpotifyPlaylistCreator

def main():
    root = tk.Tk()
    app = SpotifyPlaylistCreator(root)
    root.mainloop()

if __name__ == "__main__":
    main()