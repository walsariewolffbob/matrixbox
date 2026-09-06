Repository layout:

departures_skins/
  README.md
  <skin_id>/
    manifest.json
    __init__.py
    manifest.py
    renderer.py
    implementation.py   (optional if renderer.py is self-contained)

manifest.json is distribution metadata only. Required fields:
  id        safe folder/package identifier
  label     human-readable label
  version   positive integer package version
  format    package format version (currently 1)
  files     exact files copied into departures/skins/<id>/

The installed Python package must still export:
  manifest
  Renderer

Runtime discovery remains fully local and unchanged: skin_engine/registry.py scans
departures/skins/. No network or GitHub knowledge exists in the running app.

Installation/update:
  skin_engine.install.install_package(package_dir, departures/skins)

For manual deployment, copying the complete external skin folder directly to
departures/skins/<id>/ is equivalent, as long as the Python package files are
present. manifest.json may remain installed for diagnostics/version tracking.
