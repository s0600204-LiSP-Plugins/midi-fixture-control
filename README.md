
The **MIDI Fixture Control** is a community-created plugin for
**[Linux Show Player](https://github.com/FrancescoCeruti/linux-show-player)**

This plugin adds the ability to control supported MIDI devices in an abstract
way from within **LiSP**.

For instance, if you had an Allen-Heath GLD80 sound desk, and you wished to mute
Input Channel 14: instead of having to look up how to do it in the product
manual, **LiSP** now allows you to select that desk, that action, and that
channel, and the appropriate MIDI is pieced together for you.

This has the benefit of if you should decide to switch desks at a later date,
you can simply change the active desk, and all cues update automatically.


### Installation

To use, navigate to `$XDG_DATA_HOME/LinuxShowPlayer/$LiSP_Version/plugins/` (on
most Linux systems `$XDG_DATA_HOME` is `~/.local/share`), and create a subfolder
named `midi_fixture_control`.

Place the files comprising this plugin into this new folder.

When you next start **Linux Show Player**, the program should load the plugin
automatically.


