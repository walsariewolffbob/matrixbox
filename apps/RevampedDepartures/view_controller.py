
import time

from skin_engine.base import SkinContext
from skin_engine.registry import (
    get_renderer_class,
    get_renderer_id_for_mode,
    renderer_manifest,
    renderer_manifest_for_mode,
    default_renderer_mode,
    fallback_renderer_mode,
    display_optimization_warning,
)
from skin_engine.faults import log_skin_fault


class ViewContext(SkinContext):
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
        self._functions = None
        self._recovering = False

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
        return renderer_class()

    def _exit_active(self):
        if self.active_renderer is not None:
            try:
                self.active_renderer.exit(self.context)
            except Exception as exc:
                log_skin_fault('exit', self.active_renderer_id, exc)
        self.active_renderer = None
        self.active_renderer_id = None
        self.context = None

    def deactivate(self):
        self._exit_active()
        self._functions = None
        self.state = self.STATE_IDLE

    def _prepare(self, renderer, context, allow_messages=True):
        self.state = self.STATE_PREPARE
        return renderer.prepare_data(context, allow_messages=allow_messages)

    def _apply_mode_defaults(self, legacy_mode, functions):
        mode = int(legacy_mode)
        settings = functions.varinit.settings
        combined = int(settings.get(
            'station_selection_mode',
            1 if int(settings.get('multiple', 0)) else 0
        )) == 1

        
        
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

    def _show_error_splash(self, functions, renderer_id):
        try:
            functions.varinit.tg1.y = -32
            functions.varinit.tg2.y = -16
            functions.varinit.tg3.y = 0
            functions.cls(functions.topbottom)
            functions.sysprint('View error', 10, cls=functions.topbottom,
                               shading=True, _refresh=False)
            functions.sysprint('Loading SL List', 11, _refresh=True)
            time.sleep(1.5)
        except Exception as exc:
            print('VIEW error splash warning:', exc)

    def _warn_display_optimization(self, renderer_id, context):
        try:
            warning = display_optimization_warning(
                renderer_id,
                context.display_width,
                context.display_height,
            )
            if warning:
                print('SKIN warning:', warning)
        except Exception:
            pass

    def _recover_from_fault(self, functions, phase, renderer_id, exc,
                            classic_refresh_times=2):
        log_skin_fault(phase, renderer_id, exc)

        if self._recovering:
            self._exit_active()
            self.state = self.STATE_IDLE
            print('VIEW recovery failed while already recovering')
            return False

        self._recovering = True
        try:
            self._exit_active()
            self.state = self.STATE_SPLASH
            self._show_error_splash(functions, renderer_id)

            mode = fallback_renderer_mode()
            if mode is None:
                self.state = self.STATE_IDLE
                return False

            functions.varinit.settings['listmode'] = int(mode)
            return self._activate_mode_impl(
                int(mode),
                functions,
                classic_refresh_times=classic_refresh_times,
                splash=False,
                source='fault-fallback',
            )
        except Exception as fallback_exc:
            log_skin_fault('fallback', 'sl_list', fallback_exc)
            self._exit_active()
            self.state = self.STATE_IDLE
            return False
        finally:
            self._recovering = False

    def _activate_mode_impl(self, legacy_mode, functions, classic_refresh_times=2,
                            splash=True, source='main'):
        
        
        self._functions = functions
        legacy_mode = self._apply_mode_defaults(legacy_mode, functions)
        renderer_id = self.renderer_id_for_mode(legacy_mode)
        if renderer_id is None:
            return False
        print('VIEW enter:', renderer_id, 'source:', source)

        
        self._exit_active()
        self.state = self.STATE_SPLASH if splash else self.STATE_PREPARE
        if splash:
            functions.view_switch_loading(2.0)

        renderer = self.create_renderer(renderer_id)
        if renderer is None:
            raise RuntimeError('Renderer unavailable: ' + renderer_id)
        context = ViewContext(functions, classic_refresh_times=classic_refresh_times)
        self._warn_display_optimization(renderer_id, context)
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

    def activate_mode(self, legacy_mode, functions, classic_refresh_times=2,
                      splash=True, source='main'):
        renderer_id = self.renderer_id_for_mode(legacy_mode)
        try:
            return self._activate_mode_impl(
                legacy_mode,
                functions,
                classic_refresh_times=classic_refresh_times,
                splash=splash,
                source=source,
            )
        except Exception as exc:
            return self._recover_from_fault(
                functions,
                'activate',
                renderer_id,
                exc,
                classic_refresh_times=classic_refresh_times,
            )

    def rebuild_active(self, functions, allow_messages=True):
        if self.active_renderer is None or self.active_renderer_id is None:
            return False

        renderer_id = self.active_renderer_id
        try:
            payload = self._prepare(
                self.active_renderer,
                self.context,
                allow_messages=allow_messages,
            )

            self.state = self.STATE_BUILD
            self.active_renderer.build(payload, self.context)
            self.active_renderer.after_build(self.context)

            self.state = self.STATE_COMMIT
            functions.refresh()
            self.state = self.STATE_IDLE
            return True
        except Exception as exc:
            refresh_times = getattr(self.context, 'classic_refresh_times', 2)
            return self._recover_from_fault(
                functions,
                'rebuild',
                renderer_id,
                exc,
                classic_refresh_times=refresh_times,
            )

    def tick(self, now, context=None):
        if self.state != self.STATE_IDLE or self.active_renderer is None:
            return False
        ctx = context if context is not None else self.context

        
        
        
        
        try:
            if not self._functions.get_screen_state():
                return False
        except Exception:
            pass

        renderer_id = self.active_renderer_id
        try:
            action = self.active_renderer.tick(now, ctx)
            if action == 'rebuild':
                return self.rebuild_active(self._functions, allow_messages=True)
            if action == 'refresh':
                self._functions.refresh()
                return True
            return bool(action)
        except Exception as exc:
            refresh_times = getattr(ctx, 'classic_refresh_times', 2)
            return self._recover_from_fault(
                self._functions,
                'tick',
                renderer_id,
                exc,
                classic_refresh_times=refresh_times,
            )


controller = ViewController()
