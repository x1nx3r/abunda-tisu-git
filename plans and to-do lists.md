<h1>To-Dos</h1>

* To integrate and make functions of playlist

    async def create_playlist(self, *, name: str) -> Playlist: Creates a new playlist with the given name.

    async def delete_playlist(self, *, playlist: Playlist) -> None: Deletes a playlist.

    async def get_playlists(self) -> List[Playlist]: Returns a list of all the playlists in the connected node.

    async def add_tracks(self, *, playlist: Playlist, tracks: List[Track], requester: Optional[Union[discord.User, discord.Member]] = None) -> None: Adds tracks to the given playlist.

    async def remove_tracks(self, *, playlist: Playlist, tracks: List[Track]) -> None: Removes tracks from the given playlist.

    async def get_tracks(self, *, playlist: Playlist) -> List[Track]: Returns a list of tracks in the given playlist.

    async def shuffle(self, *, playlist: Playlist) -> None: Shuffles the tracks in the given playlist.

    async def clear(self, *, playlist: Playlist) -> None: Removes all tracks from the given playlist.

    async def rename(self, *, playlist: Playlist, new_name: str) -> None: Renames the given playlist.

    async def load_playlist(self, *, playlist: Playlist, requester: Optional[Union[discord.User, discord.Member]] = None) -> None: Loads and plays the given playlist.