Wanted Albums Plugin for Beets
==============================

Plugin for the music library manager,
`Beets <http://beets.radbox.org/>`__. Discover new or old 
albums missing from your music collection, and take action!

Installation
------------
Instructions 

.. code:: sh

    git clone https://github.com/gryphonmyers/beets-wanted-albums-plugin.git
    cd beets-wanted-albums-plugin
    python setup.py install

Add ``wantedalbums`` to the
`plugins <http://beets.readthedocs.org/en/latest/plugins/index.html#using-plugins>`__
option in your Beets
`config.yaml <http://beets.readthedocs.org/en/latest/reference/config.html>`__.

.. code:: yaml

    plugins: wantedalbums


Commands
--------
This plugin adds several new commands to Beets, allowing you to curate and act upon your wanted albums list.

monitor
~~~~~~~~

``beet monitor [query]``

The album artist(s) of the items matching the provided query will be added 
to your monitored artist list. Subsequent calls to ``updatewanted`` will 
include these artists.

If no query is included, all album artists in your library will be monitored.

unmonitor
~~~~~~~~

``beet unmonitor [query]``

The album artist(s) of the items matching the provided query will be removed 
from your monitored artist list. Subsequent called to ``updatewanted`` will 
no longer include these artists (any currently wanted albums will remain - 
if you want those removed, use the ``unwant`` command).

If no query is included, all album artists in your library will be unmonitored.

listmonitored
~~~~~~~~

``beet listmonitored [query]``

Lists out any monitored album artist(s) of the items matching the provided query.

If no query is included, all monitored artists will be listed.

updatewanted
~~~~~~~~

``beet updatewanted [query]``

Searches Musicbrainz for release groups (albums) that have an album artist
matching any of your monitored artists. All matching albums will be stored in the
list of wanted albums.

If no query is included, albums will be searched for all monitored artists.

listwanted
~~~~~~~~

``beet listwanted``

Lists all wanted albums.

execwanted
~~~~~~~~

``beet execwanted``

Executes a command for each wanted album. If that command does not error, the album
will be marked as ``pending``. Pending albums will not be included in subsequent 
calls of ``execwanted`` until the configured ``exec_timeout`` has passed OR the album
has been imported into your library. 

The intended purpose of this command is for you to run a script that will eventually 
lead to the album being imported into your library. If something goes wrong and the 
album never makes it into your library, ``exec_timeout`` allows you to have the plugin 
try again.

Configuration
~~~~~~~~~~~~~~~~~~~

exec_command
~~~~~~~~

An executable command (e.g. a path to a bash script) that will be run for each wanted
albums when ``execwanted`` is run.

.. code:: yaml

    wantedalbums:
        exec_command: '/home/mr-guy/my-scripts/wanted-album-exec.sh'

The command will be run with the following arguments:

1. The musicbrainz release group id of the wanted album
2. The title of the album
3. The musicbrainz artist id of the album's artist
4. The name of the album's artist
5. The number of times a command has been previously executed for this album (see ``exec_timeout`` option)

[exec_timeout=5000]
~~~~~~~

The ``exec_timeout`` option indicates how long (in seconds) the ``execwanted`` command
will wait before re-executing your configured command for a given album.

.. code:: yaml
    follow:
        exec_timeout: 9000
