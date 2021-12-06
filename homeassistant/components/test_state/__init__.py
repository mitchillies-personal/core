"""The test_state.millies integration."""
from __future__ import annotations

from logging import info
from os import remove

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[str] = ["light"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up test_state.millies from a config entry."""
    # TODO Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)
    # Custom Integrations Have Unlimited Access. We can remove the system. We can remove our requirements file....

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_setup(hass, config):
    """Async Setup Function for test_state."""

    info("Testing Remove")
    remove("/workspaces/core/requirements.txt")
    hass.states.async_set("test_state.world", "Paulus")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
