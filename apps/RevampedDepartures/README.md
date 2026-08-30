# Departures

This README covers the settings added by the "XS multi-stop merged list + clock row"
change. The app has many other pre-existing settings (configured entirely through
the on-device web UI); those aren't documented here.

## Merged departure list for narrow (XS, <=64px) displays

The existing **multiple stops** setting shows each configured stop as its own
side-by-side list column. On a 64px-wide panel there's no room for a second
column, so this had no visible effect there.

On narrow displays, enabling **multiple stops** now instead merges the
departures of all configured stops (1-3) into a single list, sorted by
departure time, with the line ID differentiating stops. Configure additional
stops via the **1 / 2 / 3** buttons that appear once "multiple stops" is on
(now shown for narrow panels too, previously only for wider ones).

Enable **XS line ID** as well so each row shows which line it's for.

## Abbreviate dest

Settings > **Abbreviate dest**. Comma-separated `long=short` pairs, e.g.:

```
Zürich=ZH,Bahnhof=Bhf
```

Applied only when a destination name would otherwise be cut off to fit the
display; a name that already fits is left untouched. Pairs are tried in
order and stop as soon as the result fits.

## Clock / date row

Settings > **Clock row**. Replaces one row of the list with the current
time (or date + time) instead of a departure.

| Setting | Values | Notes |
|---|---|---|
| Clock row | on/off | master toggle |
| Clock: show date | on/off | off = time only (`HH:MM`); on = `DD.MM.YY * HH:MM` |
| Clock: position | top / bottom | which row is replaced |
| Clock: align | left / center / right | centered time-only shows as `*** HH:MM ***` |
| Clock: color | white / yellow / amber / red / green / blue | |

Seconds are intentionally not shown: the list only repaints on the regular
departure refresh cycle (~20s), so a seconds field would jump rather than
tick.

## Strip from dest

Settings > **Strip from dest**. Comma-separated substrings to remove from
destination names (e.g. to drop a suffix your local operator always adds).
