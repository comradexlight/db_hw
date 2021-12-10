import requests
import sqlalchemy


def auth():
    url_aut = 'https://www.discogs.com/oauth/authorize'
    headers = {
        'Content-Type': 'application/hw4_for_psql',
        'Authorization':
            'OAuth oauth_consumer_key="my_consumer_key ", \
            oauth_nonce="timestamp",\
            oauth_signature="my_secret_key&",\
            oauth_signature_method="PLAINTEXT", \
            oauth_timestamp="current_timestamp", \
            oauth_callback="json"',
        'User-Agent': 'hw4_for_psql'
    }
    requests.get(url=url_aut, headers=headers)


def search_id(table_name, row_name, name):
    db = 'postgresql://postgres:124709@localhost:5432/music_db'
    engine = sqlalchemy.create_engine(db)
    connection = engine.connect()
    result = connection.execute(f"SELECT id FROM {table_name} WHERE {row_name} = '{name}';")
    for row in result:
        return row['id']


def upload(artist_id_from_discogs):
    db = 'postgresql://postgres:124709@localhost:5432/music_db'
    engine = sqlalchemy.create_engine(db)
    connection = engine.connect()
    url = f'https://api.discogs.com/artists/{artist_id_from_discogs}/releases'
    headers = {
        'Content-Type': 'application/hw4_for_psql',
        'Authorization':
            'OAuth oauth_consumer_key="my_consumer_key ", \
            oauth_nonce="timestamp",\
            oauth_signature="my_secret_key&",\
            oauth_signature_method="PLAINTEXT", \
            oauth_timestamp="current_timestamp", \
            oauth_callback="json"',
        'User-Agent': 'hw4_for_psql'
    }
    artist = (requests.get(url=url, headers=headers, timeout=None)).json()
    artist_name = artist['releases'][0]['artist'].split('(')[0].rstrip(' ')
    genres_list = []
    albums = []
    a_count = 0
    va_count = 0
    v_as = []
    for i in artist['releases']:
        if i['type'] == 'master' and i['artist'] == artist['releases'][0]['artist']:
            albums.append([i['title'].replace("'", ""), i['year']])
            release = requests.get(url=i['resource_url'], headers=headers, timeout=None)
            genres_list += release.json()['styles']
            tracklist = []
            for tr in release.json()['tracklist']:
                if tr['duration']:
                    tracklist.append([tr['title'].replace("'", ""), sum(
                        int(i) * 60 ** index for index, i in enumerate(tr['duration'].split(":")[::-1]))])
                else:
                    tracklist.append([tr['title'].replace("'", ""), 0])
            albums[a_count].append(tracklist)
            a_count += 1
        elif i['type'] == 'master' and i['artist'] == 'Various':
            v_as.append([i['title'].replace("'", ""), i['year']])
            release = requests.get(url=i['resource_url'], headers=headers, timeout=None)
            va_tracklist = []
            for tr in release.json()['tracklist']:
                if tr['duration']:
                    va_tracklist.append([tr['title'].replace("'", ""), sum(
                        int(i) * 60 ** index for index, i in enumerate(tr['duration'].split(":")[::-1]))])
                else:
                    va_tracklist.append([tr['title'].replace("'", ""), 0])
            v_as[va_count].append(va_tracklist)
            va_count += 1

    genre = max(set(genres_list), key=genres_list.count)
    connection.execute(f"INSERT INTO artists(name) VALUES('{artist_name}');")
    print(f'Добавлен исполнитель {artist_name}')
    artist_id = search_id('artists', 'name', artist_name)
    genre_id = search_id('genres', 'genre_name', genre)
    if genre_id is None:
        connection.execute(f"INSERT INTO genres(genre_name) VALUES('{genre}');")
        print(f'Добавлен жанр {genre}')
        genre_id = search_id('genres', 'genre_name', genre)
    for album in albums:
        connection.execute(f"INSERT INTO albums(album_title, release_date) VALUES('{album[0]}', {album[1]});")
        print(f'Добавлен альбом {album[0]}')
        album_id = search_id('albums', 'album_title', album[0])
        connection.execute(f"INSERT INTO ArtistAlbum(artist_id, album_id) VALUES({artist_id}, {album_id});")
        for track in album[2]:
            connection.execute(
                f"INSERT INTO tracks(track_title, duration, album_id) VALUES('{track[0]}', {track[1]}, {album_id});")
            print(f'Добавлен трэк {track[0]}')
        connection.execute(f"INSERT INTO ArtistGenre(artist_id, genre_id) VALUES({artist_id}, {genre_id});")
    for va in v_as:
        va_id = search_id('collections', 'collection_title', va[0])
        if va_id is None:
            connection.execute(
                f"INSERT INTO collections(collection_title, release_date) VALUES('{va[0]}', {va[1]});")
            print(f'Добавлен сборник {va[0]}')
            va_id = search_id('collections', 'collection_title', va[0])
        for track in va[2]:
            connection.execute(f"INSERT INTO tracks(track_title, duration) VALUES('{track[0]}', {track[1]});")
            print(f'Добавлен трэк {track[0]}')
            track_id = search_id('tracks', 'track_title', track[0])
            connection.execute(f"INSERT INTO CollectionTrack(collection_id, track_id) VALUES({va_id}, {track_id});")
