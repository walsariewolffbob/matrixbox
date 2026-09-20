# SL Modern line badge styling.
#
# Keep SL-specific presentation rules here so new designations can be added
# without changing the renderer itself.

WHITE = 'white'
BLACK = 'black'

BLUE = 0x008CD0
GREEN = 0x00B45A
RED = 0xE31F23
PINK = 0xF05FA0
REPLACEMENT_ORANGE = 0xFE9C50
GREY = 0x7F867D
TEAL = 0x00ADA5
NOCKEBY_BLUE = 0x708FA8
TVARBANA_ORANGE = 0xE37F1F
LIDINGO_BROWN = 0xB26934
ROSLAGSBANAN_PURPLE = 0xA458AA


def _group_matches(value, expected):
    if isinstance(value, (list, tuple)):
        return expected in value
    return str(value or '').strip() == expected


def _boxed(background, foreground=WHITE, cut_corners=False, shape='box'):
    return {
        'box': True,
        'background': background,
        'foreground': foreground,
        'cut_corners': bool(cut_corners),
        'shape': str(shape or 'box'),
    }


def _plain(foreground=WHITE):
    return {
        'box': False,
        'background': BLACK,
        'foreground': foreground,
        'cut_corners': False,
    }


def resolve_line_badge(line_id, metadata=None, is_night_bus=False):
    """Return SL Modern badge styling for one departure.

    metadata is the generic line metadata preserved by DepartureBox:
    transport_mode, group_of_lines and designation.
    """
    metadata = metadata if isinstance(metadata, dict) else {}
    mode = str(metadata.get('transport_mode', '') or '').strip().upper()
    group = metadata.get('group_of_lines', '')

    # Night bus presentation overrides all other bus categories.
    if mode == 'BUS' and is_night_bus:
        return _boxed(BLACK, RED)

    # Standard boxed SL families.
    if _group_matches(group, 'Tunnelbanans blå linje'):
        return _boxed(BLUE)
    if _group_matches(group, 'Tunnelbanans gröna linje'):
        return _boxed(GREEN)
    if _group_matches(group, 'Tunnelbanans röda linje'):
        return _boxed(RED)
    if _group_matches(group, 'Pendeltåg'):
        return _boxed(PINK)
    if _group_matches(group, 'Ersättningsbuss'):
        return _boxed(REPLACEMENT_ORANGE, BLACK)
    if _group_matches(group, 'Pendelbåt'):
        return _boxed(BLUE)
    if _group_matches(group, 'Waxholmsbolaget'):
        return _boxed(BLUE, shape='flag')
    if _group_matches(group, 'Närtrafiken'):
        return _boxed(RED, BLACK)

    # Light-rail / local-rail families use clipped corner pixels.
    if _group_matches(group, 'Roslagsbanan'):
        return _boxed(ROSLAGSBANAN_PURPLE, cut_corners=True)
    if _group_matches(group, 'Saltsjöbanan'):
        return _boxed(TEAL, cut_corners=True)
    if _group_matches(group, 'Nockebybanan'):
        return _boxed(NOCKEBY_BLUE, cut_corners=True)
    if _group_matches(group, 'Tvärbanan'):
        return _boxed(TVARBANA_ORANGE, cut_corners=True)
    if _group_matches(group, 'Spårväg City'):
        return _boxed(GREY, cut_corners=True)
    if _group_matches(group, 'Lidingöbanan'):
        return _boxed(LIDINGO_BROWN, cut_corners=True)

    # Bus families without a coloured box.
    if _group_matches(group, 'Blåbuss'):
        return _plain(BLUE)
    if mode == 'BUS':
        return _plain(WHITE)

    # Unknown line families remain readable and visually neutral.
    return _boxed(WHITE, BLACK)
