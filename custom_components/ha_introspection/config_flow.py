"""Config flow."""
from homeassistant import config_entries

from .const import DOMAIN

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id("ha_introspection")
        return self.async_create_entry(title="Home Assistant Introspection", data={})
