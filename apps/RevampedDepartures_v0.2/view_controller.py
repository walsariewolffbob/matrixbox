import time

from skin_engine.base import SkinContext
from skin_engine.registry import (
    get_renderer_class,
    get_renderer_id_for_mode,
    renderer_manifest,
    renderer_manifest_for_mode,
    default_renderer_mode,
)


class ViewContext(SkinContext):
    """Compatibility name for the stable Stage 3B skin context."""
    pass


class ViewController:
    STATE_IDLE = 'idle'
    STATE_SPLASH = 'splash'
    STATE_PREPARE = 'prepare'
    STATE_BUILD = 'build'
    STATE_COMMIT = 'commit'

    def __init__(self):
        self.state = self.STATE_IDLE
        self.active_renderer_id = None
        self.active_renderer = None
        self.context = None

    def renderer_id_for_mode(self, legacy_mode):
        return get_renderer_id_for_mode(legacy_mode)

    def mode_is_owned(self, legacy_mode):
        return self.renderer_id_for_mode(legacy_mode) is not None

    def owns_mode(self, legacy_mode):
        renderer_id = self.renderer_id_for_mode(legacy_mode)
        return renderer_id is not None and self.active_renderer_id == renderer_id

    def create_renderer(self, renderer_id):
        renderer_class = get_renderer_class(renderer_id)
        if renderer_class is None:
            return None
        try:
            return renderer_class()
        except Exception as exc:
            print('SKIN create failed:', renderer_id, exc)
            return None

    def _exit_active(self):
        if self.active_renderer is not None:
            try:
                self.active_renderer.exit(self.context)
            except Exception as exc:
                print('VIEW exit warning:', exc)
        self.active_renderer = None
        self.active_renderer_id = None
        self.context = None

    def deactivate(self):
        self._exit_active()
        self.state = self.STATE_IDLE

    def _prepare(self, renderer, context, allow_messages=True):
        """Prepare data through the active renderer's generic contract."""
        self.state = self.STATE_PREPARE
        return renderer.prepare_data(context, allow_messages=allow_messages)

    def _apply_mode_defaults(self, legacy_mode, functions):
        """Apply View-entry defaults supplied by renderer metadata."""
        mode = int(legacy_mode)
        settings = functions.varinit.settings
        combined = int(settings.get(
            'station_selection_mode',
            1 if int(settings.get('multiple', 0)) else 0
        )) == 1

        # Combined station mode currently requires the List renderer. Resolve it
        # through the registry instead of assuming the controller owns mode maps.
        if combined:
            list_manifest = renderer_manifest('sl_list') or {}
            mode = int(list_manifest.get('legacy_listmode', 1))

        manifest = renderer_manifest_for_mode(mode)
        if manifest is None:
            fallback_mode = default_renderer_mode()
            if fallback_mode is None:
                raise RuntimeError('No valid renderers are registered')
            print('VIEW fallback: unregistered mode', mode, '->', fallback_mode)
            mode = int(fallback_mode)
            manifest = renderer_manifest_for_mode(mode)

        settings['listmode'] = mode
        for key, value in (manifest.get('defaults', {}) or {}).items():
            settings[key] = value
        if combined:
            for key, value in (manifest.get('combined_defaults', {}) or {}).items():
                settings[key] = value

        if bool(manifest.get('reset_disruption_timer_on_enter', False)):
            functions.varinit.shared['disruption_timer'] = time.monotonic()

        return mode

    def activate_mode(self, legacy_mode, functions, classic_refresh_times=2,
                      splash=True, source='main'):
        legacy_mode = self._apply_mode_defaults(legacy_mode, functions)
        renderer_id = self.renderer_id_for_mode(legacy_mode)
        if renderer_id is None:
            return False
        print('VIEW enter:', renderer_id, 'source:', source)

        # Stop ticks from the source renderer before splash/preparation begins.
        self._exit_active()
        self.state = self.STATE_SPLASH if splash else self.STATE_PREPARE
        if splash:
            functions.view_switch_loading(2.0)

        renderer = self.create_renderer(renderer_id)
        if renderer is None:
            raise RuntimeError('Renderer unavailable: ' + renderer_id)
        context = ViewContext(functions, classic_refresh_times=classic_refresh_times)
        renderer.enter(context)

        payload = self._prepare(renderer, context, allow_messages=False)
        self.state = self.STATE_BUILD
        renderer.build(payload, context)
        renderer.after_build(context)

        self.state = self.STATE_COMMIT
        functions.refresh()

        self.context = context
        self.active_renderer_id = renderer_id
        self.active_renderer = renderer
        self.state = self.STATE_IDLE
        print('VIEW active:', renderer_id)
        return True

    def rebuild_active(self, functions, allow_messages=True):
        """Rebuild the currently active renderer through the controller pipeline."""
        if self.active_renderer is None or self.active_renderer_id is None:
            return False

        renderer_id = self.active_renderer_id
        payload = self._prepare(self.active_renderer, self.context, allow_messages=allow_messages)

        self.state = self.STATE_BUILD
        self.active_renderer.build(payload, self.context)
        self.active_renderer.after_build(self.context)

        self.state = self.STATE_COMMIT
        functions.refresh()
        self.state = self.STATE_IDLE
        return True

    def tick(self, now, context=None):
        if self.state != self.STATE_IDLE or self.active_renderer is None:
            return False
        ctx = context if context is not None else self.context

        # Hidden/off displays must not free-run renderer animation. On hardware
        # display.refresh() normally provides much of the loop pacing; when the
        # group is hidden that pacing disappears and Classic can otherwise race
        # through ticker cycles and repeatedly fetch/rebuild.
        try:
            if not ctx.functions.get_screen_state():
                return False
        except Exception:
            pass

        action = self.active_renderer.tick(now, ctx)
        if action == 'rebuild':
            return self.rebuild_active(ctx.functions, allow_messages=True)
        if action == 'refresh':
            ctx.functions.refresh()
            return True
        return bool(action)


controller = ViewController()
