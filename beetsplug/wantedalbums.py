from beets.plugins import BeetsPlugin
from beets.ui import Subcommand, decargs, print_, input_yn, UserError
from beets import config
import musicbrainzngs
import time
import subprocess
import pickle

MONITORED_ARTISTS_KEY = 'monitoredartists'
WANTED_RELEASE_GROUPS_KEY = 'wantedreleasegroups'
    
class BeetsWantedAlbumsPlugin(BeetsPlugin):
    def __init__(self):
        super().__init__()
        self.config.add({
            'exec_timeout': 5000,
            'statefile': 'wantedalbums.pickle'
        })
        self.import_stages = [self.on_import]

    def commands(self):
        monitor = Subcommand('monitor',
                              help='Add album artists of albums matching query to monitored list. Missing albums by this artist will be added to wanted list.')
    
        monitor.func = self.monitor

        unmonitor = Subcommand('unmonitor',
                              help='Remove artist from monitored list. Missing albums by this artist will no longer be added to wanted list, and current albums on the want list will be removed.')
        
        unmonitor.func = self.unmonitor

        updatewanted = Subcommand('updatewanted',
                              help='Check monitored artists for missing albums, adding them wanted list.')
        
        updatewanted.func = self.update_wanted_albums

        listwanted = Subcommand('listwanted',
                              help='List wanted albums.')
        
        listwanted.func = self.list_wanted_albums

        listmonitored = Subcommand('listmonitored',
                              help='List monitored artists.')
        
        listmonitored.func = self.list_monitored_artists

        execwanted = Subcommand('execwanted',
                              help='Run external command for each wanted album.')
        
        execwanted.func = self.exec_wanted_albums

        return [monitor, unmonitor, updatewanted, listwanted, listmonitored, execwanted]

    def on_import(self, session, task):
        if task.is_album:
            state = self._open_state()
            if task.album['mb_albumartistid'] in state[WANTED_RELEASE_GROUPS_KEY]:
                    
                def is_match(item):
                    return task.album['mb_releasegroupid'] == item['rgid']
                
                wanted_match = list(filter(is_match, state[WANTED_RELEASE_GROUPS_KEY][task.album['mb_albumartistid']]))

                if len(wanted_match) > 0:
                    wanted_match[0]['status'] = 'imported'
                    wanted_match[0]['imported_at'] = time.time()
                    self._save_state(state)

    def monitor(self, lib, opts, args):
        items = lib.items(decargs(args))
        state = self._open_state()

        if len(items) == 0:
            self._log.info('No items match that query.')
            return

        def _artist_not_in_state(artist):
            return artist[0] not in state[MONITORED_ARTISTS_KEY]
        
        new_artists = list(filter(_artist_not_in_state, self._get_album_artists(items)))

        if len(new_artists) == 0:
            self._log.info('No unmonitored artists match that query.')
            return
        
        for artist in new_artists:
            self._print_artist_tuple(artist)
        
        if input_yn('Found {0} new artists. Monitor them? (y/n)'.format(len(new_artists))):
            for artist in new_artists:
                state[MONITORED_ARTISTS_KEY][artist[0]] = artist
            self._log.info('Monitored %s new artist(s).' % len(new_artists))
            self._save_state(state)

    def unmonitor(self, lib, opts, args):
        items = lib.items(decargs(args))
        state = self._open_state()

        if len(items) == 0:
            self._log.info('No items match that query.')
            return

        def _artist_in_state(artist):
            return artist[0] in state[MONITORED_ARTISTS_KEY]
        
        monitored_artists = list(filter(_artist_in_state, self._get_album_artists(items)))

        if len(monitored_artists) == 0:
            self._log.info('No monitored artists match that query.')
            return
        
        for artist in monitored_artists:
            self._print_artist_tuple(artist)

        if input_yn('Found {0} monitored artists. Unmonitor them? (y/n)'.format(len(monitored_artists))):
            for artist in monitored_artists:
                state[MONITORED_ARTISTS_KEY].pop(artist[0])
            self._log.info('Unmonitored %s artist(s).' % len(monitored_artists))
            self._save_state(state)

    def list_monitored_artists(self, lib, opts, args):
        state = self._open_state()
        
        if MONITORED_ARTISTS_KEY not in state:
            self._log.info('No monitored artists')
            return
            
        items = lib.items(decargs(args))        
        
        def _artist_in_state(artist):
            return artist[0] in state[MONITORED_ARTISTS_KEY]
        
        monitored_artists = list(filter(_artist_in_state, self._get_album_artists(items)))
        
        for artist in monitored_artists:
            self._print_artist_tuple(artist)

    
    def list_wanted_albums(self, lib, opts, args):
        state = self._open_state()
        
        for artist_id in state[WANTED_RELEASE_GROUPS_KEY]:
            for release_group in state[WANTED_RELEASE_GROUPS_KEY][artist_id]:
                if release_group['status'] == 'wanted' or release_group['status'] == 'pending':
                    print_('{0} - {1} - {2}'.format(state[MONITORED_ARTISTS_KEY][artist_id][1], release_group['title'],  release_group['status']))

    def exec_wanted_albums(self, lib, opts, args):
        state = self._open_state()
        for artist_id in state[WANTED_RELEASE_GROUPS_KEY]:
            for release_group in state[WANTED_RELEASE_GROUPS_KEY][artist_id]:
                if release_group['status'] == 'wanted' or (release_group['status'] == 'pending' and time.time() - release_group['exec_timestamp'] > self.config['exec_timeout'].as_number()):
                    subprocess.run([self.config['exec_command'].as_str(), release_group['rgid'], release_group['title'], str(release_group['wanted_timestamp'])]) 
                    release_group['status'] = 'pending'
                    release_group['exec_timestamp'] = time.time()
                    self._save_state(state)

    def update_wanted_albums(self, lib, opts, args):
        state = self._open_state()

        if MONITORED_ARTISTS_KEY not in state:
            self._log.info('No monitored artists. Wanted albums update skipped.')
            return

        items = lib.items(decargs(args))        
        
        def _artist_in_state(artist):
            return artist[0] in state[MONITORED_ARTISTS_KEY]
        
        monitored_artists = list(filter(_artist_in_state, self._get_album_artists(items)))

        if len(monitored_artists) == 0:
            self._log.info('No monitored artists match that query.')
            return
        """ TODO add all artist ids to the same query instead of iterating artists """
        for artist in monitored_artists:
            def get_album_release_group(album):
                return album.get('mb_releasegroupid')

            library_artist_release_group_ids = list(map(get_album_release_group, lib.albums('mb_albumartistid:{0}'.format(artist[0]))))

            if artist[0] not in state[WANTED_RELEASE_GROUPS_KEY]:
                state[WANTED_RELEASE_GROUPS_KEY][artist[0]] = []

            wanted_release_groups = state[WANTED_RELEASE_GROUPS_KEY][artist[0]]
            new_wanted_release_groups = []

            exhausted = False

            def get_rgid(item):
                return item['rgid']
            
            while not exhausted:            
                release_group_ids_to_exclude = library_artist_release_group_ids + list(map(get_rgid, wanted_release_groups + new_wanted_release_groups))
                
                try:
                    result = musicbrainzngs.search_release_groups(
                        'arid:{0} AND NOT rgid:({1})'.format(artist[0], ' OR '.join(release_group_ids_to_exclude)) if len(release_group_ids_to_exclude) > 0 else 'arid:{0}'.format(artist[0]),
                        limit = 100
                    )
                except (musicbrainzngs.ResponseError, musicbrainzngs.NetworkError) as exc:
                    raise UserError(f'MusicBrainz API error: {exc}')

                if result['release-group-count'] == len(result['release-group-list']):
                    exhausted = True

                for release_group in result['release-group-list']:
                    new_wanted_release_groups.append({
                        'rgid': release_group['id'],
                        'title': release_group['title'],
                        'wanted_timestamp': time.time(),
                        'status': 'wanted'
                    })
                    print('{0} - {1}'.format(artist[1], release_group['title']))

            if len(new_wanted_release_groups) > 0:
                state[WANTED_RELEASE_GROUPS_KEY][artist[0]] = wanted_release_groups + new_wanted_release_groups
                self._save_state(state)
                self._log.info('Added {0} new albums to want list for artist {1}'.format(len(new_wanted_release_groups), artist[1]))

    def unwant():
        pass

    def _print_artist_tuple(self, artist):
        print_('name: {1} | mb_id: {0}'.format(*artist))
            
    def _save_state(self, state):
        """Writes the state dictionary out to disk."""
        try:
            with open(self.config['statefile'].as_filename(), 'wb') as f:
                pickle.dump(state, f)
        except OSError as exc:
            self._log.error('state file could not be written: {0}', exc)

    def _open_state(self):
        """Reads the state file, returning a dictionary."""
        try:
            with open(self.config['statefile'].as_filename(), 'rb') as f:
                state = pickle.load(f)
        except Exception as exc:
            # The `pickle` module can emit all sorts of exceptions during
            # unpickling, including ImportError. We use a catch-all
            # exception to avoid enumerating them all (the docs don't even have a
            # full list!).
            self._log.debug('state file could not be read: {0}', exc)
            state = {}
            
        if MONITORED_ARTISTS_KEY not in state:
            state[MONITORED_ARTISTS_KEY] = {}
            
        if WANTED_RELEASE_GROUPS_KEY not in state:
            state[WANTED_RELEASE_GROUPS_KEY] = {}

        return state
    
    def _get_album_artists(self, items):
        """Find the set of album artists belonging to the list of items and return it sorted."""
        albums = set([item.get_album() for item in items])
        return sorted(set([(album.get('mb_albumartistid'), album.albumartist)
                           for album in albums if album is not None]))
