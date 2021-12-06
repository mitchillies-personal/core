"""Platform for light integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, LightEntity
from homeassistant.core import HomeAssistant

# Import the device class from the component that you want to support
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Setup a Platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    return
    # Setup connection with devices/cloud


class Light(LightEntity):
    """Representation of a Light."""

    def __init__(self, light) -> None:
        """Initialize a Light."""

        self._light = light
        self._name = light.name
        self._state = None
        self._brightness = None

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""

        return True

    def turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on.
        You can skip the brightness part if your light does not support
        brightness control."""

        self._light.brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        self._light.turn_on()

    def turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""

        self._light.turn_off()

    def update(self) -> None:
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant."""

        self._light.update()
        self._state = self._light.is_on()
        self._brightness = self._light.brightness
