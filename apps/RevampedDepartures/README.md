# RevampedDepartures

**This README covers the changes I've made available in this version. General functionality is mirrored to the latest official MatrixBox/Departures app update of 2026-08-30.**

## Minor updates

**Web-app UI changes**

I've personally found the UI somewhat difficult to navigate. Some main changes are moving around of settings, making options show conditionally, forcing options that otherwise would perhaps cause things to come out weird or laggy, etc.

**Dynamic times**

In Stockholm, if a departure is more than 30mins away, it is usually shown as a clock time, rather than a minute countdown. I've added that option to the app. Showing everything as a countdown or as a set time is also still available.

**Button management**

As I only really run the departures app, I don't really feel like I always need the long-press exit function. The odd time I run lastfm, I can use the webapp.
Therefore, I added the ability to choose its behaviour in the web-app. Both the short and long-press can be programmed.

** Highlight night buses **

Mostly useful for the DLR lay-out. When active it highlights night buses in red. There is also the option to only do this when both "day traffic" and night buses are displayed on the screen.'
The reason for the function is mostly that DLR-mode can make it unclear when night traffic starts because of the 1-2-3 rather than line numbers.

## New lay-out

I made a new lay-out to show departures. It is based on the classic DLR departure screens in London. The top line shows the first departure in a larger font, the lower two lines the 2nd and 3rd in a smaller all-caps font. A clock can be added in the bottom right as well.

The classic DLR screens don't show line numbers, as those are not used in London, rather numbers the upcoming departures in order. This could be confusing in Stockholm, so the order numbers can be swapped for line numbers. The colour-switching for both lines and minutes remaining is also available for the DLR-screens. I've mirrored these options to the SL-list screen the app supports natively.

## Scrolling text

On the actual Stockholm Tunnelbana, sometimes scrolling text comes past for disruptions. I added a functionality to the Classic SL lay-out where free-text can also be added. When using free-text, the location of the message can be set to be before all scrolling departures, after the first, or after all departures have scrolled by. 

The same logic is added to the DLR lay-out I made myself, both disruption information and free-text are available. The 2nd and 3rd departure line will disappear, the message will then scroll by. In DLR-mode, the interval for both disruptions and free-text can be manually set.

## Remote control screen

I've added functionality to the screen on/off logic to be able to remotely control the screen. It works by typing a webadress in a browser, which sends that command to the box to either turn the screen on or off. Another command returns a JSON line, which could be used for integration purposes (for example, I've included my box in HomeAssistant as if it were a regular lamp).

The commands can be used as follows:

| **Webadress** | **Action** |
|---|---|
| http://YOUR-IP/?screen_power=off | Screen powers off |
| http://YOUR-IP/?screen_power=on | Screen powers on |
| http://YOUR-IP/?screen_state=1 | Returns JSON on screen state |

The button on the box still works normally (depending on the settings in the webapp, see above), as does the digital button in the webapp (current state may not be presented properly). These also update the JSON return.

*This is still in the development phase, so the code may be somewhat unstable. It is functional, but more extensive testing is still required. Moreover, this only works when the RevampedDepartures app is running, as the changes are made in there. Not in the MatrixBox core code*

## Future Preperation: Multiple stations

I added a third "view type", which in the future should be able to have up to 5 stations prepared, with the button being able to switch between them. This is mostly out of personal interest, as I live in a place where I use different transport modes (from different stops) during weekdays vs the weekend. The UI is prepared for that, but the logic is not implemented yet.

---

If you'd like to try out my changes and found any bugs or things not looking or working like they should, shoot me a message!

> DISCLAIMER: This is an unofficial edit of MatrixBox, made under the OpenSource license. See also the license in the top directory.
