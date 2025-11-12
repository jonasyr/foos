"""Platform detection helpers for Pi3D environments."""

import pi3d


def is_x11():
    """Return ``True`` when the app is running on a desktop X11 environment."""

    return pi3d.PLATFORM != pi3d.PLATFORM_PI and pi3d.PLATFORM != pi3d.PLATFORM_ANDROID


def is_pi():
    """Return ``True`` when the process executes on a Raspberry Pi target."""

    return pi3d.PLATFORM == pi3d.PLATFORM_PI
