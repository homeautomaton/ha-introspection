"""The Home Assistant Introspection integration."""
import logging

import homeassistant.core as ha
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .const import SERVICE_DO_INTROSPECTION
from .const import ATTR_EXPRESSION
from .const import ATTR_STATEMENT
from .const import ATTR_LIMIT


SCHEMA_DO_INTROSPECTION = vol.Schema(
    {
    vol.Required(ATTR_EXPRESSION): cv.string,
    vol.Optional(ATTR_STATEMENT): cv.string,
    vol.Optional(ATTR_LIMIT): cv.positive_int,
    }
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up Home Assistant Introspection from a config entry."""

    async def async_do_introspection(call: ha.ServiceCall) -> None:
        """do introspection."""
        result = ""
        stmt = ""
        limit = 2550

        if ATTR_LIMIT in call.data:
            limit = call.data[ATTR_LIMIT]

        limit = int((limit + 254) / 255)

        if ATTR_STATEMENT in call.data:
            stmt = call.data[ATTR_STATEMENT]

        if stmt != "":
            try:
                exec(stmt)
            except Exception as e:
                result = str(e)

        if result == "":
            try:
                expression = call.data[ATTR_EXPRESSION]
                result = str(eval(expression))
            except Exception as e:
                result = str(e)

        if result == '':
            result = '<none>'

        total_len = len(result)
        n = 0
        while result != '' and n < limit:
            n += 1
            part = result[0:255]
            result = result[255:]
            hass.states.async_set("introspection.result_" + str(n), part)

        hass.states.async_set("introspection.len", str(n))
        hass.states.async_set("introspection.total_len", str(total_len))
        hass.states.async_set("introspection.truncated", str(1 if result != '' else 0))

    hass.services.async_register(
        DOMAIN,
        SERVICE_DO_INTROSPECTION,
        async_do_introspection,
        schema=SCHEMA_DO_INTROSPECTION,
    )

    return True

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    return True
