
The **MIDI Fixture Control** is a community-created plugin for
**[Linux Show Player](https://github.com/FrancescoCeruti/linux-show-player)**

This plugin adds the ability to control supported MIDI devices in an abstract way
from within **lisp**.

For instance, if you had an Allen-Heath GLD80 sound desk, and you wished to mute
Input Channel 14: instead of having to look up how to do it in the product manual,
**lisp** now allows you to select that desk, that action, and that channel, and the
appropriate MIDI is pieced together for you.

This has the benefit of if you should decide to switch desks at a later date, you
can simply change the active desk, and all cues update automatically.


### Installation

To use, place the contents in a subfolder of `$XDG_DATA_HOME/linux_show_player/plugins`
(On most Linux systems, this will default to `~/.share/linux_show_player/plugins`.)

When you next start **Linux Show Player**, the program should load the plugin
automatically.


