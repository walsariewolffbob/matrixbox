
# RevampedDepartures v0.2.1

An expanded and redesigned version of the official **MatrixBox Departures** app, with additional display layouts, more control over how departures are shown, an improved web interface, and the groundwork for installable custom display skins.

The underlying departure functionality is based on the latest official `MatrixBox/Departures` app available on **2026-09-08**.

## Changes in v0.2.1

### Skins are now separated from the app core

The biggest change in v0.2.1 is a new renderer/skin architecture.

Previously, the different departure layouts were tightly integrated with the main application logic. This have now been separated so that each display style can own its own rendering, layout behaviour, view-specific options and display update logic

Skin files are stored in `/skins`. Shared skin handling and supporting logic live in `/skin_engine`

The goal is to make it much easier to add, maintain and eventually install completely new display styles without modifying large parts of the core app. Documentation for the new structure is available in the `/docs` folder.

**Installing new skins directly is not supported yet.**

> **Note:** v0.2.1 introduces a significant internal restructuring and still needs more testing on physical MatrixBox hardware. If stability is your main priority, use **v0.1.5.1** for now.

---

## Changes in previous versions

### New departure layout

The legacy **SL Classic** and **SL List** are retained. Modifications are listed below.

A new layout, **TfL DLR**, inspired by the classic departure displays used on London's Docklands Light Railway, has been incorporated. The next departure is shown prominently on the top row, while departures 2 and 3 are shown underneath in a smaller font. An optional clock can also be displayed in the bottom-right corner. The real DLR displays normally show departure order rather than line numbers, but it's possible to instead set line numbers to be displayed.


### Dynamic departure times

Stockholm departure displays switch between countdowns and clock times depending on how far away the departure is. This behaviour is now mirrored in the app. Departures more than 30mins away are shown as its scheduled time, rather than countdown. You can also force all departures to use countdowns or clock times instead, rather than the dynamic option.

Furthermore, when the departure is less than 1 min away, the display now shows `Nu` on screen by default. This is editable in the web UI.


### Night bus highlighting

Night buses can optionally be highlighted in red, making the transition between daytime and night traffic easier to spot. This is particularly useful with the DLR layout, where departure order numbers are the standard rather than line numbers.

Highlighting can be turned **On**, **Off**, or set to "**Mixed Traffic**", where highlighting is only used when both daytime services and night buses are visible at the same time.


### Scrolling messages

Both **SL Classic** and **TfL DLR** support additional scrolling text. Messages can come from traffic disruption information or custom free text.

Within **SL Classic**, custom text can be inserted, before or after the departure list, as well as after the first departure in the bottom row ticker.

In **TfL DLR** mode, the lower two departure rows temporarily move away while the message scrolls across the screen, after which the departures return. The interval between messages can also be configured in this mode.


### Improved web interface

The web interface has been reorganised to make the increasing number of options easier to understand.

Settings are grouped according to what they affect, and options are shown only when they are relevant to the currently selected transport type or display layout. Some settings are also automatically restricted where combinations would produce an unusable or poorly performing display.

Among other things, the web interface provides control over:

- Departure layout
- Transport types
- Direction and line filtering
- Countdown behaviour, minute markers and "now" indication
- Clock display
- Line and minute colour inversion
- Scrolling text
- Night buses and highlighting
- Physical button behaviour


### Configurable physical button

The MatrixBox button no longer has to use the standard short-press/long-press behaviour. Both button actions can be configured from the web interface. This is useful for boxes primarily dedicated to Departures, where the normal long-press exit behaviour may not always be needed.


### Remote screen control

The physical display can also be switched on and off over the network by "visiting" a webpage while the app is running. This makes it possible to control the MatrixBox from another system. Replace `YOUR-IP` with the IP address of your MatrixBox:

| Address | Action |
| --- | --- |
| `http://YOUR-IP/?screen_power=off` | Turn the display off |
| `http://YOUR-IP/?screen_power=on` | Turn the display on |
| `http://YOUR-IP/?screen_state=1` | Return the current display state as JSON |

The physical button and the button in the web interface continue to work normally, departures are also still updated while the screen is off.

> **Note:** Remote screen control is currently implemented inside the RevampedDepartures app rather than the MatrixBox core, so these endpoints are only available while this app is running. Furthermore, if you plan to use this frequently, for example with HomeAssistant or IFTTT, it is highly recommended to assign a static IP to your MatrixBox as to not break any integrations when the connection has been interrupted.


## Status

RevampedDepartures is still under active development. Version **0.2.1** represents a substantial internal change because the display layouts have been moved into independent skins. The current layouts are functional, but this version needs more long-term testing on real MatrixBox hardware.

For the more established version, use **v0.1.5.1**.

*If you try the app and find a bug, graphical issue or behaviour that doesn't seem right, feel free to get in touch or open an issue.*

### Planned

The next major step is to continue developing the skin system so that additional display skins can be added without modifying the main application.

> **Disclaimer:** RevampedDepartures is an unofficial modification of MatrixBox and is not part of the official MatrixBox project. It is distributed under the applicable open-source licence; see the licence in the repository root.
