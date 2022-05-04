
MIDI Fixture Control
====================

The **MIDI Fixture Control** is a community-created plugin for `Linux Show
Player`_.

This plugin adds the ability to control supported MIDI devices in an abstract
way from within *Linux Show Player*.

For instance, if you had an *Allen & Heath GLD80* sound desk, and you wished to
mute Input Channel 14: instead of having to look up how to do it in the product
manual, this plugin allows you to select that desk, that action, and that
channel - and the appropriate MIDI is pieced together for you.

At no point does the user need to know the ``MIDI`` implementation of the device
they're sending messages to.


Usage
-----

Once the plugin has been installed and enabled, you can find a ``MIDI`` patch
list (akin to a lighting console's ``DMX`` patch list) in the *Session
Preferences* dialog.

Select and address your device; then save and close the dialog.

Create one or more *Fixture Control Cues*, and edit them to instruct *Linux Show
Player* what you wish it to tell the attached device to do.

When you hit "Go", the requested action should be performed.


Dependencies
------------

This plugin depends on a python module that isn't currently publicly available
right now. Sorry.


Installation
------------

To use, navigate to ``$XDG_DATA_HOME/LinuxShowPlayer/$LiSP_Version/plugins/``
(on most Linux systems ``$XDG_DATA_HOME`` is ``~/.local/share``), and create a
subfolder named ``midi_fixture_control``.

Place the files comprising this plugin into this new folder.

When you next start **Linux Show Player**, the program should load the plugin
automatically.

.. _Linux Show Player: https://github.com/FrancescoCeruti/linux-show-player
