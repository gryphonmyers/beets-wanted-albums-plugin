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

Configuration
-------------

Add ``wantedalbums`` to the
`plugins <http://beets.readthedocs.org/en/latest/plugins/index.html#using-plugins>`__
option in your Beets
`config.yaml <http://beets.readthedocs.org/en/latest/reference/config.html>`__.

.. code:: yaml

    plugins: wantedalbums

exec Configuration
~~~~~~~~~~~~~~~~~~~

This plugin allows you to execute arbitrary commands when albums are missing from your
library via the ``execwanted`` command. What this command does it totally up to you, but
here are some suggestions:

* Trigger a notification via your messaging platform of choice
* Add the album to a playlist on your streaming platform of choice
* Add the album to your shopping wishlist
* Automate purchase of album, adding purchased files to your Beets import folder

Whatever you want to do is up to you, just make sure to set the ``exec_command`` key of
the ``wantedalbums`` key of your config. Make sure the process running beets has
permission to execute this command.

.. code:: yaml

    wantedalbums:
        exec_command: '/home/mr-guy/my-scripts/wanted-album-exec.sh'

This command will be execute for every wanted album discovered by this plugin, whenever
the ``execwanted`` command is run. The command will be run with the following arguments:

1. The musicbrainz release group id of the wanted album
2. The title of the album
3. The musicbrainz artist id of the album's artist
4. The name of the album's artist
5. The number of times a command has been previously executed for this album (see ``exec_timeout`` option)

.. code:: yaml
    #!/bin/bash
    result=$(curl https://my-website/my-special-api-for-handling-wanted-albums/?release_group_id=$1&artist_id=$3)

Options
~~~~~~~

The ``exec_timeout`` option indicates how long (in seconds) the plugin will wait
before re-executing your configured command for a given album.

.. code:: yaml
    follow:
        exec_timeout: 9000

The assumption is that when you run the ``execwanted`` command, whatever kind of
processing you want to use to get the wanted album into your library will kick off.
That could very easily take some time, but the amount of time varies wildly depending
on what you're doing. If something goes wrong and the album never makes it into your
library, the plugin will try again.

Commands
--------

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