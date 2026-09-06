import time
from skin_engine.services import SkinServices


class SkinContext:
    """Stable renderer-facing context.

    Stage 3B keeps ``functions`` available for the current built-ins, while
    exposing common state through narrow properties/methods that external skins
    can use without reaching directly into controller internals.
    """

    def __init__(self, functions, classic_refresh_times=2):
        self.functions = functions
        self.services = SkinServices(functions)
        self.classic_refresh_times = classic_refresh_times

    @property
    def settings(self):
        return self.services.settings

    @property
    def shared(self):
        return self.services.shared

    @property
    def display_width(self):
        return self.functions.varinit.display.width

    @property
    def display_height(self):
        return self.functions.varinit.display.height

    @property
    def now_text(self):
        try:
            return self.services.now_text()
        except Exception:
            return 'Nu'

    def clear(self, surface):
        return self.services.clear(surface)

    def render_text(self, text, *args, **kwargs):
        return self.services.render_text(text, *args, **kwargs)

    def request_refresh(self):
        """Renderer tick helper: return this value to request one refresh."""
        return 'refresh'

    def request_rebuild(self):
        """Renderer tick helper: return this value to request a rebuild."""
        return 'rebuild'


class BaseRenderer:
    renderer_id = 'base'
    display_name = 'Base renderer'
    implemented = False

    # Metadata is kept close to the renderer so a future skin can provide the
    # same information without hard-coding it into the web UI/controller.
    metadata = {
        'departure_count': None,
        'supports_tick': False,
        'supports_128x32': True,
        'legacy_listmode': None,
        'data_pipeline': 'raw',
        'post_build': 'standard',
        'defaults': {},
        'combined_defaults': {},
        'capabilities': {},
        'show_in_view_menu': True,
    }

    def __init__(self):
        self.active = False
        self.context = None

    def enter(self, context):
        """Reset renderer-local state before the first build.

        No network access and no physical display refresh is allowed here.
        """
        self.context = context
        self.active = True

    def prepare_data(self, context, allow_messages=True):
        """Prepare the payload consumed by build().

        Stage 3D1 makes this the generic preparation contract used by the
        controller. The default renderer behavior is the ordinary raw
        departure feed; built-in skins may override this while preparation
        ownership is being migrated out of ViewController.
        """
        return context.services.get_departures()

    def build(self, departures, context):
        """Build a complete target view from prepared departures.

        Implementations must not perform the final display commit.
        """
        raise NotImplementedError('Renderer build() is not implemented')

    def after_build(self, context):
        """Finalize renderer-owned state after build(), before commit.

        The default behavior starts the ordinary timed-refresh window. Skins
        override this only when they own additional post-build state.
        """
        context.services.shared['scroll_timer'] = time.monotonic()
        return True

    def tick(self, now, context):
        """Advance renderer-local animation after activation."""
        return False

    def exit(self, context):
        """Stop/reset renderer-local transient state before leaving the View."""
        self.active = False
        self.context = None

    def refresh_settings(self, context):
        """Accept non-structural settings changes without changing View."""
        self.context = context
