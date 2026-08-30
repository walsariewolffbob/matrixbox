#RevampedDepartures

**This README covers the changes I've made available in this version. General functionality is mirrored to the latest official MatrixBox/Departures version of 2026-08-30.**

##General UI changes

I've personally found the UI somewhat difficult to navigate. (Probs just me, but this is my playground! I'll change it if I want to, thank you very much.) Some main changes are moving around of options, making options show conditionally, forcing options that otherwise would maybe cause things to come out weird or laggy. That sorta thing.

##New view

To test if I can - and I apparently could - I made a new view to show departures. It is based on the old(? idk, haven't been in a while) DLR departure screens in London. Basically testing the water before moving on to a major new view which I had planned.

##Scrolling text

On the actual Stockholm Tub, sometimes scrolling text comes past for disruptions. I added that functionality to the Classic SL view the Departures app natively has. It can be set to show disruption information or free text. 
The same logic is added to the DLR view I made myself.

##Button management

I felt a bit constrained in what one can do with the physical button on the box. As I only really run the departures app, I don't really feel like I need the exit function, for example.
So, while I was at it, I added the ability to choose its behaviour in the web-app.

##Future Preperations

**Remote Control**

I've prepared the screen on/off logic to be able to use some sort of "remote control" to turn the screen on or off in the future. This is still in the development phase, so the code is somewhat unstable there. This is me wanting to integrate the box into my HomeAssistant to turn on/off on a more developed schedule and along with the state of my lights at home.

**Multiple stations**

I added a third "view type", which in the future should be able to have up to 5 stations prepared, with the button being able to switch between them. This is mostly out of personal interest, as I live in a place where I use different transport modes (from different stops) during weekdays vs the weekend. The UI is prepared for that, but the logic is not implemented yet.

*If you'd like to try out my changes and found any bugs or things looking not like they should, shoot me a message!*

> DISCLAIMER: This is an unofficial fork of MatrixBox!
