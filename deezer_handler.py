import deezer
import requests
import time
import deezpy


def download_file(url, name):
    orig = requests.get(url)
    with open(name, 'wb') as copy:
        copy.write(orig.content)


class Session:
    # [deezer_object]_parameters
    artist_params = {
        'name'
    }
    album_params = {
        'title',
        'artist'
    }
    track_params = {
        'title',
        'release_date',
        'artist',
        'album'
    }
    playlist_params = {
        'title'
    }
    # [object]_options
    artist_opts = {
        'link',
        'tracklist'
    }
    album_opts = {
        'tracks',
        'link',
        'tracklist',
        'artist'
    }
    track_opts = {
        'link',
        'preview',
        'artist',
        'album'
    }
    playlist_opts = {
        'tracks',
        'link'
    }

    def __init__(self):
        self.full_cool_down_time = time.clock()
        self.requests_session = requests.Session()
        self.track_info = {}
        self.album_info = {}
        self.artist_info = {}
        self.playlist_info = {}
        with open('deezer_app.txt', 'r') as f:
            app_id, app_secret = f.read().split('\n')
        self.client = deezer.Client(app_id=app_id, app_secret=app_secret)
        self.chart_id = {}
        with open('charts.txt', 'r') as f:
            output = f.read()
            lines = output.split('\n')
            for line in lines:
                c_name, c_id = line.split()
                self.chart_id[c_name] = c_id

    def charts(self):
        return self.chart_id.keys()

    def get_options(self, deezer_obj):
        if type(deezer_obj) == deezer.Artist:
            self.update_artist(deezer_obj.id)
            return set(self.artist_info[deezer_obj.id].__dict__['_fields']) & self.artist_opts
        elif type(deezer_obj) == deezer.Album:
            self.update_album(deezer_obj.id)
            return set(self.album_info[deezer_obj.id].__dict__['_fields']) & self.album_opts
        elif type(deezer_obj) == deezer.Track:
            self.update_track(deezer_obj.id)
            res = set(self.track_info[deezer_obj.id].__dict__['_fields']) & self.track_opts
            res.add('download')
            return res
        elif type(deezer_obj) == deezer.Playlist:
            self.update_playlist(deezer_obj.id)
            return set(self.playlist_info[deezer_obj.id].__dict__['_fields']) & self.playlist_opts
        else:
            return []

    def get_parameter_list(self, deezer_obj):
        self.update_object(deezer_obj)
        if type(deezer_obj) == deezer.Artist:
            return set(self.artist_info[deezer_obj.id].__dict__['_fields']) & self.artist_params
        elif type(deezer_obj) == deezer.Album:
            return set(self.album_info[deezer_obj.id].__dict__['_fields']) & self.album_params
        elif type(deezer_obj) == deezer.Track:
            return set(self.track_info[deezer_obj.id].__dict__['_fields']) & self.track_params
        elif type(deezer_obj) == deezer.Playlist:
            return set(self.playlist_info[deezer_obj.id].__dict__['_fields']) & self.playlist_params
        else:
            return []

    def get_parameter(self, deezer_obj, param):
        deezer_obj = self.update_object(deezer_obj)
        res = deezer_obj.__getattribute__(param)
        if isinstance(res, str):
            return res
        res = self.update_object(res)
        if isinstance(res, deezer.Album):
            return res.title
        if isinstance(res, deezer.Artist):
            return res.name
        if isinstance(res, deezer.Track):
            return self.track_name(res)[0]
        if isinstance(res, deezer.Playlist):
            return res.title

    def exec_option(self, deezer_obj, opt):
        if type(deezer_obj) in [
            deezer.Artist,
            deezer.Album,
            deezer.Track,
            deezer.Playlist,
            list
        ]:
            deezer_obj = self.update_object(deezer_obj)
            if opt not in self.get_options(deezer_obj):
                return {
                    'text': 'No such option',
                    'context': deezer_obj
                }
            atr = deezer_obj.__getattribute__(opt)
            if type(atr) == deezer.Artist:
                self.update_artist(atr.id)
                return {
                    'text': atr.name,
                    'context': atr
                }
            elif type(atr) == deezer.Album:
                self.update_album(atr.id)
                return {
                    'text': atr.title,
                    'context': atr
                }
            elif type(atr) == deezer.Track:
                self.update_track(atr.id)
                return {
                    'text': self.track_name(atr)[0],
                    'context': atr
                }
            elif type(atr) == deezer.Playlist:
                self.update_playlist(atr.id)
                return {
                    'text': atr.title,
                    'context': atr
                }
            elif type(atr) == list:
                return {
                    'text': 'Tracklist',
                    'context': atr
                }
            else:
                return {
                    'text': atr,
                    'context': deezer_obj
                }

    def track_name(self, track):
        if type(track) == deezer.Track:
            track = [track]
        res = []
        for t in track:
            self.update_track(t.id)
            res.append('{} - {}'.format(self.track_info[t.id].artist.name,
                                        self.track_info[t.id].title))
        return res

    def send_preview(self, bot, user_id, track):
        nm = 'tracks/{}.mp3'.format(self.track_name(track))
        download_file(track.preview, nm)
        file = open(nm, 'rb')
        bot.send_audio(user_id, file)
        file.close()

    def tracks_from_playlist(self, playlist_id, limit=10):
        tracks = self.client.get_playlist(playlist_id).tracks
        return tracks[:min(limit, len(tracks))]

    def chart_tracks(self, region='Worldwide', limit=10):
        if region not in self.chart_id.keys():
            return ["I don't know this region"]
        ids = self.tracks_from_playlist(self.chart_id[region], limit=limit)
        return ids

    # search
    def exec_search(self, s):
        return self.client.search(s)

    # updates of content
    def update_artist(self, artist_id):
        if artist_id not in self.artist_info.keys():
            self.artist_info[artist_id] = self.client.get_artist(artist_id)
        return self.artist_info[artist_id]

    def update_album(self, album_id):
        if album_id not in self.album_info.keys():
            self.album_info[album_id] = self.client.get_album(album_id)
        return self.album_info[album_id]

    def update_track(self, track_id):
        if track_id not in self.track_info.keys():
            self.track_info[track_id] = self.client.get_track(track_id)
        return self.track_info[track_id]

    def update_playlist(self, playlist_id):
        if playlist_id not in self.playlist_info.keys():
            self.playlist_info[playlist_id] = self.client.get_playlist(playlist_id)
        return self.playlist_info[playlist_id]

    def update_object(self, deezer_object):
        if type(deezer_object) == deezer.Artist:
            return self.update_artist(deezer_object.id)
        elif type(deezer_object) == deezer.Album:
            return self.update_album(deezer_object.id)
        elif type(deezer_object) == deezer.Playlist:
            return self.update_playlist(deezer_object.id)
        elif type(deezer_object) == deezer.Track:
            return self.update_track(deezer_object.id)
        else:
            return None

    def download(self, track_id):
        self.update_track(track_id)
        track = self.track_info[track_id]
        fname = self.track_name(track)[0]
        deezpy.downloadDeezer(track.link, 'tracks/{}'.format(fname))
        return 'tracks/{}.mp3'.format(fname)
